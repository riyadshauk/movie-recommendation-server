This is a simple recommendation server written in Python/Flask.

Akshay wrote the original code (recommendation_server.py), but it's in-memory.

To-do:
- Extend to work with a database (currently decided on PostgreSQL)
- Only store user.id, movie.id, and recommendation.{id, movieID, userID}

OCI Compute VM IP - 132.145.210.229
User - ubuntu

The server is currently running inside a TMUX session. Follow these instructions to access the session:

1. To access - tmux attach -t movie-recommendation
2. To exit - Ctrl + b, d

Server runs on port 8000 and uses v2 as its source code.
