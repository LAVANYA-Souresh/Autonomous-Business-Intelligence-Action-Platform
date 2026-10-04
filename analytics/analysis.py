# analytics/analysis.py

from sqlalchemy import text

from analytics.db import engine
from analytics import queries


def run_query(query):
    with engine.connect() as connection:
        result = connection.execute(text(query))
        return result.fetchall()


def main():

    print("\n========== BUSINESS ANALYTICS ==========\n")

    # Total customers
    result = run_query(queries.TOTAL_CUSTOMERS)
    print("Total Customers:", result[0][0])

    # Total revenue
    result = run_query(queries.TOTAL_REVENUE)
    print("Total Revenue:", result[0][0])

    # Total orders
    result = run_query(queries.TOTAL_ORDERS)
    print("Total Orders:", result[0][0])

    # Average order value
    result = run_query(queries.AVERAGE_ORDER_VALUE)
    print("Average Order Value:", result[0][0])

    # Revenue by region
    print("\nRevenue by Region:")

    result = run_query(queries.REVENUE_BY_REGION)

    for row in result:
        print(f"{row[0]}: {row[1]}")

        # Monthly revenue and growth
    print("\nMonthly Revenue and Growth:")

    result = run_query(queries.MONTHLY_REVENUE_GROWTH)

    for row in result:
        month = row[0]
        revenue = row[1]
        previous_revenue = row[2]
        growth = row[3]

        print(
            f"{month} | "
            f"Revenue: {revenue} | "
            f"Previous: {previous_revenue} | "
            f"Growth: {growth}%"
        )


if __name__ == "__main__":
    main()