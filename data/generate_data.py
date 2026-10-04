import random
from datetime import date, timedelta

from faker import Faker
from sqlalchemy import create_engine, text

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

DATABASE_URL = "postgresql+psycopg2://postgres:Lav$2001@localhost:5432/postgres"

SCHEMA = "aibusinessanalytics"

NUMBER_OF_ORDERS = 30000
NUMBER_OF_RETURNS = 3000
NUMBER_OF_TICKETS = 5000

fake = Faker()
random.seed(42)

engine = create_engine(DATABASE_URL)


# --------------------------------------------------
# CONNECT TO DATABASE
# --------------------------------------------------

with engine.connect() as connection:

    print("Connected to PostgreSQL.")

    # --------------------------------------------------
    # LOAD EXISTING CUSTOMERS
    # --------------------------------------------------

    customers = connection.execute(
        text(f"""
            SELECT customer_id, region, customer_segment
            FROM {SCHEMA}.customers
        """)
    ).fetchall()

    # --------------------------------------------------
    # LOAD EXISTING PRODUCTS
    # --------------------------------------------------

    products = connection.execute(
        text(f"""
            SELECT product_id, product_name, category, price, cost
            FROM {SCHEMA}.products
        """)
    ).fetchall()

    if not customers:
        raise Exception("No customers found. Add customers first.")

    if not products:
        raise Exception("No products found. Add products first.")

    print(f"Found {len(customers)} existing customers.")
    print(f"Found {len(products)} existing products.")

    # Convert database rows into dictionaries
    customer_data = [
        {
            "customer_id": row.customer_id,
            "region": row.region,
            "customer_segment": row.customer_segment,
        }
        for row in customers
    ]

    product_data = [
        {
            "product_id": row.product_id,
            "product_name": row.product_name,
            "category": row.category,
            "price": float(row.price),
            "cost": float(row.cost),
        }
        for row in products
    ]

    # --------------------------------------------------
    # CLEAR OLD GENERATED TRANSACTION DATA
    # --------------------------------------------------
    # This does NOT delete customers or products.

    print("\nClearing old transaction data...")

    connection.execute(
        text(f"""
            TRUNCATE TABLE
                {SCHEMA}.returns,
                {SCHEMA}.support_tickets,
                {SCHEMA}.order_items,
                {SCHEMA}.orders
            RESTART IDENTITY;
        """)
    )

    connection.commit()

    print("Transaction tables cleared.")

    # --------------------------------------------------
    # GENERATE ORDERS + ORDER ITEMS
    # --------------------------------------------------

    print("\nGenerating orders...")

    start_date = date(2024, 1, 1)
    end_date = date(2026, 9, 30)

    orders = []
    order_items = []

    order_id = 1
    order_item_id = 1

    for _ in range(NUMBER_OF_ORDERS):

        customer = random.choice(customer_data)

        order_date = fake.date_between(
            start_date=start_date,
            end_date=end_date
        )

        # Most orders are completed
        status = random.choices(
            ["Completed", "Cancelled", "Pending"],
            weights=[85, 10, 5],
            k=1
        )[0]

        # Select 1–4 products
        number_of_items = random.randint(1, 4)

        selected_products = random.choices(
            product_data,
            k=number_of_items
        )

        total_amount = 0

        for product in selected_products:

            quantity = random.randint(1, 3)

            price = product["price"]

            item_total = quantity * price

            total_amount += item_total

            order_items.append(
                {
                    "order_item_id": order_item_id,
                    "order_id": order_id,
                    "product_id": product["product_id"],
                    "quantity": quantity,
                    "price": price,
                }
            )

            order_item_id += 1

        orders.append(
            {
                "order_id": order_id,
                "customer_id": customer["customer_id"],
                "order_date": order_date,
                "total_amount": round(total_amount, 2),
                "region": customer["region"],
                "status": status,
            }
        )

        order_id += 1

        if order_id % 5000 == 0:
            print(f"Generated {order_id - 1} orders...")

    # --------------------------------------------------
    # INSERT ORDERS
    # --------------------------------------------------

    print("\nInserting orders...")

    connection.execute(
        text(f"""
            INSERT INTO {SCHEMA}.orders
            (
                order_id,
                customer_id,
                order_date,
                total_amount,
                region,
                status
            )
            VALUES
            (
                :order_id,
                :customer_id,
                :order_date,
                :total_amount,
                :region,
                :status
            )
        """),
        orders
    )

    connection.commit()

    print(f"Inserted {len(orders)} orders.")

    # --------------------------------------------------
    # INSERT ORDER ITEMS
    # --------------------------------------------------

    print("Inserting order items...")

    connection.execute(
        text(f"""
            INSERT INTO {SCHEMA}.order_items
            (
                order_item_id,
                order_id,
                product_id,
                quantity,
                price
            )
            VALUES
            (
                :order_item_id,
                :order_id,
                :product_id,
                :quantity,
                :price
            )
        """),
        order_items
    )

    connection.commit()

    print(f"Inserted {len(order_items)} order items.")

    # --------------------------------------------------
    # GENERATE RETURNS
    # --------------------------------------------------

    print("\nGenerating returns...")

    completed_orders = [
        order for order in orders
        if order["status"] == "Completed"
    ]

    return_reasons = [
        "Defective product",
        "Wrong product",
        "Changed mind",
        "Product not as expected",
        "Damaged during delivery",
        "Poor quality"
    ]

    returns = []

    for return_id in range(1, NUMBER_OF_RETURNS + 1):

        order = random.choice(completed_orders)

        # Find products belonging to this order
        order_products = [
            item for item in order_items
            if item["order_id"] == order["order_id"]
        ]

        item = random.choice(order_products)

        product_id = item["product_id"]

        # Product 7 has a higher probability of being returned.
        if product_id == 7:
            reason = random.choice(
                [
                    "Defective product",
                    "Poor quality",
                    "Product not as expected",
                    "Damaged during delivery"
                ]
            )
        else:
            reason = random.choice(return_reasons)

        refund_amount = item["price"] * item["quantity"]

        returns.append(
            {
                "return_id": return_id,
                "order_id": order["order_id"],
                "product_id": product_id,
                "customer_id": order["customer_id"],
                "return_date": order["order_date"] + timedelta(
                    days=random.randint(1, 20)
                ),
                "reason": reason,
                "refund_amount": round(refund_amount, 2),
            }
        )

    connection.execute(
        text(f"""
            INSERT INTO {SCHEMA}.returns
            (
                return_id,
                order_id,
                product_id,
                customer_id,
                return_date,
                reason,
                refund_amount
            )
            VALUES
            (
                :return_id,
                :order_id,
                :product_id,
                :customer_id,
                :return_date,
                :reason,
                :refund_amount
            )
        """),
        returns
    )

    connection.commit()

    print(f"Inserted {len(returns)} returns.")

    # --------------------------------------------------
    # GENERATE SUPPORT TICKETS
    # --------------------------------------------------

    print("\nGenerating support tickets...")

    ticket_categories = [
        "Complaint",
        "Delivery",
        "Payment",
        "Product Question",
        "Technical Issue",
        "Refund"
    ]

    priorities = [
        "Low",
        "Medium",
        "High",
        "Critical"
    ]

    ticket_statuses = [
        "Open",
        "In Progress",
        "Resolved",
        "Closed"
    ]

    descriptions = [
        "Customer reported an issue with the order.",
        "Customer is asking about delivery status.",
        "Customer reported a payment problem.",
        "Customer requested more information about the product.",
        "Customer reported a technical issue.",
        "Customer is asking about a refund."
    ]

    tickets = []

    for ticket_id in range(1, NUMBER_OF_TICKETS + 1):

        customer = random.choice(customer_data)
        product = random.choice(product_data)

        category = random.choice(ticket_categories)

        # Create some regional delivery patterns
        if customer["region"] == "East" and random.random() < 0.35:
            category = "Delivery"

        # Product 7 gets more complaints
        if product["product_id"] == 7 and random.random() < 0.45:
            category = "Complaint"

        tickets.append(
            {
                "ticket_id": ticket_id,
                "customer_id": customer["customer_id"],
                "product_id": product["product_id"],
                "created_at": fake.date_between(
                    start_date=start_date,
                    end_date=end_date
                ),
                "category": category,
                "description": random.choice(descriptions),
                "priority": random.choices(
                    priorities,
                    weights=[40, 35, 20, 5],
                    k=1
                )[0],
                "status": random.choice(ticket_statuses),
            }
        )

    connection.execute(
        text(f"""
            INSERT INTO {SCHEMA}.support_tickets
            (
                ticket_id,
                customer_id,
                product_id,
                created_at,
                category,
                description,
                priority,
                status
            )
            VALUES
            (
                :ticket_id,
                :customer_id,
                :product_id,
                :created_at,
                :category,
                :description,
                :priority,
                :status
            )
        """),
        tickets
    )

    connection.commit()

    print(f"Inserted {len(tickets)} support tickets.")

    # --------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------

    print("\n========================================")
    print("DATA GENERATION COMPLETE")
    print("========================================")

    print(f"Customers       : {len(customer_data)}")
    print(f"Products        : {len(product_data)}")
    print(f"Orders          : {len(orders)}")
    print(f"Order Items     : {len(order_items)}")
    print(f"Returns         : {len(returns)}")
    print(f"Support Tickets : {len(tickets)}")

    print("\nYour AIBusinessIntelligence database is ready.")