-- Q6. RFM segmentation: Recency, Frequency, Monetary value.
-- Technique: NTILE(3) scores each customer 1 (worst) to 3 (best) on each measure.
-- Recency is measured against the last invoice date in the data, not today's date,
-- so the result does not change when you run it later.
-- Caveat: in this dataset most customers have nearly the same number of invoices, so
-- frequency ties are common and NTILE splits them by CustomerId. Treat Frequency as weak.
WITH bounds AS (
    SELECT MAX(InvoiceDate) AS as_of FROM Invoice
),
per_customer AS (
    SELECT i.CustomerId,
           CAST(julianday((SELECT as_of FROM bounds)) - julianday(MAX(i.InvoiceDate)) AS INTEGER) AS recency_days,
           COUNT(*)                                                                                AS frequency,
           ROUND(SUM(i.Total), 2)                                                                  AS monetary
    FROM Invoice AS i
    GROUP BY i.CustomerId
),
scored AS (
    SELECT *,
           NTILE(3) OVER (ORDER BY recency_days DESC, CustomerId) AS r_score,  -- long ago = 1
           NTILE(3) OVER (ORDER BY frequency,        CustomerId)  AS f_score,
           NTILE(3) OVER (ORDER BY monetary,         CustomerId)  AS m_score
    FROM per_customer
)
SELECT CustomerId,
       recency_days, frequency, monetary,
       r_score, f_score, m_score,
       r_score + f_score + m_score AS total_score,
       CASE WHEN r_score + f_score + m_score >= 7 THEN 'High value'
            WHEN r_score + f_score + m_score >= 5 THEN 'Middle'
            ELSE 'Low value' END   AS segment
FROM scored
ORDER BY total_score DESC, monetary DESC, CustomerId;
