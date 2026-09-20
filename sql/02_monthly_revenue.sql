-- Q2. What does the month-by-month picture look like, smoothed?
-- Technique: window frame (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) for a 3-month moving average.
-- The first two months average over fewer than three months.
WITH monthly AS (
    SELECT strftime('%Y-%m', InvoiceDate) AS month,
           COUNT(*)                       AS invoices,
           ROUND(SUM(Total), 2)           AS revenue
    FROM Invoice
    GROUP BY month
)
SELECT month,
       invoices,
       revenue,
       ROUND(AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m
FROM monthly
ORDER BY month;
