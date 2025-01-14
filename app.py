import os
import requests
from flask import (
    Flask, flash, render_template, redirect, request, session, url_for)
# from flask_pymongo import PyMongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

# api authorisation
api_bearer = os.environ.get("API_BEARER")
headers = {
    "accept": "application/json",
    "Authorization": f"{api_bearer}"
    }

app = Flask(__name__)

# app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
# app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

# mongo = PyMongo(app)

try:
    # Initialize MongoDB client
    client = MongoClient(os.environ.get("MONGO_URI"), server_api=ServerApi('1'))

    # Specify the database (replace "mydatabase" with your actual database name)
    mongo = client.get_database(os.environ.get("MONGO_DBNAME", "mydatabase"))

    # Test the connection
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    mongo = None



def move_items():
    """
    Moves all items from the 'users' collection
    to the 'db.users' collection in the same database.
    """
    try:
        # Access the source and target collections
        source_collection = mongo["all_added_titles"]
        target_collection = mongo["db.all_added_titles"]

        # Fetch all documents from the source collection
        documents = list(source_collection.find({}))

        if not documents:
            print("No documents found in the source collection.")
            return

        # Insert documents into the target collection
        target_collection.insert_many(documents)

        # Optionally, delete documents from the source collection
        source_collection.delete_many({})

        print(f"Moved {len(documents)} documents to 'db.users' successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")


# get API request data
def get_api_data(url):
    """
    Accesses the API with the supplied url,
    gets the data and returns the data in json format
    """
    # store the url response
    response = requests.get(url, headers=headers)
    return response.json()


@app.route("/")
@app.route("/home")
def home():
    """
    Accesses the home page and retireves popular
    movies and TV shows data from the API
    """
    # access popular movies from api
    # store the api url with the title included
    url = "https://api.themoviedb.org/3/movie/popular?language=en-US&page=1"
    # get json data
    popular_movie_data = get_api_data(url)
    # split object in first 5 results
    popular_movie_data = popular_movie_data["results"][0:5]
    # access popular tv shows from api
    # store the api url with the title included
    url = "https://api.themoviedb.org/3/trending/tv/day?language=en-US"  # noqa
    # get json data
    popular_series_data = get_api_data(url)
    # split object into first 5 results
    popular_series_data = popular_series_data["results"][0:5]
    return render_template(
        "home.html", popular_series_data=popular_series_data,
        popular_movie_data=popular_movie_data)


@app.route("/register", methods=["POST"])
def register():
    """
    Allows new users to register an account.
    The user library is loaded upon successful registration
    and a database entry is made.
    if unsuccessful user is directed back to home
    """
    # register new account
    if request.method == "POST" and request.form.get("signup-username"):
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("signup-username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("home"))

        register_user = {
            "username": request.form.get("signup-username").lower(),
            "password": generate_password_hash(
                        request.form.get("signup-password")),
            "movie_list": [],
            "tv_list": [],
            "watchlist": [],
            "seenlist": []
        }
        mongo.db.users.insert_one(register_user)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("signup-username").lower()
        flash("Registration Successful!")
        return redirect(url_for("library", username=session["user"]))


@app.route("/login", methods=["POST"])
def login():
    """
    Allows users to log in with an existing account.
    The user library is loaded upon successful log in
    or directed back to home if unsuccessful
    """
    # log in
    if request.method == "POST" and request.form.get("login-username"):
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("login-username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"],
                    request.form.get("login-password")):
                session["user"] = request.form.get(
                    "login-username").lower()
                flash(f"Welcome, {request.form.get('login-username')}")
                return redirect(url_for(
                    "library", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("home"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("home"))


@app.route("/logout")
def logout():
    """
    Allows users to log out.
    The user is directed back to home
    """
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("home"))


@app.route("/library/")
def library():
    """
    loads the users library page and accesses the database to get
    the users list of films and tv shows to be displayed
    """
    if "user" in session:
        # get user data from DB
        user = mongo.db.users.find_one({"username": session["user"]})
        # split the db lists from user
        movie_list = user["movie_list"]
        tv_list = user["tv_list"]

        # get movie data
        movie_data = []
        for title_id in movie_list:
            # make sure id is in all_added_titles collection
            if mongo.db.all_added_titles.find_one({"id": title_id}):
                # get the movie title and poster from DB
                details = mongo.db.all_added_titles.find_one({"id": title_id})
                movie_data.append(details)
            # if id is not in all_added_titles collection
            else:
                # get details from the API
                movie = get_media_details(title_id, "movie")
                feature_info = {
                    "id": str(movie["id"]),
                    "title": movie["title"],
                    "poster_path": movie["poster_path"]
                }
                # insert details into all_added_titles collection
                mongo.db.all_added_titles.insert_one(feature_info)
                movie_data.append(feature_info)
        # get tv data
        tv_data = []
        for title_id in tv_list:
            # make sure id is in all_added_titles collection
            if mongo.db.all_added_titles.find_one({"id": title_id}):
                # get the movie title and poster from DB
                details = mongo.db.all_added_titles.find_one({"id": title_id})
                tv_data.append(details)
            # if id is not in all_added_titles collection
            else:
                # get details from the API
                tv_show = get_media_details(title_id, "tv")
                feature_info = {
                    "id": str(tv_show["id"]),
                    "title": tv_show["name"],
                    "poster_path": tv_show["poster_path"]
                }
                # insert details into all_added_titles collection
                mongo.db.all_added_titles.insert_one(feature_info)
                tv_data.append(feature_info)
        return render_template(
            "library.html", movie_data=movie_data, tv_data=tv_data)

    # user is not logged in - display home page
    return redirect(url_for("home"))


@app.route("/search", methods=["GET", "POST"])
@app.route("/search/<media_type>/<media_id>", methods=["GET", "POST"])
def search(media_type=None, media_id=None):
    """
    Allows the user to search for a movie or tv show from the search bar.
    If no result or no value supplied user is directed back to home.
    if search is successful the user is shown the
    full details of the requsted title.
    New feature - movies are suggested to the user as they type
    """
    # if feature_id request came from search suggestions
    if media_id:
        # get the movie or show details
        media_data = get_media_details(media_id, media_type)
        media_certificate = get_media_certificate(media_id, media_type)
        return render_template(
            "search-result.html", media_data=media_data,
            media_certificate=media_certificate, media_type=media_type)
    else:
        # get the movie/show title from the search input
        title = request.form.get("search")
        # check if title has a value
        if title:
            # get the movie/show ID from the API
            url = f"https://api.themoviedb.org/3/search/multi?query={title}&include_adult=false&language=en-US&page=1"  # noqa
            # get json data
            json_data = get_api_data(url)
            # get the movie or show id from json results
            if json_data["total_results"] > 0:
                media_id = json_data['results'][0]['id']
                # get media type
                media_type = json_data['results'][0]['media_type']
                # get the movie or show details
                media_data = get_media_details(media_id, media_type)
                media_certificate = get_media_certificate(media_id, media_type)
                return render_template(
                    "search-result.html", media_data=media_data,
                    media_certificate=media_certificate, media_type=media_type)
            else:
                flash(f'No results found for "{title}"')
                return redirect(url_for("home"))
        
    # title has no value - display home page
    return redirect(url_for("home"))
    

@app.route("/search_suggestions/<search_term>", methods=["GET", "POST"])
def search_suggestions(search_term):
    """
    Securely handles the api calls made by fetch in script.js when 
    the user begins typing search terms in the input field of the nav bar
    """
    if not search_term or len(search_term) <= 3:
        return {'results': []}

    # Make the request to the external API
    url = f'https://api.themoviedb.org/3/search/multi?query={search_term}&include_adult=false&language=en-US'
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return {'error': 'Failed to fetch data'}, response.status_code

    data = response.json()
    # Optionally, filter out 'person' media type if not needed
    results = [item for item in data['results'] if item['media_type'] != 'person'][:5]
    
    return {'results': results}


@app.route(
    "/feature_details/<feature_id>/<media_type>", methods=["GET", "POST"])
def feature_details(feature_id, media_type):
    """
    When the user to selects a movie or tv show from one of the lists
    (library, watchlist or seenlist) the API is accessed to provide all the
    details of that title and are displayed to the user
    """
    if "user" in session:
        # store the api url with the feature_id included
        if media_type == "movie":
            url = f"https://api.themoviedb.org/3/movie/{feature_id}/watch/providers"
        else:
            url = f"https://api.themoviedb.org/3/tv/{feature_id}/watch/providers"
        # get json data
        get_watch_providers = get_api_data(url)

        try:
            flatrate_providers = get_watch_providers['results']['GB'].get('flatrate', [])
            buy_providers = get_watch_providers['results']['GB'].get('buy', [])
            if flatrate_providers:
                watch_providers = flatrate_providers[0:3]
            elif buy_providers:
                watch_providers = buy_providers[0:3]
        except:
            watch_providers = []
        # get user data from DB
        user = mongo.db.users.find_one({"username": session["user"]})
        # get the movie or show details
        media_data = get_media_details(feature_id, media_type)
        media_certificate = get_media_certificate(feature_id, media_type)
        # get user rating data from DB
        rating_review = mongo.db.rating_review.find_one({
            "$and": [
                {"user_id": ObjectId(user["_id"])},
                {"feature_id": feature_id}
                ]})

        return render_template(
            "feature-details.html", media_data=media_data,
            media_type=media_type, media_certificate=media_certificate,
            rating_review=rating_review, watch_providers=watch_providers
        )
    else:
        # user is not logged in - display home page
        return redirect(url_for("home"))


@app.route("/popular_feature/<title>")
def popular_feature(title):
    """
    This function is called when the user clicks on a poster
    img from the home pages popular films and tv show section.
    It accesses the api to get the full details of the selected
    title and loads the results for the user to see
    """
    # get the movie/show ID from the API
    url = f"https://api.themoviedb.org/3/search/multi?query={title}&include_adult=false&language=en-US&page=1"  # noqa
    # get json data
    json_data = get_api_data(url)
    # get the movie or show id from json results
    media_id = json_data['results'][0]['id']
    # get media type
    media_type = json_data['results'][0]['media_type']
    # get the movie or show details
    media_data = get_media_details(media_id, media_type)
    media_certificate = get_media_certificate(media_id, media_type)
    return render_template(
            "search-result.html", media_data=media_data,
            media_certificate=media_certificate, media_type=media_type)


# use different API request format to get extended details
def get_media_details(media_id, media_type):
    """
    This function is called by various other functions and accesses
    the api to get details such as the title, poster_path and genres.
    The data is returned in json format
    """
    # get the movie/show ID from the API
    if media_type == "movie" or media_type == "tv":
        url = f"https://api.themoviedb.org/3/{media_type}/{media_id}?language=en-US"  # noqa
    # get json data
    json_data = get_api_data(url)
    return json_data


# use different API request format to get movie/show certificate
def get_media_certificate(media_id, media_type):
    """
    This function gets the age rating (certificate) for the movie or tv show
    """
    if media_type == "movie":
        url = f"https://api.themoviedb.org/3/movie/{media_id}/release_dates"
        # get json data
        json_data = get_api_data(url)
        # step through the listed countries until GB is found
        for country in json_data["results"]:
            if country["iso_3166_1"] == "GB":
                # find a valid certificate and return it
                for item in country["release_dates"]:
                    if item["certification"]:
                        return item["certification"]
    if media_type == "tv":
        url = f"https://api.themoviedb.org/3/tv/{media_id}/content_ratings"
        # get json data
        json_data = get_api_data(url)
        # step through listed countries until GB is found return certificate
        for item in json_data["results"]:
            if item["iso_3166_1"] == "GB":
                # return certificate
                return item["rating"]


@app.route("/add_rating_review/<media_type>", methods=["GET", "POST"])
def add_rating_review(media_type):
    """
    Allows the user to add their own personal rating and give a
    review or comment to the title they are currently viewing.
    This is then added to the database
    """
    if request.method == "POST":
        # get user data from DB
        user = mongo.db.users.find_one({"username": session["user"]})
        # get the feature id
        feature_id = request.form.get("id")
        # check if rating/review exist in DB
        rating_review = mongo.db.rating_review.find_one({
            "$and": [
                {"user_id": ObjectId(user["_id"])},
                {"feature_id": feature_id}
            ]})
        # if rating/review exists in the DB, update the DB
        if rating_review:
            mongo.db.rating_review.update_many(
                {"_id": ObjectId(rating_review["_id"])},
                {"$set": {
                    "rating": request.form.get("rating"),
                    "review": request.form.get("review")
                }})
            flash("Your Rating/Review has been Updated")
        # insert rating/review if none exists in the DB
        else:
            review_submit = {
                "user_id": user["_id"],
                "feature_id": feature_id,
                "rating": request.form.get("rating"),
                "review": request.form.get("review")
            }
            mongo.db.rating_review.insert_one(review_submit)
            flash("Your Rating/Review has been Added")
        return redirect(url_for(
            "feature_details", feature_id=feature_id, media_type=media_type))


@app.route("/add_watchlist", methods=["GET", "POST"])
def add_watchlist():
    """
    Allows the user to add a title to thier watchlist.
    the title id gets added to the users arrays in the database
    and the title, id and poster_path gets added to a shared
    collection (all_added_titles) in the database
    """
    # get user data from DB
    user = mongo.db.users.find_one({"username": session["user"]})
    if request.method == "POST":
        # get the id, title and poster path
        title_id = request.form.get("id")
        title = request.form.get("title")
        poster = request.form.get("poster")
        # check if id is already in watchlist
        if title_id in user["watchlist"]:
            # already exists
            flash(f'"{title}" is already in your Watchlist!')

        else:
            # check if it exists in the seenlist / if so, remove it
            for seen_id in user["seenlist"]:
                if title_id == seen_id:
                    # match found, remove from seenlist
                    list_index = user["seenlist"].index(seen_id)
                    user["seenlist"].pop(list_index)
            # add movie/tv show to the watchlist
            user["watchlist"].append(title_id)
            if request.form.get("media_type") == "movie":
                # check if already in movie_list
                found_movie_match = False
                for movie_id in user["movie_list"]:
                    if title_id == movie_id:
                        # yep, already exists in user's movie list
                        found_movie_match = True
                if found_movie_match is False:
                    # movie not in list yet, add to movie_list
                    user["movie_list"].append(title_id)
            elif request.form.get("media_type") == "tv":
                # check if already in tv_list
                found_tv_match = False
                for tv_id in user["tv_list"]:
                    if title_id == tv_id:
                        # yep, already exists in user's tv list
                        found_tv_match = True
                if found_tv_match is False:
                    # tv not in the list yet, add to tv_list
                    user["tv_list"].append(title_id)
            mongo.db.users.update_many(
                {"username": session["user"]},
                {"$set": {
                    "movie_list": user["movie_list"],
                    "tv_list": user["tv_list"],
                    "watchlist": user["watchlist"],
                    "seenlist": user["seenlist"]
                }}
            )
            # add/update the all_added_titles collection
            feature_info = {
                "id": title_id,
                "title": title,
                "poster_path": poster
            }
            if mongo.db.all_added_titles.find_one({"id": title_id}):
                mongo.db.all_added_titles.update_one(
                    {"id": title_id}, {"$set": feature_info})
            else:
                mongo.db.all_added_titles.insert_one(feature_info)
            flash(f'"{title }" added to your Watchlist')

        return redirect(url_for("library", username=session["user"]))


@app.route("/add_seenlist", methods=["GET", "POST"])
def add_seenlist():
    """
    Allows the user to add a title to thier seenlist.
    the title id gets added to the users arrays in the database
    and the title, id and poster_path gets added to a shared
    collection (all_added_titles) in the database
    """
    # get user data from DB
    user = mongo.db.users.find_one({"username": session["user"]})
    if request.method == "POST":
        # get the id, title and poster path
        title_id = request.form.get("id")
        title = request.form.get("title")
        poster = request.form.get("poster")
        # check if id is already in seenlist
        if title_id in user["seenlist"]:
            # already exists
            flash(f'"{title}" is already in your Seenlist!')

        else:
            # check if it exists in the watchlist / if so, remove it
            for watch_id in user["watchlist"]:
                if title_id == watch_id:
                    # match found, remove from watchlist
                    list_index = user["watchlist"].index(watch_id)
                    user["watchlist"].pop(list_index)
            # add movie/tv show to the seenlist
            user["seenlist"].append(title_id)
            if request.form.get("media_type") == "movie":
                # check if already in movie_list
                found_movie_match = False
                for movie_id in user["movie_list"]:
                    if title_id == movie_id:
                        # yep, already exists in user's movie list
                        found_movie_match = True
                if found_movie_match is False:
                    # movie not in list yet, add to movie_list
                    user["movie_list"].append(title_id)
            elif request.form.get("media_type") == "tv":
                # check if already in tv_list
                found_tv_match = False
                for tv_id in user["tv_list"]:
                    if title_id == tv_id:
                        # yep, already exists in user's tv list
                        found_tv_match = True
                if found_tv_match is False:
                    # tv not in the list yet, add to tv_list
                    user["tv_list"].append(title_id)
            mongo.db.users.update_many(
                {"username": session["user"]},
                {"$set": {
                    "movie_list": user["movie_list"],
                    "tv_list": user["tv_list"],
                    "watchlist": user["watchlist"],
                    "seenlist": user["seenlist"]
                }}
            )
            # add/update the all_added_titles collection
            feature_info = {
                "id": title_id,
                "title": title,
                "poster_path": poster
            }
            if mongo.db.all_added_titles.find_one({"id": title_id}):
                mongo.db.all_added_titles.update_one(
                    {"id": title_id}, {"$set": feature_info})
            else:
                mongo.db.all_added_titles.insert_one(feature_info)
            flash(f'"{title }" added to your Seenlist')

        return redirect(url_for("library", username=session["user"]))


@app.route("/view_watchlist/<media_type>", methods=["GET", "POST"])
def view_watchlist(media_type):
    """
    The user can view all the titles in thier watchlist. depending on the
    media_type supplied the user will see either the tv show watchlist or the
    films watchlist. This is done by accessing the id from the users specific
    watchlist array then matching the id to that in the all_added_titles
    collection and returning a list of dictionaries containing id's,
    titles and poster paths. If the title isn't in the all_added_titles
    collection the API is called and the title is added for future reference
    """
    if "user" in session:
        # get user data from DB
        user = mongo.db.users.find_one({"username": session["user"]})
        # get movie data
        watchlist = user["watchlist"]
        media_data = []
        if media_type == "movie":
            for title_id in watchlist:
                if title_id in user["movie_list"]:
                    # make sure id is in all_added_titles collection
                    if mongo.db.all_added_titles.find_one({"id": title_id}):
                        # get the movie title and poster from DB
                        details = mongo.db.all_added_titles.find_one(
                            {"id": title_id})
                        media_data.append(details)
                    else:
                        # get details from the API
                        movie = get_media_details(title_id, "movie")
                        feature_info = {
                            "id": str(movie["id"]),
                            "title": movie["title"],
                            "poster_path": movie["poster_path"]
                        }
                        # insert details into all_added_titles collection
                        mongo.db.all_added_titles.insert_one(feature_info)
                        media_data.append(feature_info)
        else:
            for title_id in watchlist:
                if title_id in user["tv_list"]:
                    # make sure id is in all_added_titles collection
                    if mongo.db.all_added_titles.find_one({"id": title_id}):
                        # get the movie title and poster from DB
                        details = mongo.db.all_added_titles.find_one(
                            {"id": title_id})
                        media_data.append(details)
                    else:
                        # get details from the API
                        tv_show = get_media_details(title_id, "tv")
                        feature_info = {
                            "id": str(tv_show["id"]),
                            "title": tv_show["name"],
                            "poster_path": tv_show["poster_path"]
                        }
                        # insert details into all_added_titles collection
                        mongo.db.all_added_titles.insert_one(feature_info)
                        media_data.append(feature_info)

        return render_template(
            "list.html", media_data=media_data,
            media_type=media_type, list_type="watchlist")
    else:
        # user is not logged in - display home page
        return redirect(url_for("home"))


@app.route("/view_seenlist/<media_type>", methods=["GET", "POST"])
def view_seenlist(media_type):
    """
    The user can view all the titles in thier seenlist. depending on the
    media_type supplied the user will see either the tv show seenlist or the
    films seenlist. This is done by accessing the id from the users specific
    seenlist array then matching the id to that in the all_added_titles
    collection and returning a list of dictionaries containing id's,
    titles and poster paths. If the title isn't in the all_added_titles
    collection the API is called and the title is added for future reference
    """
    if "user" in session:
        # get user data from DB
        user = mongo.db.users.find_one({"username": session["user"]})
        # get movie data
        seenlist = user["seenlist"]
        media_data = []
        if media_type == "movie":
            for title_id in seenlist:
                if title_id in user["movie_list"]:
                    # make sure id is in all_added_titles collection
                    if mongo.db.all_added_titles.find_one({"id": title_id}):
                        # get the movie title and poster from DB
                        details = mongo.db.all_added_titles.find_one(
                            {"id": title_id})
                        media_data.append(details)
                    else:
                        # get details from the API
                        movie = get_media_details(title_id, "movie")
                        feature_info = {
                            "id": str(movie["id"]),
                            "title": movie["title"],
                            "poster_path": movie["poster_path"]
                        }
                        # insert details into all_added_titles collection
                        mongo.db.all_added_titles.insert_one(feature_info)
                        media_data.append(feature_info)
        else:
            for title_id in seenlist:
                if title_id in user["tv_list"]:
                    # make sure id is in all_added_titles collection
                    if mongo.db.all_added_titles.find_one({"id": title_id}):
                        # get the movie title and poster from DB
                        details = mongo.db.all_added_titles.find_one(
                            {"id": title_id})
                        media_data.append(details)
                    else:
                        # get details from the API
                        tv_show = get_media_details(title_id, "tv")
                        feature_info = {
                            "id": str(tv_show["id"]),
                            "title": tv_show["name"],
                            "poster_path": tv_show["poster_path"]
                        }
                        # insert details into all_added_titles collection
                        mongo.db.all_added_titles.insert_one(feature_info)
                        media_data.append(feature_info)

        return render_template(
            "list.html", media_data=media_data,
            media_type=media_type, list_type="seenlist")
    else:
        # user is not logged in - display home page
        return redirect(url_for("home"))


@app.route("/delete/<feature_id>/<media_type>")
def delete(feature_id, media_type):
    """
    Allows the user to delete a title from thier collection
    """
    # get title before deleting from user's database
    feature = get_media_details(feature_id, media_type)
    if media_type == "movie":
        title = feature["title"]
    else:
        title = feature["name"]

    # get user data from DB
    user = mongo.db.users.find_one({"username": session["user"]})

    # if in watchlist, remove it
    for title_id in user["watchlist"]:
        if title_id == feature_id:
            # match found, remove from watchlist
            list_index = user["watchlist"].index(title_id)
            user["watchlist"].pop(list_index)

    # if in seenlist, remove it
    for title_id in user["seenlist"]:
        if title_id == feature_id:
            # match found, remove from seenlist
            list_index = user["seenlist"].index(title_id)
            user["seenlist"].pop(list_index)

    # if in movie_list, remove it
    for title_id in user["movie_list"]:
        if title_id == feature_id:
            # match found, remove from movie_list
            list_index = user["movie_list"].index(title_id)
            user["movie_list"].pop(list_index)

    # if in tv_list, remove it
    for title_id in user["tv_list"]:
        if title_id == feature_id:
            # match found, remove from tv_list
            list_index = user["tv_list"].index(title_id)
            user["tv_list"].pop(list_index)

    # save database changes
    mongo.db.users.update_many(
        {"username": session["user"]},
        {"$set": {
            "movie_list": user["movie_list"],
            "tv_list": user["tv_list"],
            "watchlist": user["watchlist"],
            "seenlist": user["seenlist"]
        }}
    )
    # find rating/review linked to this title
    rating_review = mongo.db.rating_review.find_one({
        "$and": [
            {"user_id": ObjectId(user["_id"])},
            {"feature_id": feature_id}
            ]})
    # if rating/review exists in the DB, update the DB
    if rating_review:
        mongo.db.rating_review.update_one(
            {"_id": ObjectId(rating_review["_id"])},
            {"$set": {
                "review": "",
                "rating": ""
            }})

    flash(f'"{title}" deleted from your Library')
    return redirect(url_for("library", username=session["user"]))


@app.route("/delete_review/<feature_id>/<media_type>")
def delete_review(feature_id, media_type):
    """
    Allows the user to delete reviews that have been added
    """
    # get user data from DB
    user = mongo.db.users.find_one({"username": session["user"]})
    rating_review = mongo.db.rating_review.find_one({
            "$and": [
                {"user_id": ObjectId(user["_id"])},
                {"feature_id": feature_id}
                ]})
    # if rating/review exists in the DB, update the DB
    if rating_review["review"]:
        mongo.db.rating_review.update_one(
            {"_id": ObjectId(rating_review["_id"])},
            {"$set": {
                "review": ""
            }})
    flash("Your review has been Deleted")
    return redirect(url_for(
            "feature_details", feature_id=feature_id, media_type=media_type))


@app.errorhandler(404)
def page_not_found(e):
    """
    Route for all 404 errors
    """
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    """
    Route for all 500 errors
    """
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=os.environ.get("DEBUG", False))
