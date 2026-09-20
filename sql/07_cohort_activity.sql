-- Q7. Do customers keep buying? Cohorts by the year of their first purchase.
-- For each cohort, how many of its customers were active in each later year?
-- Technique: two CTEs (first purchase, distinct customer-years) joined to cohort sizes.
WITH first_purchase AS (
    SELECT CustomerId, MIN(strftime('%Y', InvoiceDate)) AS cohort_year
    FROM Invoice
    GROUP BY CustomerId
),
cohort_size AS (
    SELECT cohort_year, COUNT(*) AS customers_in_cohort
    FROM first_purchase
    GROUP BY cohort_year
),
activity AS (
    SELECT DISTINCT CustomerId, strftime('%Y', InvoiceDate) AS activity_year
    FROM Invoice
)
SELECT f.cohort_year,
       a.activity_year,
       cs.customers_in_cohort,
       COUNT(DISTINCT a.CustomerId) AS active_customers,
       ROUND(100.0 * COUNT(DISTINCT a.CustomerId) / cs.customers_in_cohort, 1) AS retention_pct
FROM first_purchase AS f
JOIN activity       AS a  ON a.CustomerId = f.CustomerId AND a.activity_year >= f.cohort_year
JOIN cohort_size    AS cs ON cs.cohort_year = f.cohort_year
GROUP BY f.cohort_year, a.activity_year
ORDER BY f.cohort_year, a.activity_year;
