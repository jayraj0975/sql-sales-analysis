-- Q3. How concentrated is revenue among customers (a Pareto / 80-20 view)?
-- Technique: ROW_NUMBER() for a stable rank, SUM() OVER () for the grand total,
-- and a running SUM() OVER (ORDER BY rank) for the cumulative share.
WITH customer_revenue AS (
    SELECT c.CustomerId,
           c.FirstName || ' ' || c.LastName AS customer,
           c.Country                        AS country,
           ROUND(SUM(i.Total), 2)           AS revenue
    FROM Customer AS c
    JOIN Invoice  AS i ON i.CustomerId = c.CustomerId
    GROUP BY c.CustomerId
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (ORDER BY revenue DESC, CustomerId) AS customer_rank,
           SUM(revenue)  OVER ()                                 AS total_revenue
    FROM customer_revenue
)
SELECT customer_rank,
       customer,
       country,
       revenue,
       ROUND(100.0 * revenue / total_revenue, 2) AS share_pct,
       ROUND(100.0 * SUM(revenue) OVER (ORDER BY customer_rank) / total_revenue, 2) AS cumulative_pct
FROM ranked
ORDER BY customer_rank;
