-- Q10. How does revenue split across support reps?
-- Technique: join Customer to Employee on SupportRepId, aggregate revenue through Invoice.
SELECT e.FirstName || ' ' || e.LastName                        AS support_rep,
       COUNT(DISTINCT c.CustomerId)                            AS customers,
       ROUND(SUM(i.Total), 2)                                  AS revenue,
       ROUND(SUM(i.Total) * 1.0 / COUNT(DISTINCT c.CustomerId), 2) AS revenue_per_customer
FROM Employee AS e
JOIN Customer AS c ON c.SupportRepId = e.EmployeeId
JOIN Invoice  AS i ON i.CustomerId   = c.CustomerId
GROUP BY e.EmployeeId
ORDER BY revenue DESC, support_rep;
