# analytics/cross_business.py

import pandas as pd

from sqlalchemy import text

from analytics.db import engine
from analytics import queries


def run_query(query):
    with engine.connect() as connection:
        result = connection.execute(text(query))
        return result.fetchall()


def analyze_return_rates():

    result = run_query(queries.RETURN_RATE_BY_PRODUCT)

    df = pd.DataFrame(
        result,
        columns=[
            "product",
            "total_orders",
            "total_returns",
            "return_rate"
        ]
    )

    print("\n========== RETURN RATE ANALYSIS ==========\n")

    for _, row in df.iterrows():

        print(
            f"{row['product']} | "
            f"Orders: {row['total_orders']} | "
            f"Returns: {row['total_returns']} | "
            f"Return Rate: {row['return_rate']}%"
        )


def analyze_support_and_returns():

    result = run_query(
        queries.SUPPORT_AND_RETURNS_BY_PRODUCT
    )

    df = pd.DataFrame(
        result,
        columns=[
            "product",
            "total_returns",
            "support_tickets",
            "complaints"
        ]
    )

    print("\n========== SUPPORT + RETURN ANALYSIS ==========\n")

    for _, row in df.iterrows():

        print(
            f"{row['product']} | "
            f"Returns: {row['total_returns']} | "
            f"Support Tickets: {row['support_tickets']} | "
            f"Complaints: {row['complaints']}"
        )


def identify_products_for_investigation():

    result = run_query(
        queries.SUPPORT_AND_RETURNS_BY_PRODUCT
    )

    df = pd.DataFrame(
        result,
        columns=[
            "product",
            "total_returns",
            "support_tickets",
            "complaints"
        ]
    )

    print("\n========== PRODUCTS TO INVESTIGATE ==========\n")

    # Use the 75th percentile as a simple data-driven threshold.
    return_threshold = df["total_returns"].quantile(0.75)
    complaint_threshold = df["complaints"].quantile(0.75)

    candidates = df[
        (df["total_returns"] >= return_threshold)
        &
        (df["complaints"] >= complaint_threshold)
    ]

    if candidates.empty:

        print("No products currently meet both thresholds.")

    else:

        for _, row in candidates.iterrows():

            print(
                f"⚠️ {row['product']} | "
                f"Returns: {row['total_returns']} | "
                f"Complaints: {row['complaints']}"
            )


def main():

    analyze_return_rates()

    analyze_support_and_returns()

    identify_products_for_investigation()


if __name__ == "__main__":
    main()