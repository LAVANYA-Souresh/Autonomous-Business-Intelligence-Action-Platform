# analytics/queries.py

TOTAL_CUSTOMERS = """
SELECT COUNT(*) AS total_customers
FROM aibusinessanalytics.customers;
"""


TOTAL_REVENUE = """
SELECT
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM aibusinessanalytics.orders
WHERE status = 'Completed';
"""


TOTAL_ORDERS = """
SELECT
    COUNT(*) AS total_orders
FROM aibusinessanalytics.orders
WHERE status = 'Completed';
"""


AVERAGE_ORDER_VALUE = """
SELECT
    ROUND(
        SUM(total_amount) / NULLIF(COUNT(*), 0),
        2
    ) AS average_order_value
FROM aibusinessanalytics.orders
WHERE status = 'Completed';
"""


REVENUE_BY_REGION = """
SELECT
    region,
    ROUND(SUM(total_amount), 2) AS revenue
FROM aibusinessanalytics.orders
WHERE status = 'Completed'
GROUP BY region
ORDER BY revenue DESC;
"""


MONTHLY_REVENUE = """
SELECT
    DATE_TRUNC('month', order_date)::date AS month,
    ROUND(SUM(total_amount), 2) AS revenue
FROM aibusinessanalytics.orders
WHERE status = 'Completed'
GROUP BY month
ORDER BY month;
"""

MONTHLY_REVENUE_GROWTH = """
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', order_date)::date AS month,
        SUM(total_amount) AS revenue
    FROM aibusinessanalytics.orders
    WHERE status = 'Completed'
    GROUP BY month
)
SELECT
    month,
    ROUND(revenue, 2) AS revenue,
    ROUND(LAG(revenue) OVER (ORDER BY month), 2) AS previous_month_revenue,
    ROUND(
        (
            (revenue - LAG(revenue) OVER (ORDER BY month))
            / NULLIF(LAG(revenue) OVER (ORDER BY month), 0)
        ) * 100,
        2
    ) AS growth_percentage
FROM monthly_revenue
ORDER BY month;
"""

REVENUE_BY_PRODUCT = """
SELECT
    p.product_name,
    ROUND(SUM(oi.quantity * oi.price), 2) AS revenue
FROM aibusinessanalytics.order_items oi
JOIN aibusinessanalytics.products p
    ON oi.product_id = p.product_id
JOIN aibusinessanalytics.orders o
    ON oi.order_id = o.order_id
WHERE o.status = 'Completed'
GROUP BY p.product_name
ORDER BY revenue DESC;
"""


REVENUE_BY_CATEGORY = """
SELECT
    p.category,
    ROUND(SUM(oi.quantity * oi.price), 2) AS revenue
FROM aibusinessanalytics.order_items oi
JOIN aibusinessanalytics.products p
    ON oi.product_id = p.product_id
JOIN aibusinessanalytics.orders o
    ON oi.order_id = o.order_id
WHERE o.status = 'Completed'
GROUP BY p.category
ORDER BY revenue DESC;
"""


GROSS_PROFIT_BY_PRODUCT = """
SELECT
    p.product_name,
    ROUND(
        SUM(oi.quantity * (oi.price - p.cost)),
        2
    ) AS gross_profit
FROM aibusinessanalytics.order_items oi
JOIN aibusinessanalytics.products p
    ON oi.product_id = p.product_id
JOIN aibusinessanalytics.orders o
    ON oi.order_id = o.order_id
WHERE o.status = 'Completed'
GROUP BY p.product_name
ORDER BY gross_profit DESC;
"""


TOTAL_RETURNS = """
SELECT
    COUNT(*) AS total_returns
FROM aibusinessanalytics.returns;
"""


RETURN_REASONS = """
SELECT
    reason,
    COUNT(*) AS return_count
FROM aibusinessanalytics.returns
GROUP BY reason
ORDER BY return_count DESC;
"""


TICKETS_BY_CATEGORY = """
SELECT
    category,
    COUNT(*) AS ticket_count
FROM aibusinessanalytics.support_tickets
GROUP BY category
ORDER BY ticket_count DESC;
"""

RETURN_RATE_BY_PRODUCT = """
WITH product_orders AS (
    SELECT
        oi.product_id,
        COUNT(DISTINCT oi.order_id) AS total_orders
    FROM aibusinessanalytics.order_items oi
    JOIN aibusinessanalytics.orders o
        ON oi.order_id = o.order_id
    WHERE o.status = 'Completed'
    GROUP BY oi.product_id
),
product_returns AS (
    SELECT
        product_id,
        COUNT(*) AS total_returns
    FROM aibusinessanalytics.returns
    GROUP BY product_id
)
SELECT
    p.product_name,
    COALESCE(po.total_orders, 0) AS total_orders,
    COALESCE(pr.total_returns, 0) AS total_returns,
    ROUND(
        COALESCE(pr.total_returns, 0)::numeric
        / NULLIF(COALESCE(po.total_orders, 0), 0) * 100,
        2
    ) AS return_rate
FROM aibusinessanalytics.products p
LEFT JOIN product_orders po
    ON p.product_id = po.product_id
LEFT JOIN product_returns pr
    ON p.product_id = pr.product_id
ORDER BY return_rate DESC;
"""


SUPPORT_AND_RETURNS_BY_PRODUCT = """
WITH product_returns AS (
    SELECT
        product_id,
        COUNT(*) AS total_returns
    FROM aibusinessanalytics.returns
    GROUP BY product_id
),
product_support AS (
    SELECT
        product_id,
        COUNT(*) AS total_tickets,
        COUNT(*) FILTER (
            WHERE category = 'Complaint'
        ) AS complaints
    FROM aibusinessanalytics.support_tickets
    GROUP BY product_id
)
SELECT
    p.product_name,
    COALESCE(pr.total_returns, 0) AS total_returns,
    COALESCE(ps.total_tickets, 0) AS support_tickets,
    COALESCE(ps.complaints, 0) AS complaints
FROM aibusinessanalytics.products p
LEFT JOIN product_returns pr
    ON p.product_id = pr.product_id
LEFT JOIN product_support ps
    ON p.product_id = ps.product_id
ORDER BY complaints DESC;
"""
TICKETS_BY_PRIORITY = """
SELECT
    priority,
    COUNT(*) AS ticket_count
FROM aibusinessanalytics.support_tickets
GROUP BY priority
ORDER BY ticket_count DESC;
"""


COMPLAINTS_BY_PRODUCT = """
SELECT
    p.product_name,
    COUNT(*) AS complaints
FROM aibusinessanalytics.support_tickets s
JOIN aibusinessanalytics.products p
    ON s.product_id = p.product_id
WHERE s.category = 'Complaint'
GROUP BY p.product_name
ORDER BY complaints DESC;
"""

PRODUCT_MONTHLY_REVENUE = """
SELECT
    DATE_TRUNC('month', o.order_date)::date AS month,
    p.product_name AS product,
    ROUND(SUM(oi.quantity * oi.price), 2) AS revenue
FROM aibusinessanalytics.order_items oi
JOIN aibusinessanalytics.orders o
    ON oi.order_id = o.order_id
JOIN aibusinessanalytics.products p
    ON oi.product_id = p.product_id
WHERE o.status = 'Completed'
GROUP BY month, p.product_name
ORDER BY month, revenue DESC;
"""


REGION_MONTHLY_REVENUE = """
SELECT
    DATE_TRUNC('month', order_date)::date AS month,
    region,
    ROUND(SUM(total_amount), 2) AS revenue
FROM aibusinessanalytics.orders
WHERE status = 'Completed'
GROUP BY month, region
ORDER BY month, revenue DESC;
"""


MONTHLY_RETURNS = """
SELECT
    DATE_TRUNC('month', return_date)::date AS month,
    COUNT(*) AS total_returns
FROM aibusinessanalytics.returns
GROUP BY month
ORDER BY month;
"""

MONTHLY_COMPLETED_ORDERS = """
SELECT
    DATE_TRUNC('month', order_date)::date AS month,
    COUNT(*) AS completed_orders
FROM aibusinessanalytics.orders
WHERE status = 'Completed'
GROUP BY month
ORDER BY month;
"""


MONTHLY_SUPPORT_TICKETS = """
SELECT
    DATE_TRUNC('month', created_at)::date AS month,
    COUNT(*) AS total_tickets
FROM aibusinessanalytics.support_tickets
GROUP BY month
ORDER BY month;
"""

MONTHLY_TICKETS_BY_CATEGORY = """
SELECT
    DATE_TRUNC('month', created_at)::date AS month,
    category,
    COUNT(*) AS ticket_count
FROM aibusinessanalytics.support_tickets
GROUP BY month, category
ORDER BY month, ticket_count DESC;
"""

MONTHLY_SUPPORT_BY_PRODUCT = """
SELECT
    DATE_TRUNC('month', s.created_at)::date AS month,
    p.product_name AS product,
    COUNT(*) AS ticket_count,
    COUNT(*) FILTER (
        WHERE s.category = 'Complaint'
    ) AS complaints,
    COUNT(*) FILTER (
        WHERE s.category = 'Refund'
    ) AS refunds,
    COUNT(*) FILTER (
        WHERE s.category = 'Technical Issue'
    ) AS technical_issues
FROM aibusinessanalytics.support_tickets s
JOIN aibusinessanalytics.products p
    ON s.product_id = p.product_id
GROUP BY month, p.product_name
ORDER BY month, ticket_count DESC;
"""


MONTHLY_RETURNS_BY_PRODUCT = """
SELECT
    DATE_TRUNC('month', r.return_date)::date AS month,
    p.product_name AS product,
    COUNT(*) AS return_count
FROM aibusinessanalytics.returns r
JOIN aibusinessanalytics.products p
    ON r.product_id = p.product_id
GROUP BY month, p.product_name
ORDER BY month, return_count DESC;
"""