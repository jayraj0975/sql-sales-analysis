-- Q6. RFM segmentation: Recency, Frequency, Monetary value.
-- Technique: PERCENT_RANK() places each customer on each measure, and thirds of that position give a
-- score from 1 (worst) to 3 (best). Recency is measured against the last invoice date in the data,
-- not today's date, so the result does not change when you run it later.
-- Ties: customers with the same value get the SAME score (a tie shares the lowest position of its
-- group). NTILE, which this query used before, splits ties by CustomerId, so two customers with
-- identical behaviour could land in different bands for no reason but their id. Here almost every
-- customer has the same number of invoices, so Frequency comes out (correctly) as almost constant:
-- it carries no information, and the segments are really Recency plus Monetary.
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
ranked AS (
    SELECT *,
           PERCENT_RANK() OVER (ORDER BY recency_days DESC) AS r_pos,   -- long ago = lowest
           PERCENT_RANK() OVER (ORDER BY frequency)         AS f_pos,
           PERCENT_RANK() OVER (ORDER BY monetary)          AS m_pos
    FROM per_customer
),
scored AS (
    SELECT CustomerId, recency_days, frequency, monetary,
           1 + (r_pos >= 1.0 / 3) + (r_pos >= 2.0 / 3) AS r_score,
           1 + (f_pos >= 1.0 / 3) + (f_pos >= 2.0 / 3) AS f_score,
           1 + (m_pos >= 1.0 / 3) + (m_pos >= 2.0 / 3) AS m_score
    FROM ranked
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
