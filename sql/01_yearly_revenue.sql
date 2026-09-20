-- Q1. How is revenue trending year over year?
-- Technique: CTE to aggregate, then LAG() window function for year-over-year change.
WITH yearly AS (
    SELECT strftime('%Y', InvoiceDate)      AS year,
           COUNT(*)                         AS invoices,
           COUNT(DISTINCT CustomerId)       AS customers,
           ROUND(SUM(Total), 2)             AS revenue
    FROM Invoice
    GROUP BY year
)
SELECT year,
       invoices,
       customers,
       revenue,
       ROUND(revenue * 1.0 / invoices, 2) AS avg_order_value,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY year))
                   / LAG(revenue) OVER (ORDER BY year), 1) AS yoy_pct
FROM yearly
ORDER BY year;
