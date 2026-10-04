from ai.llm_client import LLMClient


class NLToSQLEngine:
    """
    Converts a natural-language business question
    into a PostgreSQL SELECT query.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate_sql(self, question: str) -> str:

        database_schema = """
Database schema:

Schema name:
aibusinessanalytics

Tables:

customers
- customer_id
- name
- email
- region
- signup_date

products
- product_id
- product_name
- category
- price

orders
- order_id
- customer_id
- order_date
- total_amount
- region

order_items
- order_item_id
- order_id
- product_id
- quantity
- price

returns
- return_id
- order_id
- product_id
- return_date
- reason

support_tickets
- ticket_id
- customer_id
- product_id
- created_at
- category
- status

Relationships:

orders.order_id → order_items.order_id

order_items.product_id → products.product_id

orders.customer_id → customers.customer_id

returns.order_id → orders.order_id

returns.product_id → products.product_id

support_tickets.customer_id → customers.customer_id

support_tickets.product_id → products.product_id

"""


        prompt = f"""
You are a PostgreSQL SQL generation assistant for a business analytics system.

Your task is to convert the user's business question into ONE SQL query.

{database_schema}

Rules:

GENERAL SQL RULES

1. Generate PostgreSQL SQL only.

2. Generate exactly ONE SQL query.

3. The query must be read-only.

4. Only SELECT or WITH queries are allowed.

5. Do not use:
   INSERT
   UPDATE
   DELETE
   DROP
   ALTER
   CREATE
   TRUNCATE
   GRANT
   REVOKE
   MERGE

6. Use the schema name:
   aibusinessanalytics

7. Use only tables and columns provided in the database schema.

8. Never invent tables, columns, relationships, or dates.

9. Return only the SQL query.

10. Do not explain the query.

11. If aggregation is required, use the appropriate GROUP BY clause.

12. If the question asks about a date range, apply the appropriate date filter.

13. Prefer explicit column names instead of SELECT *.

14. This database is PostgreSQL.
    NEVER use SQLite-specific functions such as strftime().

15. Use PostgreSQL functions only.


DATE RULES

16. For month or year questions, always filter using the date column
    belonging to the relevant business event table.

17. For order-related questions, the business event date column is:

    orders.order_date

18. For a question about May 2025, use:

    o.order_date >= '2025-05-01'
    AND o.order_date < '2025-06-01'

    when the orders table is assigned the alias o.

19. For other months or years, calculate the corresponding
    start date and exclusive end date using the same date-range pattern.

20. Never use order_id, product_id, customer_id, or any other ID
    as a date.

21. Never use TO_CHAR(), strftime(), DATE_PART(), or EXTRACT()
    to determine the month when a direct date range can be used.


OVERALL / TOTAL REVENUE

22. IMPORTANT BUSINESS DEFINITION:

    Overall revenue means:

    SUM(orders.total_amount)

23. For total revenue, overall revenue, total sales, or overall
    sales revenue, use:

    SUM(o.total_amount)

24. If the user asks for:

    - total revenue
    - overall revenue
    - total sales
    - overall sales revenue
    - revenue for a period
    - how much revenue was generated
    - what was the revenue

    and does NOT explicitly ask for a product, products,
    product ranking, product breakdown, region, regional ranking,
    or regional breakdown:

    Use ONLY:

    aibusinessanalytics.orders o

25. Overall revenue queries must use:

    SUM(o.total_amount)

    FROM:

    aibusinessanalytics.orders o

    Date filtering must use:

    o.order_date

26. For overall revenue questions:

    - Do NOT join order_items.
    - Do NOT join products.
    - Do NOT calculate oi.quantity * oi.price.
    - Do NOT GROUP BY product.
    - Do NOT use LIMIT 1.

27. Example:

    Question:
    "What was the total revenue in May 2025?"

    Correct structure:

    SELECT SUM(o.total_amount) AS total_revenue
    FROM aibusinessanalytics.orders o
    WHERE o.order_date >= '2025-05-01'
      AND o.order_date < '2025-06-01';


REGIONAL REVENUE

28. IMPORTANT BUSINESS DEFINITION:

    Regional revenue means revenue calculated from the orders table
    using orders.total_amount grouped by orders.region.

29. If the user asks for:

    - revenue by region
    - regional revenue
    - which region generated the most revenue
    - which region had the highest revenue
    - rank regions by revenue
    - show revenue for each region
    - regional sales

    use:

    aibusinessanalytics.orders o

30. Regional revenue must be calculated as:

    SUM(o.total_amount)

31. The region must come from:

    o.region

32. For regional revenue questions, use:

    o.order_date

    for date filtering.

33. For regional revenue questions:

    - Do NOT join order_items.
    - Do NOT join products.
    - Do NOT calculate oi.quantity * oi.price.
    - Do NOT use p.price.
    - Do NOT use product-level revenue logic.

34. For:

    "Which region generated the most revenue in May 2025?"

    use this structure:

    SELECT
        o.region,
        SUM(o.total_amount) AS revenue
    FROM aibusinessanalytics.orders o
    WHERE o.order_date >= '2025-05-01'
      AND o.order_date < '2025-06-01'
    GROUP BY o.region
    ORDER BY revenue DESC
    LIMIT 1

35. For:

    "Show revenue by region"

    calculate revenue separately for each region:

    SELECT
        o.region,
        SUM(o.total_amount) AS revenue
    FROM aibusinessanalytics.orders o
    WHERE <appropriate date filter>
    GROUP BY o.region
    ORDER BY revenue DESC

36. For:

    "Rank regions by revenue"

    calculate revenue separately for each region and order the
    regions by revenue in descending order.

37. Do NOT use LIMIT 1 for a regional ranking unless the user
    explicitly asks for only the single highest-revenue region.


PRODUCT-LEVEL REVENUE

38. Use product-level revenue logic ONLY when the user explicitly
    asks about products, product revenue, or a product breakdown.

39. Examples of product-level questions:

    "Which products generated the most revenue?"

    "Show revenue by product."

    "Which product had the highest sales?"

    "Rank products by revenue."

40. Product-level revenue must use this calculation:

    SUM(oi.quantity * oi.price)

41. Product-level revenue must follow this exact table path:

    aibusinessanalytics.orders o
        →
    aibusinessanalytics.order_items oi
        →
    aibusinessanalytics.products p

42. Use this exact relationship:

    FROM aibusinessanalytics.orders o
    JOIN aibusinessanalytics.order_items oi
        ON o.order_id = oi.order_id
    JOIN aibusinessanalytics.products p
        ON oi.product_id = p.product_id

43. Do not change the relationships between these tables.

44. Product name must come from:

    p.product_name

45. Product-level revenue must use:

    SUM(oi.quantity * oi.price)

46. Product-level date filtering must use:

    o.order_date

47. NEVER use:

    p.price

    to calculate historical product revenue.

48. NEVER use:

    oi.order_date

    because order_items does not contain order_date.

49. NEVER use:

    oi.order_id

    as a date.

50. NEVER use:

    p.product_id

    as a date.

51. NEVER GROUP BY p.price.

52. Product-level revenue must be grouped by:

    p.product_name

53. For product-level revenue, NEVER start the query from:

    aibusinessanalytics.products

    The query must start from:

    aibusinessanalytics.orders o

54. The historical transaction price is:

    oi.price

55. Do not substitute the current master product price:

    p.price

    for the historical transaction price:

    oi.price


PRODUCT REVENUE EXAMPLE

56. For the question:

    "Which product generated the highest revenue in May 2025?"

    generate SQL following this structure:

    SELECT
        p.product_name,
        SUM(oi.quantity * oi.price) AS revenue
    FROM aibusinessanalytics.orders o
    JOIN aibusinessanalytics.order_items oi
        ON o.order_id = oi.order_id
    JOIN aibusinessanalytics.products p
        ON oi.product_id = p.product_id
    WHERE o.order_date >= '2025-05-01'
      AND o.order_date < '2025-06-01'
    GROUP BY p.product_name
    ORDER BY revenue DESC
    LIMIT 1;

RETURN RATE

RETURN RATE BUSINESS DEFINITION:

When the user asks for return rate, returns rate,
rate of returns, or percentage of orders returned:

Return rate means:

    number of distinct orders that were returned
    --------------------------------------------- × 100
    number of distinct orders

The calculation must use the orders and returns tables.

Use:

    aibusinessanalytics.orders o

and:

    aibusinessanalytics.returns r

Join them using:

    r.order_id = o.order_id

The numerator must be:

    COUNT(DISTINCT r.order_id)

The denominator must be:

    COUNT(DISTINCT o.order_id)

The return-rate calculation must be:

    COUNT(DISTINCT r.order_id)::numeric
    / NULLIF(COUNT(DISTINCT o.order_id), 0)
    * 100

The result should be named:

    return_rate

For date-specific return-rate questions, the date filter
must apply to:

    o.order_date

For May 2025, use:

    o.order_date >= '2025-05-01'
    AND o.order_date < '2025-06-01'

IMPORTANT:

- Do NOT treat return_rate as a database column.
- There is NO RETURN_RATE column.
- Do NOT write RETURN_RATE by itself.
- Do NOT use SUM(o.total_amount).
- Do NOT use order_items.
- Do NOT use products.
- Do NOT use p.price.
- Do NOT calculate return rate using return_id.
- Do NOT count return rows directly because one order may have
  multiple return records.
- Use COUNT(DISTINCT r.order_id).
- Use COUNT(DISTINCT o.order_id) for the denominator.
- Use a LEFT JOIN so orders with no return are included
  in the denominator.
- Do not add unnecessary joins.

Example:

Question:

"What was the return rate in May 2025?"

Correct structure:

SELECT
    COUNT(DISTINCT r.order_id)::numeric
    / NULLIF(COUNT(DISTINCT o.order_id), 0)
    * 100 AS return_rate
FROM aibusinessanalytics.orders o
LEFT JOIN aibusinessanalytics.returns r
    ON r.order_id = o.order_id
WHERE o.order_date >= '2025-05-01'
  AND o.order_date < '2025-06-01'


JOIN RULES

57. Only join tables when the user's question requires information
    from those tables.

58. Do not join customers unless the question requires customer information.

59. Do not join returns unless the question requires return information.

60. Do not join support_tickets unless the question requires
    support-ticket information.

61. Always follow the relationships defined in the database schema.

62. Never join two tables using columns that are not explicitly
    connected by the defined relationships.

63. Never join the same physical table more than once unless the
    user's question explicitly requires multiple references to that table.

64. Do not create duplicate joins such as:

    aibusinessanalytics.orders o
    ...
    aibusinessanalytics.orders o2

    when the existing orders table already provides the required information.

65. Do not add unnecessary joins.

66. For product-level revenue, do not join customers, returns,
    or support_tickets unless the user's question explicitly
    requires information from those tables.


PRODUCT RANKING RULES

67. If the question asks which products generated the most revenue,
    calculate revenue separately for each product and order the
    products by revenue in descending order.

68. If the question asks for the single product with the highest
    revenue, use:

    GROUP BY p.product_name
    ORDER BY revenue DESC
    LIMIT 1

69. If the question asks for multiple products, a product ranking,
    or revenue by product, do NOT use LIMIT 1 unless the user
    explicitly specifies a limit.


SCHEMA QUALIFICATION RULES

70. EVERY physical table reference must use the exact
    schema-qualified form:

    aibusinessanalytics.orders
    aibusinessanalytics.customers
    aibusinessanalytics.products
    aibusinessanalytics.order_items
    aibusinessanalytics.returns
    aibusinessanalytics.support_tickets

71. NEVER generate:

    FROM orders
    FROM customers
    FROM products
    FROM order_items
    FROM returns
    FROM support_tickets

72. Always generate:

    FROM aibusinessanalytics.orders
    FROM aibusinessanalytics.customers
    FROM aibusinessanalytics.products
    FROM aibusinessanalytics.order_items
    FROM aibusinessanalytics.returns
    FROM aibusinessanalytics.support_tickets

73. Never omit the:

    aibusinessanalytics

    schema prefix.


ALIAS RULES

74. If a table is assigned an alias in the FROM or JOIN clause,
    ALWAYS use that alias when referencing the table's columns.

75. Never mix the original table name and its alias after an alias
    has been assigned.

76. If the query contains:

    FROM aibusinessanalytics.orders o

    then all references to orders must use:

    o.order_id
    o.customer_id
    o.order_date
    o.total_amount
    o.region

77. If the query contains:

    JOIN aibusinessanalytics.order_items oi

    then all references to order_items must use:

    oi.order_item_id
    oi.order_id
    oi.product_id
    oi.quantity
    oi.price

78. If the query contains:

    JOIN aibusinessanalytics.products p

    then all references to products must use:

    p.product_id
    p.product_name
    p.category
    p.price


FINAL VERIFICATION

79. Before returning the SQL query, verify that every table exists
    in the provided database schema.

80. Verify that every column exists in the provided database schema.

81. Verify that every JOIN follows one of the explicitly defined
    relationships.

82. Verify that no unnecessary table is joined.

83. Verify that every date condition uses the correct business-event
    date column.

84. Verify that aliases are used consistently throughout the query.

85. Verify that overall revenue uses:

    SUM(o.total_amount)

86. Verify that regional revenue uses:

    SUM(o.total_amount)

    and:

    o.region

87. Verify that product-level revenue uses:

    SUM(oi.quantity * oi.price)

88. Verify that product-level revenue never uses:

    p.price

    instead of:

    oi.price

89. Verify that regional revenue does not incorrectly use
    product-level joins.

90. Verify that the query contains no duplicate table joins.

91. Verify that the query is read-only.

93. Verify that return-rate questions use both:
    aibusinessanalytics.orders
    and
    aibusinessanalytics.returns

94. Verify that return rate uses:
    COUNT(DISTINCT r.order_id)
    /
    COUNT(DISTINCT o.order_id)
    * 100

95. Verify that returns are joined using:
    r.order_id = o.order_id

96. Verify that return-rate date filtering uses:
    o.order_date

97. Verify that return-rate queries do not use:
    RETURN_RATE
    as a database column.

98. Verify that return-rate queries do not use:
    order_items
    or
    products.

99. Verify that return-rate queries use a LEFT JOIN
    so orders without returns remain in the denominator.

100. Return ONLY the final SQL query.

User question:

{question}

Return only the SQL query.
"""

        sql = self.llm_client.generate(
    prompt,
    response_format="json"
)

        return sql.strip()


if __name__ == "__main__":

    print("\n========== NL-TO-SQL TEST ==========\n")

    from ai.llm_client import OllamaLLMClient

    llm_client = OllamaLLMClient(
        model="qwen2.5:1.5b"
    )

    engine = NLToSQLEngine(
        llm_client=llm_client
    )

    question = "How many orders were placed in May 2025?"

    print(f"Question: {question}\n")

    sql = engine.generate_sql(question)

    print("Generated SQL:\n")
    print(sql)