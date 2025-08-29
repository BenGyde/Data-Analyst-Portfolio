-- Print the title and ratings of the movies released in 2012 whose metacritic rating is more than 60 and Domestic collections exceed 10 Crores.

SELECT IMDB.Title, IMDB.Rating
FROM IMDB
JOIN earning ON IMDB.Movie_id = earning.Movie_id
	WHERE IMDB.Title like '% (2012)%'
	AND IMDB.MetaCritic > 60 
	AND earning.Domestic > 100000000
