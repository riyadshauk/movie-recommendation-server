# @author Riyad Shauk
# This is in-progress. The schema is pretty simple (3 tables):
# movie     user      recommendation
#  - id      - id       - id
#                       - movieID
#                       - userID

import psycopg2

def connect():
  connection = None
  try:
    connection = psycopg2.connect(user="postgres",
                                  password="postgres",
                                  host="127.0.0.1",
                                  port="5432",
                                  database="movie_challenge_recommendations")
    return connection
  except (Exception, psycopg2.Error) as error :
    print ("Error while connecting to PostgreSQL", error)

# https://pynative.com/python-postgresql-tutorial/
def test():
  connection = None
  cursor = None
  try:
    connection = connect()
    cursor = connection.cursor()
    # Print PostgreSQL Connection properties
    print ( connection.get_dsn_parameters(),"\n")
    # Print PostgreSQL version
    cursor.execute("SELECT version();")
    record = cursor.fetchone()
    print("You are connected to - ", record,"\n")
  except (Exception, psycopg2.Error) as error :
    print ("Error while connecting to PostgreSQL", error)
  finally:
    # closing database connection.
    if(connection):
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")



def run_query(query):
  # select count(*) from "user"
  connection = None
  cursor = None
  try:
    connection = connect()
    cursor.execute(query)
    return cursor
  except (Exception, psycopg2.Error) as error :
    print ("Error while connecting to PostgreSQL", error)
  finally:
    # closing database connection.
    if(connection):
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")

def get_num_users():
  return run_query('SELECT COUNT(*) FROM "user";').fetchone()

def get_num_movies():
  return run_query('SELECT COUNT(*) FROM movie;').fetchone()