-- Q9. How much of the catalogue has never sold, by genre?
-- Technique: anti-join via LEFT JOIN ... IS NULL against the set of tracks that appear on any invoice.
WITH sold AS (
    SELECT DISTINCT TrackId FROM InvoiceLine
)
SELECT COALESCE(g.Name, 'Unknown')                                   AS genre,
       COUNT(*)                                                      AS tracks_in_catalogue,
       SUM(CASE WHEN s.TrackId IS NULL THEN 0 ELSE 1 END)            AS tracks_ever_sold,
       ROUND(100.0 * SUM(CASE WHEN s.TrackId IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS never_sold_pct
FROM Track AS t
LEFT JOIN Genre AS g ON g.GenreId = t.GenreId
LEFT JOIN sold  AS s ON s.TrackId = t.TrackId
GROUP BY genre
ORDER BY tracks_in_catalogue DESC, genre;
