--Write a SQL query for a report that provides the pairs (actor_id, director_id) where the actor have co-worked with the director at least 3 times.

Select 
	actor_id,
	director_id
FROM ActorDirector
GROUP by actor_id, director_id
HAVING count(*) >= 3
