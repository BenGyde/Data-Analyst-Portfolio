--Write a SQL query to rank scores. If there is a tie between two scores, both should have the same ranking. 
--Note that after a tie, the next ranking number should be the next consecutive integer value. In other words, there should be no "holes" between ranks.

SELECT
  s.score,
  (
    SELECT COUNT(DISTINCT ss.score)
    FROM Scores ss
    WHERE ss.score > s.score
  ) + 1 AS "Rank"
FROM Scores s
ORDER BY s.score DESC
