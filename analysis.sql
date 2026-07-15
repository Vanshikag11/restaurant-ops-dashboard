-- ============================================================
-- Restaurant Performance & Delivery Ops Analysis
-- Dataset: orders, customers, restaurants (SQLite)
-- ============================================================

-- 1. DELIVERY OPS: Avg delivery time & order volume by city
-- Business question: which cities are dragging down delivery SLAs?
SELECT
    restaurant_city AS city,
    COUNT(*) AS total_orders,
    ROUND(AVG(delivery_time_mins), 1) AS avg_delivery_mins,
    ROUND(AVG(rating), 2) AS avg_rating
FROM orders
GROUP BY restaurant_city
ORDER BY avg_delivery_mins DESC;


-- 2. CUISINE PERFORMANCE: order value & rating by cuisine
-- Business question: which cuisines drive the most revenue per order,
-- and does speed correlate with satisfaction?
SELECT
    cuisine,
    COUNT(*) AS total_orders,
    ROUND(AVG(order_value), 0) AS avg_order_value,
    ROUND(SUM(order_value), 0) AS total_revenue,
    ROUND(AVG(delivery_time_mins), 1) AS avg_delivery_mins,
    ROUND(AVG(rating), 2) AS avg_rating
FROM orders
GROUP BY cuisine
ORDER BY total_revenue DESC;


-- 3. PEAK-HOUR STRAIN: delivery time during lunch/dinner peaks vs off-peak
-- Business question: how much does peak-hour demand degrade delivery SLA?
SELECT
    CASE
        WHEN CAST(strftime('%H', order_datetime) AS INTEGER) BETWEEN 12 AND 14 THEN 'Lunch Peak'
        WHEN CAST(strftime('%H', order_datetime) AS INTEGER) BETWEEN 19 AND 22 THEN 'Dinner Peak'
        ELSE 'Off-Peak'
    END AS time_band,
    COUNT(*) AS total_orders,
    ROUND(AVG(delivery_time_mins), 1) AS avg_delivery_mins
FROM orders
GROUP BY time_band
ORDER BY avg_delivery_mins DESC;


-- 4. CUSTOMER CHURN: customers with no order in the last 60 days
-- (using the dataset's max date as the analysis "today")
-- Business question: what % of the customer base is at risk of churn, by city?
WITH last_order AS (
    SELECT
        c.customer_id,
        c.city,
        MAX(o.order_datetime) AS last_order_date
    FROM customers c
    LEFT JOIN orders o ON o.customer_id = c.customer_id
    GROUP BY c.customer_id, c.city
),
analysis_date AS (
    SELECT MAX(order_datetime) AS max_date FROM orders
)
SELECT
    city,
    COUNT(*) AS total_customers,
    SUM(CASE
        WHEN last_order_date IS NULL
             OR julianday((SELECT max_date FROM analysis_date)) - julianday(last_order_date) > 60
        THEN 1 ELSE 0
    END) AS churned_customers,
    ROUND(100.0 * SUM(CASE
        WHEN last_order_date IS NULL
             OR julianday((SELECT max_date FROM analysis_date)) - julianday(last_order_date) > 60
        THEN 1 ELSE 0
    END) / COUNT(*), 1) AS churn_rate_pct
FROM last_order
GROUP BY city
ORDER BY churn_rate_pct DESC;


-- 5. RESTAURANT LEADERBOARD: top restaurants by revenue, with rank
-- Business question: who are the top 5 restaurants per city by revenue?
-- (window function - RANK)
WITH restaurant_revenue AS (
    SELECT
        r.restaurant_id,
        r.city,
        r.cuisine,
        COUNT(o.order_id) AS total_orders,
        ROUND(SUM(o.order_value), 0) AS total_revenue,
        ROUND(AVG(o.rating), 2) AS avg_rating
    FROM restaurants r
    JOIN orders o ON o.restaurant_id = r.restaurant_id
    GROUP BY r.restaurant_id, r.city, r.cuisine
),
ranked AS (
    SELECT *,
        RANK() OVER (PARTITION BY city ORDER BY total_revenue DESC) AS city_rank
    FROM restaurant_revenue
)
SELECT * FROM ranked
WHERE city_rank <= 5
ORDER BY city, city_rank;


-- 6. MONTH-OVER-MONTH ORDER VOLUME TREND (per city)
-- Business question: is order volume growing or shrinking city by city?
-- (window function - LAG for MoM delta)
WITH monthly AS (
    SELECT
        restaurant_city AS city,
        strftime('%Y-%m', order_datetime) AS month,
        COUNT(*) AS total_orders,
        ROUND(SUM(order_value), 0) AS total_revenue
    FROM orders
    GROUP BY restaurant_city, strftime('%Y-%m', order_datetime)
)
SELECT
    city,
    month,
    total_orders,
    total_revenue,
    total_orders - LAG(total_orders) OVER (PARTITION BY city ORDER BY month) AS order_mom_change
FROM monthly
ORDER BY city, month;


-- 7. LATE-DELIVERY RISK FLAG: orders that took >99th-percentile-equivalent long
-- Business question: which restaurants have chronic slow-delivery problems?
-- (using a fixed 55-min threshold as SLA breach, then ranking offenders)
SELECT
    restaurant_id,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN delivery_time_mins > 55 THEN 1 ELSE 0 END) AS sla_breaches,
    ROUND(100.0 * SUM(CASE WHEN delivery_time_mins > 55 THEN 1 ELSE 0 END) / COUNT(*), 1) AS breach_rate_pct
FROM orders
GROUP BY restaurant_id
HAVING total_orders >= 50
ORDER BY breach_rate_pct DESC
LIMIT 15;
