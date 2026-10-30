CREATE OR REPLACE VIEW v_order_financials AS
SELECT
    orders.id AS order_id,
    orders.order_no,
    DATE(orders.placed_at) AS order_date,
    HOUR(orders.placed_at) AS business_hour,
    orders.table_id,
    orders.customer_id,
    CASE WHEN orders.customer_id IS NULL THEN 0 ELSE 1 END AS is_identified_customer,
    orders.status,
    orders.total_amount AS gross_sales,
    COALESCE(refunds.refund_amount, 0.00) AS refund_amount,
    orders.total_amount - COALESCE(refunds.refund_amount, 0.00) AS net_sales,
    COALESCE(order_items.quantity, 0) AS item_quantity
FROM orders
LEFT JOIN (
    SELECT payments.order_id, SUM(refunds.amount) AS refund_amount
    FROM payments
    JOIN refunds ON refunds.payment_id = payments.id
    GROUP BY payments.order_id
) AS refunds ON refunds.order_id = orders.id
LEFT JOIN (
    SELECT order_items.order_id, SUM(order_items.quantity) AS quantity
    FROM order_items
    GROUP BY order_items.order_id
) AS order_items ON order_items.order_id = orders.id
WHERE orders.status IN ('paid', 'partially_refunded', 'refunded');

CREATE OR REPLACE VIEW v_order_item_sales AS
SELECT
    order_items.id AS order_item_id,
    order_items.order_id,
    order_items.menu_item_id,
    order_items.quantity,
    order_items.unit_price,
    order_items.line_total AS gross_item_sales,
    CASE
        WHEN financials.gross_sales = 0 THEN order_items.line_total
        ELSE order_items.line_total * (1 - financials.refund_amount / financials.gross_sales)
    END AS net_item_sales,
    financials.order_date,
    financials.business_hour,
    financials.customer_id,
    financials.table_id
FROM order_items
JOIN v_order_financials AS financials ON financials.order_id = order_items.order_id;

CREATE OR REPLACE VIEW v_customer_order_summary AS
SELECT
    customer_id,
    MIN(order_date) AS first_order_date,
    MAX(order_date) AS last_order_date,
    COUNT(*) AS order_count,
    SUM(gross_sales) AS gross_sales,
    SUM(refund_amount) AS refund_amount,
    SUM(net_sales) AS net_sales,
    AVG(gross_sales) AS average_order_value
FROM v_order_financials
WHERE customer_id IS NOT NULL
GROUP BY customer_id;

