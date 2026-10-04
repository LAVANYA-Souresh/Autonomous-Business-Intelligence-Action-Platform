# analytics/insights.py

import pandas as pd

from sqlalchemy import text

from analytics.db import engine
from analytics import queries


def run_query(query):
    with engine.connect() as connection:
        result = connection.execute(text(query))
        return result.fetchall()


def analyze_monthly_revenue():

    result = run_query(queries.MONTHLY_REVENUE_GROWTH)

    df = pd.DataFrame(
        result,
        columns=[
            "month",
            "revenue",
            "previous_month_revenue",
            "growth_percentage"
        ]
    )

    df["month"] = pd.to_datetime(df["month"])

    print("\n========== REVENUE INSIGHTS ==========\n")

    for _, row in df.iterrows():

        month = row["month"].strftime("%Y-%m")

        revenue = row["revenue"]
        previous_revenue = row["previous_month_revenue"]
        growth = row["growth_percentage"]

        if pd.isna(previous_revenue):
            continue

        if growth > 5:

            print(
                f"📈 {month}: Revenue increased by "
                f"{growth}% compared with the previous month."
            )

        elif growth < -5:

            print(
                f"📉 {month}: Revenue decreased by "
                f"{abs(growth)}% compared with the previous month."
            )

        else:

            print(
                f"➡️ {month}: Revenue remained relatively stable "
                f"({growth}% change)."
            )


def analyze_top_products():

    result = run_query(queries.REVENUE_BY_PRODUCT)

    df = pd.DataFrame(
        result,
        columns=["product", "revenue"]
    )

    top_product = df.iloc[0]

    print("\n========== PRODUCT INSIGHTS ==========\n")

    print(
        f"Top revenue-generating product: "
        f"{top_product['product']}"
    )

    print(
        f"Revenue: {top_product['revenue']}"
    )


def analyze_profitability():

    result = run_query(queries.GROSS_PROFIT_BY_PRODUCT)

    df = pd.DataFrame(
        result,
        columns=["product", "gross_profit"]
    )

    highest_profit = df.iloc[0]

    print("\n========== PROFITABILITY INSIGHTS ==========\n")

    print(
        f"Highest gross-profit product: "
        f"{highest_profit['product']}"
    )

    print(
        f"Gross profit: {highest_profit['gross_profit']}"
    )


def main():

    analyze_monthly_revenue()

    analyze_top_products()

    analyze_profitability()


if __name__ == "__main__":
    main()