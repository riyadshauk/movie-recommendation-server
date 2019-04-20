This is a simple recommendation server written in Python/Flask.

Akshay wrote the original code (recommendation_server.py), but it's in-memory.

To-do:
- Extend to work with a database (currently decided on PostgreSQL)
- Only store user.id, movie.id, and recommendation.{id, movieID, userID}