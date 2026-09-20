-- Q4. Which countries generate the revenue, and how much per customer?
-- Uses the billing country, i.e. where the sale was invoiced.
SELECT BillingCountry                                        AS country,
       COUNT(DISTINCT CustomerId)                            AS customers,
       COUNT(*)                                              AS invoices,
       ROUND(SUM(Total), 2)                                  AS revenue,
       ROUND(SUM(Total) * 1.0 / COUNT(DISTINCT CustomerId), 2) AS revenue_per_customer,
       ROUND(100.0 * SUM(Total) / SUM(SUM(Total)) OVER (), 2)  AS share_pct
FROM Invoice
GROUP BY BillingCountry
ORDER BY revenue DESC, country;
