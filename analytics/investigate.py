# analytics/investigate.py

import pandas as pd

from sqlalchemy import text

from analytics.db import engine
from analytics import queries


def run_query(query):
    with engine.connect() as connection:
        result = connection.execute(text(query))
        return result.fetchall()


def get_monthly_revenue():

    result = run_query(queries.MONTHLY_REVENUE)

    df = pd.DataFrame(
        result,
        columns=["month", "revenue"]
    )

    df["month"] = pd.to_datetime(df["month"])

    # Convert PostgreSQL Decimal values to Python floats
    df["revenue"] = pd.to_numeric(
        df["revenue"],
        errors="coerce"
    )

    return df


def detect_anomalous_month(df):

    df["month"] = pd.to_datetime(df["month"])

    # Calculate normal revenue using median
    median_revenue = df["revenue"].median()

    # Find the month furthest from the median
    df["distance_from_median"] = (
        abs(df["revenue"] - median_revenue)
    )

    anomaly = df.loc[
        df["distance_from_median"].idxmax()
    ]

    return anomaly


def investigate_products(anomaly_month):

    result = run_query(
        queries.PRODUCT_MONTHLY_REVENUE
    )

    df = pd.DataFrame(
        result,
        columns=[
            "month",
            "product",
            "revenue"
        ]
    )

    df["month"] = pd.to_datetime(df["month"])

    df["revenue"] = pd.to_numeric(
        df["revenue"],
        errors="coerce"
    )

    current = df[
        df["month"] == anomaly_month
    ].copy()

    previous_month = (
        anomaly_month - pd.DateOffset(months=1)
    )

    previous = df[
        df["month"] == previous_month
    ].copy()

    if previous.empty:

        return current

    comparison = current.merge(
        previous,
        on="product",
        how="left",
        suffixes=("_current", "_previous")
    )

    comparison["revenue_current"] = pd.to_numeric(
        comparison["revenue_current"],
        errors="coerce"
)

    comparison["revenue_previous"] = pd.to_numeric(
        comparison["revenue_previous"],
        errors="coerce"
)

    comparison["change"] = (
        comparison["revenue_current"]
        - comparison["revenue_previous"]
    )

    comparison["change_percentage"] = (
        comparison["change"]
        / comparison["revenue_previous"]
        .replace(0, pd.NA)
        * 100
    )

    return comparison.sort_values(
        "change_percentage"
    )


def investigate_regions(anomaly_month):

    result = run_query(
        queries.REGION_MONTHLY_REVENUE
    )

    df = pd.DataFrame(
        result,
        columns=[
            "month",
            "region",
            "revenue"
        ]
    )

    # Convert PostgreSQL values to compatible Python/Pandas types
    df["month"] = pd.to_datetime(df["month"])

    df["revenue"] = pd.to_numeric(
        df["revenue"],
        errors="coerce"
    )

    # Get revenue for the anomalous month
    current = df[
        df["month"] == anomaly_month
    ].copy()

    # Calculate previous month
    previous_month = (
        anomaly_month - pd.DateOffset(months=1)
    )

    # Get revenue for the previous month
    previous = df[
        df["month"] == previous_month
    ].copy()

    # If there is no previous month, return current data
    if previous.empty:
        return current

    # Compare current month with previous month
    comparison = current.merge(
        previous,
        on="region",
        how="left",
        suffixes=("_current", "_previous")
    )

    # Make sure merged revenue columns are numeric
    comparison["revenue_current"] = pd.to_numeric(
        comparison["revenue_current"],
        errors="coerce"
    )

    comparison["revenue_previous"] = pd.to_numeric(
        comparison["revenue_previous"],
        errors="coerce"
    )

    # Calculate absolute revenue change
    comparison["change"] = (
        comparison["revenue_current"]
        - comparison["revenue_previous"]
    )

    # Calculate percentage change
    comparison["change_percentage"] = (
        comparison["change"]
        / comparison["revenue_previous"].replace(0, pd.NA)
        * 100
    )

    # Return regions sorted by percentage change
    return comparison.sort_values(
        "change_percentage"
    )


def investigate_returns(anomaly_month):

    returns_result = run_query(
        queries.MONTHLY_RETURNS
    )

    orders_result = run_query(
        queries.MONTHLY_COMPLETED_ORDERS
    )

    returns_df = pd.DataFrame(
        returns_result,
        columns=[
            "month",
            "total_returns"
        ]
    )

    orders_df = pd.DataFrame(
        orders_result,
        columns=[
            "month",
            "completed_orders"
        ]
    )

    # Convert dates
    returns_df["month"] = pd.to_datetime(
        returns_df["month"]
    )

    orders_df["month"] = pd.to_datetime(
        orders_df["month"]
    )

    # Convert numeric values
    returns_df["total_returns"] = pd.to_numeric(
        returns_df["total_returns"],
        errors="coerce"
    )

    orders_df["completed_orders"] = pd.to_numeric(
        orders_df["completed_orders"],
        errors="coerce"
    )

    # Calculate return rate
    df = returns_df.merge(
        orders_df,
        on="month",
        how="left"
    )

    df["return_rate"] = (
        df["total_returns"]
        / df["completed_orders"]
        * 100
    )

    # Current anomaly month
    current = df[
        df["month"] == anomaly_month
    ]

    # Previous month
    previous_month = (
        anomaly_month
        - pd.DateOffset(months=1)
    )

    previous = df[
        df["month"] == previous_month
    ]

    if current.empty or previous.empty:
        return None

    current_row = current.iloc[0]
    previous_row = previous.iloc[0]

    # Display results
    print("\n--- Return Rate Analysis ---")

    print(
        f"\n{anomaly_month.strftime('%Y-%m')}"
    )

    print(
        f"Completed Orders: "
        f"{int(current_row['completed_orders'])}"
    )

    print(
        f"Returns: "
        f"{int(current_row['total_returns'])}"
    )

    print(
        f"Return Rate: "
        f"{current_row['return_rate']:.2f}%"
    )

    print(
        f"\n{previous_month.strftime('%Y-%m')}"
    )

    print(
        f"Completed Orders: "
        f"{int(previous_row['completed_orders'])}"
    )

    print(
        f"Returns: "
        f"{int(previous_row['total_returns'])}"
    )

    print(
        f"Return Rate: "
        f"{previous_row['return_rate']:.2f}%"
    )

    change = (
        current_row["return_rate"]
        - previous_row["return_rate"]
    )

    print(
        f"\nChange in Return Rate: "
        f"{change:+.2f} percentage points"
    )

    if change > 0:
        print("⚠️ Return rate increased.")
    elif change < 0:
        print("✅ Return rate decreased.")
    else:
        print("Return rate remained unchanged.")

    # Return structured data
    return {
        "current_returns": int(
            current_row["total_returns"]
        ),
        "previous_returns": int(
            previous_row["total_returns"]
        ),
        "current_completed_orders": int(
            current_row["completed_orders"]
        ),
        "previous_completed_orders": int(
            previous_row["completed_orders"]
        ),
        "current_return_rate": float(
            current_row["return_rate"]
        ),
        "previous_return_rate": float(
            previous_row["return_rate"]
        )
    }

def investigate_support_tickets(anomaly_month):

    result = run_query(
        queries.MONTHLY_SUPPORT_TICKETS
    )

    df = pd.DataFrame(
        result,
        columns=[
            "month",
            "total_tickets"
        ]
    )

    # Convert dates
    df["month"] = pd.to_datetime(
        df["month"]
    )

    # Convert numeric values
    df["total_tickets"] = pd.to_numeric(
        df["total_tickets"],
        errors="coerce"
    )

    # Current anomaly month
    current = df[
        df["month"] == anomaly_month
    ]

    # Previous month
    previous_month = (
        anomaly_month
        - pd.DateOffset(months=1)
    )

    previous = df[
        df["month"] == previous_month
    ]

    if current.empty or previous.empty:
        return None

    current_tickets = int(
        current.iloc[0]["total_tickets"]
    )

    previous_tickets = int(
        previous.iloc[0]["total_tickets"]
    )

    ticket_change = (
        current_tickets
        - previous_tickets
    )

    ticket_percentage_change = (
        ticket_change
        / previous_tickets
        * 100
    )

    # Display results
    print("\n--- Support Ticket Analysis ---")

    print(
        f"\n{anomaly_month.strftime('%Y-%m')}"
    )

    print(
        f"Support Tickets: "
        f"{current_tickets}"
    )

    print(
        f"\n{previous_month.strftime('%Y-%m')}"
    )

    print(
        f"Support Tickets: "
        f"{previous_tickets}"
    )

    print(
        f"Ticket change: "
        f"{ticket_change}"
    )

    print(
        f"Ticket percentage change: "
        f"{ticket_percentage_change:.2f}%"
    )

    # Return structured data
    return {
        "current_tickets": current_tickets,
        "previous_tickets": previous_tickets,
        "change": ticket_change,
        "percentage_change": float(
            ticket_percentage_change
        )
    }

def investigate_ticket_categories(anomaly_month):

    result = run_query(
        queries.MONTHLY_TICKETS_BY_CATEGORY
    )

    df = pd.DataFrame(
        result,
        columns=[
            "month",
            "category",
            "ticket_count"
        ]
    )

    # Convert database values
    df["month"] = pd.to_datetime(
        df["month"]
    )

    df["ticket_count"] = pd.to_numeric(
        df["ticket_count"],
        errors="coerce"
    )

    # Current month
    current = df[
        df["month"] == anomaly_month
    ].copy()

    # Previous month
    previous_month = (
        anomaly_month
        - pd.DateOffset(months=1)
    )

    previous = df[
        df["month"] == previous_month
    ].copy()

    print("\n--- Support Ticket Categories ---")

    if current.empty:

        print(
            "No category data found for "
            f"{anomaly_month.strftime('%Y-%m')}."
        )

        return

    if previous.empty:

        print(
            "Previous month category data unavailable."
        )

        return

    # Compare categories
    comparison = current.merge(
        previous,
        on="category",
        how="outer",
        suffixes=("_current", "_previous")
    )

    # Missing categories should count as zero
    comparison["ticket_count_current"] = (
        comparison["ticket_count_current"]
        .fillna(0)
    )

    comparison["ticket_count_previous"] = (
        comparison["ticket_count_previous"]
        .fillna(0)
    )

    # Calculate change
    comparison["change"] = (
        comparison["ticket_count_current"]
        - comparison["ticket_count_previous"]
    )

    # Calculate percentage change
    comparison["change_percentage"] = (
        comparison["change"]
        / comparison["ticket_count_previous"]
        .replace(0, pd.NA)
        * 100
    )

    # Sort by largest increase
    comparison = comparison.sort_values(
        "change_percentage",
        ascending=False,
        na_position="last"
    )

    print(
        comparison[
            [
                "category",
                "ticket_count_current",
                "ticket_count_previous",
                "change",
                "change_percentage"
            ]
        ].to_string(index=False)
    )


def investigate_support_by_product(anomaly_month):

    result = run_query(
        queries.MONTHLY_SUPPORT_BY_PRODUCT
    )

    df = pd.DataFrame(
        result,
        columns=[
            "month",
            "product",
            "ticket_count",
            "complaints",
            "refunds",
            "technical_issues"
        ]
    )

    # Convert database values
    df["month"] = pd.to_datetime(
        df["month"]
    )

    numeric_columns = [
        "ticket_count",
        "complaints",
        "refunds",
        "technical_issues"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Current month
    current = df[
        df["month"] == anomaly_month
    ].copy()

    # Previous month
    previous_month = (
        anomaly_month
        - pd.DateOffset(months=1)
    )

    previous = df[
        df["month"] == previous_month
    ].copy()

    print("\n--- Support Issues by Product ---")

    if current.empty:

        print(
            "No product support data found for "
            f"{anomaly_month.strftime('%Y-%m')}."
        )

        return

    if previous.empty:

        print(
            "Previous month product support "
            "data unavailable."
        )

        return

    comparison = current.merge(
        previous,
        on="product",
        how="outer",
        suffixes=("_current", "_previous")
    )

    # Missing values mean there were no tickets
    # for that product in that month.
    comparison = comparison.fillna(0)

    # Calculate total ticket change
    comparison["ticket_change"] = (
        comparison["ticket_count_current"]
        - comparison["ticket_count_previous"]
    )

    # Calculate complaint change
    comparison["complaint_change"] = (
        comparison["complaints_current"]
        - comparison["complaints_previous"]
    )

    # Calculate refund change
    comparison["refund_change"] = (
        comparison["refunds_current"]
        - comparison["refunds_previous"]
    )

    # Calculate technical issue change
    comparison["technical_change"] = (
        comparison["technical_issues_current"]
        - comparison["technical_issues_previous"]
    )

    comparison = comparison.sort_values(
        "ticket_change",
        ascending=False
    )

    print(
        comparison[
            [
                "product",
                "ticket_count_current",
                "ticket_count_previous",
                "ticket_change",
                "complaint_change",
                "refund_change",
                "technical_change"
            ]
        ].to_string(index=False)
    )

def investigate_returns_by_product(anomaly_month):

    result = run_query(
        queries.MONTHLY_RETURNS_BY_PRODUCT
    )

    df = pd.DataFrame(
        result,
        columns=[
            "month",
            "product",
            "return_count"
        ]
    )

    df["month"] = pd.to_datetime(
        df["month"]
    )

    df["return_count"] = pd.to_numeric(
        df["return_count"],
        errors="coerce"
    )

    # Current month
    current = df[
        df["month"] == anomaly_month
    ].copy()

    # Previous month
    previous_month = (
        anomaly_month
        - pd.DateOffset(months=1)
    )

    previous = df[
        df["month"] == previous_month
    ].copy()

    print("\n--- Returns by Product ---")

    if current.empty:

        print(
            "No product return data found for "
            f"{anomaly_month.strftime('%Y-%m')}."
        )

        return

    if previous.empty:

        print(
            "Previous month product return "
            "data unavailable."
        )

        return

    comparison = current.merge(
        previous,
        on="product",
        how="outer",
        suffixes=("_current", "_previous")
    )

    comparison["return_count_current"] = (
        comparison["return_count_current"]
        .fillna(0)
    )

    comparison["return_count_previous"] = (
        comparison["return_count_previous"]
        .fillna(0)
    )

    comparison["return_change"] = (
        comparison["return_count_current"]
        - comparison["return_count_previous"]
    )

    comparison = comparison.sort_values(
        "return_change",
        ascending=False
    )

    print(
        comparison[
            [
                "product",
                "return_count_current",
                "return_count_previous",
                "return_change"
            ]
        ].to_string(index=False)
    )


def build_product_evidence(anomaly_month):

    # -----------------------------
    # Product revenue
    # -----------------------------

    revenue_result = run_query(
        queries.PRODUCT_MONTHLY_REVENUE
    )

    revenue_df = pd.DataFrame(
        revenue_result,
        columns=[
            "month",
            "product",
            "revenue"
        ]
    )

    revenue_df["month"] = pd.to_datetime(
        revenue_df["month"]
    )

    revenue_df["revenue"] = pd.to_numeric(
        revenue_df["revenue"],
        errors="coerce"
    )

    previous_month = (
        anomaly_month
        - pd.DateOffset(months=1)
    )

    current_revenue = revenue_df[
        revenue_df["month"] == anomaly_month
    ][["product", "revenue"]].copy()

    previous_revenue = revenue_df[
        revenue_df["month"] == previous_month
    ][["product", "revenue"]].copy()

    revenue_comparison = current_revenue.merge(
        previous_revenue,
        on="product",
        how="outer",
        suffixes=("_current", "_previous")
    )

    revenue_comparison["revenue_current"] = (
        revenue_comparison["revenue_current"]
        .fillna(0)
    )

    revenue_comparison["revenue_previous"] = (
        revenue_comparison["revenue_previous"]
        .fillna(0)
    )

    revenue_comparison["revenue_change_percentage"] = (
        (
            revenue_comparison["revenue_current"]
            - revenue_comparison["revenue_previous"]
        )
        / revenue_comparison["revenue_previous"]
        .replace(0, pd.NA)
        * 100
    )

    # -----------------------------
    # Product returns
    # -----------------------------

    return_result = run_query(
        queries.MONTHLY_RETURNS_BY_PRODUCT
    )

    return_df = pd.DataFrame(
        return_result,
        columns=[
            "month",
            "product",
            "return_count"
        ]
    )

    return_df["month"] = pd.to_datetime(
        return_df["month"]
    )

    return_df["return_count"] = pd.to_numeric(
        return_df["return_count"],
        errors="coerce"
    )

    current_returns = return_df[
        return_df["month"] == anomaly_month
    ][["product", "return_count"]].copy()

    previous_returns = return_df[
        return_df["month"] == previous_month
    ][["product", "return_count"]].copy()

    returns_comparison = current_returns.merge(
        previous_returns,
        on="product",
        how="outer",
        suffixes=("_current", "_previous")
    )

    returns_comparison["return_count_current"] = (
        returns_comparison["return_count_current"]
        .fillna(0)
    )

    returns_comparison["return_count_previous"] = (
        returns_comparison["return_count_previous"]
        .fillna(0)
    )

    returns_comparison["return_change"] = (
        returns_comparison["return_count_current"]
        - returns_comparison["return_count_previous"]
    )

    # -----------------------------
    # Product support tickets
    # -----------------------------

    support_result = run_query(
        queries.MONTHLY_SUPPORT_BY_PRODUCT
    )

    support_df = pd.DataFrame(
        support_result,
        columns=[
            "month",
            "product",
            "ticket_count",
            "complaints",
            "refunds",
            "technical_issues"
        ]
    )

    support_df["month"] = pd.to_datetime(
        support_df["month"]
    )

    support_columns = [
        "ticket_count",
        "complaints",
        "refunds",
        "technical_issues"
    ]

    for column in support_columns:

        support_df[column] = pd.to_numeric(
            support_df[column],
            errors="coerce"
        )

    current_support = support_df[
        support_df["month"] == anomaly_month
    ][
        [
            "product",
            "ticket_count",
            "complaints",
            "refunds",
            "technical_issues"
        ]
    ].copy()

    previous_support = support_df[
        support_df["month"] == previous_month
    ][
        [
            "product",
            "ticket_count",
            "complaints",
            "refunds",
            "technical_issues"
        ]
    ].copy()

    support_comparison = current_support.merge(
        previous_support,
        on="product",
        how="outer",
        suffixes=("_current", "_previous")
    )

    support_comparison = support_comparison.fillna(0)

    support_comparison["ticket_change"] = (
        support_comparison["ticket_count_current"]
        - support_comparison["ticket_count_previous"]
    )

    support_comparison["complaint_change"] = (
        support_comparison["complaints_current"]
        - support_comparison["complaints_previous"]
    )

    support_comparison["refund_change"] = (
        support_comparison["refunds_current"]
        - support_comparison["refunds_previous"]
    )

    # -----------------------------
    # Combine all evidence
    # -----------------------------

    evidence = revenue_comparison.merge(
        returns_comparison,
        on="product",
        how="outer"
    )

    evidence = evidence.merge(
        support_comparison[
            [
                "product",
                "ticket_count_current",
                "ticket_count_previous",
                "ticket_change",
                "complaint_change",
                "refund_change"
            ]
        ],
        on="product",
        how="outer"
    )

    evidence = evidence.fillna(0)

    # -----------------------------
    # Display combined evidence
    # -----------------------------

    print(
        "\n--- Combined Product Evidence ---"
    )

    print(
        evidence[
            [
                "product",
                "revenue_change_percentage",
                "return_change",
                "ticket_change",
                "complaint_change",
                "refund_change"
            ]
        ]
        .sort_values(
            "revenue_change_percentage",
            ascending=False
        )
        .to_string(index=False)
    )

    return evidence

def main():

    print("\n========== ANOMALY INVESTIGATION ==========\n")

    monthly = get_monthly_revenue()

    anomaly = detect_anomalous_month(monthly)

    anomaly_month = anomaly["month"]
    anomaly_revenue = anomaly["revenue"]

    print(
        f"Investigating month: "
        f"{anomaly_month.strftime('%Y-%m')}"
    )

    print(
        f"Revenue: {anomaly['revenue']}"
    )

    print("\n--- Product Changes ---")

    products = investigate_products(
        anomaly_month
    )

    print(
        products[
            [
                "product",
                "revenue_current",
                "revenue_previous",
                "change_percentage"
            ]
        ].to_string(index=False)
    )

    print("\n--- Regional Changes ---")

    regions = investigate_regions(
        anomaly_month
    )

    print(
        regions[
            [
                "region",
                "revenue_current",
                "revenue_previous",
                "change_percentage"
            ]
        ].to_string(index=False)
    )
    
    return_data = investigate_returns(anomaly_month)
    support_data = investigate_support_tickets(anomaly_month)
    regional_evidence = investigate_regions(anomaly_month)
    product_evidence = build_product_evidence(anomaly_month)
    
    # ==========================================
# Build investigation report
# ==========================================

    from analytics.investigation_report import (
    build_investigation_report,
    save_report
    )

    report = build_investigation_report(
    anomaly_month=anomaly_month,
    anomaly_revenue=anomaly_revenue,
    product_evidence=product_evidence,
    regional_evidence=regional_evidence,
    return_rate_current=return_data[
        "current_return_rate"
    ],
    return_rate_previous=return_data[
        "previous_return_rate"
    ],
    support_ticket_current=support_data[
        "current_tickets"
    ],
    support_ticket_previous=support_data[
        "previous_tickets"
    ]
)

    save_report(report)
    


if __name__ == "__main__":
    main()