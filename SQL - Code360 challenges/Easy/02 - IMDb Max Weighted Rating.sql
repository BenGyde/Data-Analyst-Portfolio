-- Print the genre and the maximum weighted rating among all the movies of that genre released in 2014 per genre.
--1. Do not print any row where either genre or the weighted rating is empty/null.
--2. weighted_rating = avgerge of (rating + metacritic/10.0)
--3. Keep the name of the columns as 'genre' and 'weighted_rating'
--4. The genres should be printed in alphabetical order.


SELECT genre, 
MAX((IMDB.Rating + IMDB.MetaCritic / 10.0) / 2.0) AS weighted_rating
FROM genre
JOIN IMDB on IMDB.Movie_id = genre.Movie_id
JOIN earning on earning.Movie_id = genre.Movie_id
WHERE genre is not NULL
	AND IMDB.Title like '% (2014)%'
GROUP by genre
HAVING MAX((IMDB.Rating + IMDB.MetaCritic / 10.0) / 2.0) > 0
ORDER by genre
