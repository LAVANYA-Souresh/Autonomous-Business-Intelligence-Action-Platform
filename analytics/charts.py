# analytics/charts.py

import pandas as pd
import matplotlib.pyplot as plt

from sqlalchemy import text

from analytics.db import engine
from analytics import queries


def run_query(query):
    with engine.connect() as connection:
        result = connection.execute(text(query))
        return result.fetchall()


def monthly_revenue_chart():
    result = run_query(queries.MONTHLY_REVENUE)

    df = pd.DataFrame(
        result,
        columns=["month", "revenue"]
    )

    df["month"] = pd.to_datetime(df["month"])

    plt.figure(figsize=(12, 6))

    plt.plot(
        df["month"],
        df["revenue"],
        marker="o"
    )

    plt.title("Monthly Revenue")
    plt.xlabel("Month")
    plt.ylabel("Revenue")

    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.show()


def revenue_by_product_chart():
    result = run_query(queries.REVENUE_BY_PRODUCT)

    df = pd.DataFrame(
        result,
        columns=["product", "revenue"]
    )

    plt.figure(figsize=(12, 6))

    plt.bar(
        df["product"],
        df["revenue"]
    )

    plt.title("Revenue by Product")
    plt.xlabel("Product")
    plt.ylabel("Revenue")

    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.show()


def revenue_by_category_chart():
    result = run_query(queries.REVENUE_BY_CATEGORY)

    df = pd.DataFrame(
        result,
        columns=["category", "revenue"]
    )

    plt.figure(figsize=(10, 6))

    plt.bar(
        df["category"],
        df["revenue"]
    )

    plt.title("Revenue by Category")
    plt.xlabel("Category")
    plt.ylabel("Revenue")

    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.show()


def gross_profit_by_product_chart():
    result = run_query(queries.GROSS_PROFIT_BY_PRODUCT)

    df = pd.DataFrame(
        result,
        columns=["product", "gross_profit"]
    )

    plt.figure(figsize=(12, 6))

    plt.bar(
        df["product"],
        df["gross_profit"]
    )

    plt.title("Gross Profit by Product")
    plt.xlabel("Product")
    plt.ylabel("Gross Profit")

    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.show()


if __name__ == "__main__":

    monthly_revenue_chart()

    revenue_by_product_chart()

    revenue_by_category_chart()

    gross_profit_by_product_chart()