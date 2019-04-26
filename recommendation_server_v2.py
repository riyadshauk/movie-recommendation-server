# Server runs on port 8000
# User rates movies on a scale of 1 - 10
#
# user_id starts from 0 to NUM_USERS-1
# movie_id starts from 0 to NUM_MOVIES-1

from flask import Flask, request, jsonify
from scipy.stats import pearsonr
from apscheduler.schedulers.background import BackgroundScheduler
import numpy as np
import os
import copy
import schedule
import requests

app = Flask(__name__)

port = int(os.environ.get("PORT", 8000))

# Enter number of users
NUM_USERS = 42

# Enter of movies needed. 20 should be sufficient
NUM_MOVIES = 1000

MOVIE_ID_TO_INDEX_MAP = dict()
INDEX_TO_MOVIE_ID_MAP = dict()

# Initialize movie ratings by user with random values from 1-10
# to initiate primary calculation of recommendations
user_ratings = np.random.choice(11, (NUM_USERS, NUM_MOVIES), p=[0.3,0.07,0.07,0.07,0.07,0.07,0.07,0.07,0.07,0.07,0.07])

# Array which pairs every user with its most similar user
# in terms of taste in movies
user_recommendations = [[]]*NUM_USERS

# Read list of movies from movies_list.json
# movies_list = {}

# with open('movies_list.json', 'r') as jsonfile:
# 	movies_list = json.load(jsonfile)
# movies_list = sorted(movies_list, key=lambda x: x['id'])

# ***
# REST endpoint - http://localhost:port/
# Gives a greeting
# ***
@app.route('/', methods=['GET'])
def index():
	return "Hello! This is the Recommendation server and it is a pleasure to meet you!"

# ***
# REST endpoint - http://localhost:port/reset
# Resets recommendations and re-initializes list of ratings
# with fake ratings. Good for restarting PoC
# ****
@app.route('/reset', methods=['GET'])
def reset():
	weekly_movie_refresh()
	# user_ratings = np.random.choice(11, (NUM_USERS, NUM_MOVIES), p=[0.3,0.07,0.07,0.07,0.07,0.07,0.07,0.07,0.07,0.07,0.07])
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

	user_ratings[user_id, MOVIE_ID_TO_INDEX_MAP[movie_id]] = rating

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

	for i in range(len(user_ratings[user_id, :])):
		if user_ratings[user_id, i]!=0:
			current_movie = dict()
			current_movie['movie_id'] = INDEX_TO_MOVIE_ID_MAP[i]
			current_movie['user_rating'] = int(user_ratings[user_id, i])
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

	if user_id>=NUM_USERS:
		return jsonify({'success_code': 0, 'message': 'Breached total number of users'})

	user_recommendations_details = []

	for movie_id in user_recommendations[user_id]:
		user_recommendations_details.append(movie_id)

	print(user_recommendations[user_id])
	return jsonify({'success_code': 1, 'message': "", 'payload': user_recommendations_details })

# DEBUGGING ONLY! - @app.route('/refresh', methods=['GET'])

# Function which periodically refreshes recommendations for each and every user
# Uses collaborative filtering with Pearson co-efficient as a metric of correlation
def refresh_recommendations():

	global INDEX_TO_MOVIE_ID_MAP, user_recommendations

	# Copy current list of user_ratings so app is not affected during refresh
	latest_ratings = np.array(user_ratings, copy=True)
	new_recommendations_for_all_users = []

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

		new_recommendations_for_current_user = []

		for j in range(NUM_MOVIES):
			if latest_ratings[i][j]==0 and latest_ratings[most_correlated_user][j]!=0:
				new_recommendations_for_current_user.append(INDEX_TO_MOVIE_ID_MAP[j])

		new_recommendations_for_all_users.append(new_recommendations_for_current_user)
		
	user_recommendations = copy.deepcopy(new_recommendations_for_all_users)
	print("\nRecommendations updated\n")

	# DEBUGGING ONLY! - return jsonify({'success_code': 1, 'message': "", 'payload': "" })


# Called periodically to update list of popular movies per week
def weekly_movie_refresh():

	global MOVIE_ID_TO_INDEX_MAP, INDEX_TO_MOVIE_ID_MAP

	tentative_movie_id_to_index_map = dict()
	tentative_index_to_movie_id_map = dict()

	base_url = "https://api.themoviedb.org/3/discover/movie?page="
	token_string = "&api_key=024d69b581633d457ac58359146c43f6"

	index_tracker_for_recommendation_arr = 0
	total_movie_count = 0

	for page_id in range(1,NUM_MOVIES//20 + 1,1):

		print("Processing page " + str(page_id))
		popular_movies = (requests.get(base_url + str(page_id) + token_string, data=None)).json()

		for movie in popular_movies["results"]:

			if total_movie_count==NUM_MOVIES:
				break

			tentative_movie_id_to_index_map[movie["id"]] = index_tracker_for_recommendation_arr
			tentative_index_to_movie_id_map[index_tracker_for_recommendation_arr] = movie["id"]

			index_tracker_for_recommendation_arr+=1
			total_movie_count+=1

		if total_movie_count==NUM_MOVIES:
			break

	user_ratings = np.random.choice(11, (NUM_USERS, NUM_MOVIES), p=[0.3,0.07,0.07,0.07,0.07,0.07,0.07,0.07,0.07,0.07,0.07])

	MOVIE_ID_TO_INDEX_MAP = tentative_movie_id_to_index_map
	INDEX_TO_MOVIE_ID_MAP = tentative_index_to_movie_id_map

	print("Processed " + str(total_movie_count) + " movies")

	refresh_recommendations()


if __name__ == '__main__':

	weekly_movie_refresh()

	# Starts periodic background task for refreshing list of popular movies
	# Occurs every week
	weekly_movie_update_task = BackgroundScheduler()
	weekly_movie_update_task.add_job(func=weekly_movie_refresh, trigger="interval", seconds=604800)
	print("Started scheduler for weekly movie updates")
	weekly_movie_update_task.start()

	# Starts periodic background task for refreshing recommendations.
	# Occurs every day
	recommendation_update_task = BackgroundScheduler()
	recommendation_update_task.add_job(func=refresh_recommendations, trigger="interval", seconds=86400)
	print("Started scheduler for updating recommendations")
	recommendation_update_task.start()
    
    # Running server on port 8080. Accepts all IP addresses
	app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
