-- Q8. Who are the top 15 artists by revenue?
-- Technique: a four-table join (InvoiceLine, Track, Album, Artist).
SELECT ar.Name                                   AS artist,
       COUNT(DISTINCT il.TrackId)                AS distinct_tracks_sold,
       SUM(il.Quantity)                          AS units,
       ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS revenue
FROM InvoiceLine AS il
JOIN Track  AS t  ON t.TrackId  = il.TrackId
JOIN Album  AS al ON al.AlbumId = t.AlbumId
JOIN Artist AS ar ON ar.ArtistId = al.ArtistId
GROUP BY ar.ArtistId
ORDER BY revenue DESC, artist
LIMIT 15;
