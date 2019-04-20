# Server runs on port 8000
# User rates movies on a scale of 1 - 10
#
# user_id starts from 0 to NUM_USERS-1
# movie_id starts from 0 to NUM_MOVIES-1
#
# @author Akshay (initial code)
# @author Riyad Shauk (refactor to use DB instead of in-memory)
#

from flask import Flask, request, jsonify
from scipy.stats import pearsonr
from apscheduler.schedulers.background import BackgroundScheduler
import numpy as np
import time
import json
import sys
import os
import copy
import schedule

# from db_layer import test
import db_layer

app = Flask(__name__)

port = int(os.environ.get("PORT", 8000))

# Enter number of users
NUM_USERS = 5 # db_layer.get_num_users()

# Enter of movies needed. 20 should be sufficient
NUM_MOVIES = 20 # db_layer.get_num_movies()

# Initialize movie ratings by user with random values from 1-10
# to initiate primary calculation of recommendations
user_ratings = np.random.choice(11, (NUM_USERS, NUM_MOVIES))

# Array which pairs every user with its most similar user
# in terms of taste in movies
user_recommendations = [[]]*NUM_USERS

# Read list of movies from movies_list.json
movies_list = {}

with open('movies_list.json', 'r') as jsonfile:
	movies_list = json.load(jsonfile)
movies_list = sorted(movies_list, key=lambda x: x['id'])

# ***
# REST endpoint - http://localhost:port/
# Gives a greeting
# ***
@app.route('/', methods=['GET'])
def index():
	print(movies_list)
	db_layer.test()
	return "Hello! This is the Recommendation server and it is a pleasure to meet you!"

# ***
# REST endpoint - http://localhost:port/reset
# Resets recommendations and re-initializes list of ratings
# with fake ratings. Good for restarting PoC
# ****
@app.route('/reset', methods=['GET'])
def reset():
	user_ratings = np.random.choice(11, (NUM_USERS, NUM_MOVIES))
	return jsonify({'success_code': 1, 'message': "", 'payload': ""}), 200

# ***
# REST endpoint - http://localhost:port/ratings
# Gives user's rating for a given movie
#
# Args - user_id, movie_id
# ***
@app.route('/ratings', methods=['POST'])
def update_rating():
	request_payload = request.get_json()

	user_id = request_payload['user_id']
	movie_id = request_payload['movie_id']
	rating = request_payload['rating']

	user_ratings[user_id, movie_id] = rating

	return jsonify({'success_code': 1, 'message': "", 'payload': ""}), 200

# ***
# REST endpoint - http://localhost:port/ratings
# Gives movie ratings of the user
#
# Args - user-id
# Returns - Array of JSON objects which have movies in it
# ***
@app.route('/ratings', methods=['GET'])
def get_ratings():
	user_id = int(request.args.get('user_id'))

	if user_id>=NUM_USERS:
		return jsonify({'success_code': 0, 'message': 'Breached total number of users'})

	current_user_ratings = []

	for i in range(len(user_ratings[user_id].tolist())):
		if user_ratings[user_id][i]!=0:
			current_movie = movies_list[i]
			current_movie['user_rating'] = str(user_ratings[user_id][i])
			current_user_ratings.append(current_movie)

	return jsonify({'success_code': 1, 'message': "", 'payload': current_user_ratings })

# ***
# REST endpoint - http://localhost:port/recommendations
# Gives array of JSON objects of movies which the user must watch
#
# Args - user_id
# ***
@app.route('/recommendations', methods=['GET'])
def get_recommendations():
	user_id = int(request.args.get('user_id'))

	user_recommendations_details = []

	for movie_id in user_recommendations[user_id]:
		user_recommendations_details.append(movies_list[movie_id])

	print(user_recommendations[user_id])
	return jsonify({'success_code': 1, 'message': "", 'payload': user_recommendations_details })

# DEBUGGING ONLY! - @app.route('/refresh', methods=['GET'])

# Function which periodically refreshes recommendations for each and every user
# Uses collaborative filtering with Pearson co-efficient as a metric of correlation
def refresh_recommendations():

	# Copy current list of user_ratings so app is not affected during refresh
	latest_ratings = np.array(user_ratings, copy=True)
	new_recommendations_for_all_users = []

	global user_recommendations

	print("\n\n****")

	for i in range(NUM_USERS):

		# For every user, match that user's ratings with the ratings of other users
		# Best match is decided by the highest value of Pearson co-efficient for correlation
		# Update recommendations for the user
		max_coefficient = -float('inf')
		most_correlated_user = -1

		for j in range(NUM_USERS):
			if i==j:
				continue

			pearson_coeff = pearsonr(latest_ratings[i,:].tolist(), latest_ratings[j,:].tolist())[0]
			
			if pearson_coeff>max_coefficient:
				max_coefficient = pearson_coeff
				most_correlated_user = j

		print(i,most_correlated_user,max_coefficient)

		new_recommendations_for_current_user = []

		for j in range(NUM_MOVIES):
			if latest_ratings[i][j]==0 and latest_ratings[most_correlated_user][j]!=0:
				new_recommendations_for_current_user.append(j)

		new_recommendations_for_all_users.append(new_recommendations_for_current_user)
		
	user_recommendations = copy.deepcopy(new_recommendations_for_all_users)
	print(latest_ratings)
	print(user_recommendations)
	print("Recommendations updated")
	print("****\n\n")

	# DEBUGGING ONLY! - return jsonify({'success_code': 1, 'message': "", 'payload': "" })


if __name__ == '__main__':

	# Starts period background task for refreshing recommendations.
	# Occurs every 5 seconds
	scheduler = BackgroundScheduler()
	scheduler.add_job(func=refresh_recommendations, trigger="interval", seconds=5)
	print("Started scheduler")
	scheduler.start()
    
    # Running server on port 8080. Accepts all IP addresses
	app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)