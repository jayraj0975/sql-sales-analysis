-- Q5. Which genres earn the most?
-- Technique: joins across Invoice lines, Track and Genre. LEFT JOIN + COALESCE keeps
-- any track without a genre in the totals rather than silently dropping its revenue.
SELECT COALESCE(g.Name, 'Unknown')                          AS genre,
       COUNT(DISTINCT il.TrackId)                           AS distinct_tracks_sold,
       SUM(il.Quantity)                                     AS units,
       ROUND(SUM(il.UnitPrice * il.Quantity), 2)            AS revenue,
       ROUND(100.0 * SUM(il.UnitPrice * il.Quantity)
                   / SUM(SUM(il.UnitPrice * il.Quantity)) OVER (), 2) AS share_pct
FROM InvoiceLine AS il
JOIN Track       AS t ON t.TrackId = il.TrackId
LEFT JOIN Genre  AS g ON g.GenreId = t.GenreId
GROUP BY genre
ORDER BY revenue DESC, genre;
