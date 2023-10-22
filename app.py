import os
import requests
import json
from flask import (
    Flask, flash, render_template, redirect, request, session, url_for)
from flask_pymongo import PyMongo
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

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


# get API request data
def get_api_data(url):
    # store the url response
    response = requests.get(url, headers=headers)
    return response.json()


@app.route("/")
@app.route("/home")
def home():
    # access popular movies from api
    # store the api url with the title included
    url = "https://api.themoviedb.org/3/movie/popular?language=en-US&page=1"
    # get json data
    popular_movie_data = get_api_data(url)
    # split object in first 5 results
    popular_movie_data = popular_movie_data["results"][0:5]
    # access popular tv shows from api
    # store the api url with the title included
    url = "https://api.themoviedb.org/3/tv/popular?language=en-US&page=1&without_genres=10767"  # noqa
    # get json data
    popular_series_data = get_api_data(url)
    # split object into first 5 results
    popular_series_data = popular_series_data["results"][0:5]
    return render_template(
        "home.html", popular_series_data=popular_series_data,
        popular_movie_data=popular_movie_data)


@app.route("/register", methods=["POST"])
def register():
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
                flash("Welcome, {}".format(
                    request.form.get("login-username")))
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
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("home"))


@app.route("/library/")
def library():
    if "user" in session:
        # get user data from DB
        user = mongo.db.users.find_one({"username": session["user"]})
        # split the db lists from user
        movie_list = user["movie_list"]
        tv_list = user["tv_list"]

        # get movie data
        movie_data = []
        for id in movie_list:
            # make sure id is in all_added_titles collection
            if mongo.db.all_added_titles.find_one({"id": id}):
                # get the movie title and poster from DB
                details = mongo.db.all_added_titles.find_one({"id": id})
                movie_data.append(details)
                # movie = get_media_details(id, "movie")
                # title = movie["title"]
                # poster = movie["poster_path"]
                # feature_info = {
                #     "id": id,
                #     "title": title,
                #     "poster_path": poster
                # }
                # if mongo.db.all_added_titles.find_one({"id": id}):
                #     mongo.db.all_added_titles.update({"id": id}, feature_info)
                # else:
                #     mongo.db.all_added_titles.insert_one(feature_info)
            # if id is not in all_added_titles collection
            else:
                # get details from the API
                movie = get_media_details(id, "movie")
                feature_info = {
                    "id": movie["id"],
                    "title": movie["title"],
                    "poster_path": movie["poster_path"]
                }
                # insert details into all_added_titles collection
                mongo.db.all_added_titles.insert_one(feature_info)
                movie_data.append(movie)
                        
        # get tv data
        tv_data = []
        for id in tv_list:
            # make sure id is in all_added_titles collection
            if mongo.db.all_added_titles.find_one({"id": id}):
                # get the movie title and poster from DB
                details = mongo.db.all_added_titles.find_one({"id": id})
                tv_data.append(details)

                # tv_show = get_media_details(id, "tv")
                # title = tv_show["name"]
                # poster = tv_show["poster_path"]
                # feature_info = {
                #     "id": id,
                #     "title": title,
                #     "poster_path": poster
                # }
                # if mongo.db.all_added_titles.find_one({"id": id}):
                #     mongo.db.all_added_titles.update({"id": id}, feature_info)
                # else:
                #     mongo.db.all_added_titles.insert_one(feature_info)
            # if id is not in all_added_titles collection
            else:
                # get details from the API
                tv_show = get_media_details(id, "tv")
                feature_info = {
                    "id": tv_show["id"],
                    "title": tv_show["name"],
                    "poster_path": tv_show["poster_path"]
                }
                # insert details into all_added_titles collection
                mongo.db.all_added_titles.insert_one(feature_info)
                movie_data.append(tv_show)
        return render_template(
            "library.html", movie_data=movie_data, tv_data=tv_data)

    # user is not logged in - display home page
    return render_template("home.html")


# def library():
#     if "user" in session:
#         # get user data from DB
#         user = mongo.db.users.find_one({"username": session["user"]})
#         # split the db lists from user
#         movie_list = user["movie_list"]
#         tv_list = user["tv_list"]

#         # get movie data
#         movie_data = []
#         for id in movie_list:
#             movie = get_media_details(id, "movie")
#             movie_data.append(movie)
#         # get tv data
#         tv_data = []
#         for id in tv_list:
#             tv_show = get_media_details(id, "tv")
#             tv_data.append(tv_show)
#         return render_template(
#             "library.html", movie_data=movie_data, tv_data=tv_data)

#     # user is not logged in - display home page
#     return render_template("home.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    # get the movie/show title from the search input
    title = request.form.get("search")
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


@app.route("/popular_feature/<title>")
def popular_feature(title):
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
    # get the movie/show ID from the API
    if media_type == "movie" or media_type == "tv":
        url = f"https://api.themoviedb.org/3/{media_type}/{media_id}?language=en-US"  # noqa
    # get json data
    json_data = get_api_data(url)
    return json_data


# use different API request format to get movie/show certificate
def get_media_certificate(media_id, media_type):
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


# @app.route("/autocomplete", methods=["POST"])
# def autocomplete():
#     title = request.form.get("search")
#     # store the api url with the title included
#     url = f"https://api.themoviedb.org/3/search/multi?query={title}&include_adult=false&language=en-US&page=1"  # noqa
#     # get json data
#     json_data = get_api_data(url)
#     return render_template("search-result.html", json_data=json_data)


@app.route("/add_rating_review/<media_type>", methods=["GET", "POST"])
def add_rating_review(media_type):
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
        # insert rating/review if none exists in the DB
        else:
            review_submit = {
                "user_id": user["_id"],
                "feature_id": feature_id,
                "rating": request.form.get("rating"),
                "review": request.form.get("review")
            }
            mongo.db.rating_review.insert_one(review_submit)
            flash("Your Rating/Review have been Added")
        return redirect(url_for(
            "feature_details", feature_id=feature_id, media_type=media_type))


@app.route("/add_watchlist", methods=["GET", "POST"])
def add_watchlist():
    # get user data from DB
    user = mongo.db.users.find_one({"username": session["user"]})
    if request.method == "POST":
        # get the id, title and poster path
        id = request.form.get("id")
        title = request.form.get("title")
        poster = request.form.get("poster")
        # check if id is already in watchlist
        if id in user["watchlist"]:
            # already exists
            flash(f'"{title}" is already in your Watchlist!')

        else:
            # check if it exists in the seenlist / if so, remove it
            for seen_id in user["seenlist"]:
                if id == seen_id:
                    # match found, remove from seenlist
                    list_index = user["seenlist"].index(seen_id)
                    user["seenlist"].pop(list_index)
            # add movie/tv show to the watchlist
            user["watchlist"].append(id)
            if request.form.get("media_type") == "movie":
                # check if already in movie_list
                found_movie_match = False
                for movie_id in user["movie_list"]:
                    if id == movie_id:
                        # yep, already exists in user's movie list
                        found_movie_match = True
                if found_movie_match is False:
                    # movie not in list yet, add to movie_list
                    user["movie_list"].append(id)
            elif request.form.get("media_type") == "tv":
                # check if already in tv_list
                found_tv_match = False
                for tv_id in user["tv_list"]:
                    if id == tv_id:
                        # yep, already exists in user's tv list
                        found_tv_match = True
                if found_tv_match is False:
                    # tv not in the list yet, add to tv_list
                    user["tv_list"].append(id)
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
                "id": id,
                "title": title,
                "poster_path": poster
            }
            if mongo.db.all_added_titles.find_one({"id": id}):
                mongo.db.all_added_titles.update({"id": id}, feature_info)
            else:
                mongo.db.all_added_titles.insert_one(feature_info)
            flash(f'"{title }" added to your Watchlist')

        return redirect(url_for("library", username=session["user"]))


@app.route("/add_seenlist", methods=["GET", "POST"])
def add_seenlist():
    # get user data from DB
    user = mongo.db.users.find_one({"username": session["user"]})
    if request.method == "POST":
        # get the id, title and poster path
        id = request.form.get("id")
        title = request.form.get("title")
        poster = request.form.get("poster")
        # check if id is already in seenlist
        if id in user["seenlist"]:
            # already exists
            flash(f'"{title}" is already in your Seenlist!')

        else:
            # check if it exists in the watchlist / if so, remove it
            for watch_id in user["watchlist"]:
                if id == watch_id:
                    # match found, remove from watchlist
                    list_index = user["watchlist"].index(watch_id)
                    user["watchlist"].pop(list_index)
            # add movie/tv show to the seenlist
            user["seenlist"].append(id)
            if request.form.get("media_type") == "movie":
                # check if already in movie_list
                found_movie_match = False
                for movie_id in user["movie_list"]:
                    if id == movie_id:
                        # yep, already exists in user's movie list
                        found_movie_match = True
                if found_movie_match is False:
                    # movie not in list yet, add to movie_list
                    user["movie_list"].append(id)
            elif request.form.get("media_type") == "tv":
                # check if already in tv_list
                found_tv_match = False
                for tv_id in user["tv_list"]:
                    if id == tv_id:
                        # yep, already exists in user's tv list
                        found_tv_match = True
                if found_tv_match is False:
                    # tv not in the list yet, add to tv_list
                    user["tv_list"].append(id)
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
                "id": id,
                "title": title,
                "poster_path": poster
            }
            if mongo.db.all_added_titles.find_one({"id": id}):
                mongo.db.all_added_titles.update({"id": id}, feature_info)
                print("done")
            else:
                mongo.db.all_added_titles.insert_one(feature_info)
            flash(f'"{title }" added to your Seenlist')

        return redirect(url_for("library", username=session["user"]))


@app.route("/view_watchlist/<media_type>", methods=["GET", "POST"])
def view_watchlist(media_type):
    # get user data from DB
    user = mongo.db.users.find_one({"username": session["user"]})
    # get movie data
    watchlist = user["watchlist"]
    media_data = []
    if media_type == "movie":
        for id in watchlist:
            if id in user["movie_list"]:
                # make sure id is in all_added_titles collection
                if mongo.db.all_added_titles.find_one({"id": id}):
                    # movie = get_media_details(id, "movie")

                    # get the movie title and poster from DB
                    details = mongo.db.all_added_titles.find_one({"id": id})
                    media_data.append(details)
                    # media_data.append(movie)
                else:
                    # get details from the API
                    movie = get_media_details(id, "movie")
                    feature_info = {
                        "id": movie["id"],
                        "title": movie["title"],
                        "poster_path": movie["poster_path"]
                    }
                    # insert details into all_added_titles collection
                    mongo.db.all_added_titles.insert_one(feature_info)
                    media_data.append(movie)
    else:
        for id in watchlist:
            if id in user["tv_list"]:
                # make sure id is in all_added_titles collection
                if mongo.db.all_added_titles.find_one({"id": id}):
                    # tv_show = get_media_details(id, "tv")
                    
                    # get the movie title and poster from DB
                    details = mongo.db.all_added_titles.find_one({"id": id})
                    media_data.append(details)
                    # media_data.append(tv_show)
                else:
                    # get details from the API
                    tv_show = get_media_details(id, "tv")
                    feature_info = {
                        "id": tv_show["id"],
                        "title": tv_show["name"],
                        "poster_path": tv_show["poster_path"]
                    }
                    # insert details into all_added_titles collection
                    mongo.db.all_added_titles.insert_one(feature_info)
                    media_data.append(tv_show)

    return render_template(
        "list.html", media_data=media_data,
        media_type=media_type, list_type="watchlist")


@app.route("/view_seenlist/<media_type>", methods=["GET", "POST"])
def view_seenlist(media_type):
    # get user data from DB
    user = mongo.db.users.find_one({"username": session["user"]})
    # get movie data
    seenlist = user["seenlist"]
    media_data = []
    if media_type == "movie":
        for id in seenlist:
            if id in user["movie_list"]:
                # make sure id is in all_added_titles collection
                if mongo.db.all_added_titles.find_one({"id": id}):
                    # movie = get_media_details(id, "movie")

                    # get the movie title and poster from DB
                    details = mongo.db.all_added_titles.find_one({"id": id})
                    media_data.append(details)
                    # media_data.append(movie)
                else:
                    # get details from the API
                    movie = get_media_details(id, "movie")
                    feature_info = {
                        "id": movie["id"],
                        "title": movie["title"],
                        "poster_path": movie["poster_path"]
                    }
                    # insert details into all_added_titles collection
                    mongo.db.all_added_titles.insert_one(feature_info)
                    media_data.append(movie)
    else:
        for id in seenlist:
            if id in user["tv_list"]:
                # make sure id is in all_added_titles collection
                if mongo.db.all_added_titles.find_one({"id": id}):
                    # tv_show = get_media_details(id, "tv")

                    # get the movie title and poster from DB
                    details = mongo.db.all_added_titles.find_one({"id": id})
                    media_data.append(details)
                    # media_data.append(tv_show)
                else:
                    # get details from the API
                    tv_show = get_media_details(id, "tv")
                    feature_info = {
                        "id": tv_show["id"],
                        "title": tv_show["name"],
                        "poster_path": tv_show["poster_path"]
                    }
                    # insert details into all_added_titles collection
                    mongo.db.all_added_titles.insert_one(feature_info)
                    media_data.append(tv_show)

    return render_template(
        "list.html", media_data=media_data,
        media_type=media_type, list_type="seenlist")


@app.route(
    "/feature_details/<feature_id>/<media_type>", methods=["GET", "POST"])
def feature_details(feature_id, media_type):
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
        rating_review=rating_review
    )


@app.route("/delete/<feature_id>/<media_type>")
def delete(feature_id, media_type):
    # get title before deleting from user's database
    feature = get_media_details(feature_id, media_type)
    if media_type == "movie":
        title = feature["title"]
    else:
        title = feature["name"]

    # get user data from DB
    user = mongo.db.users.find_one({"username": session["user"]})

    # if in watchlist, remove it
    for id in user["watchlist"]:
        if id == feature_id:
            # match found, remove from watchlist
            list_index = user["watchlist"].index(id)
            user["watchlist"].pop(list_index)

    # if in seenlist, remove it
    for id in user["seenlist"]:
        if id == feature_id:
            # match found, remove from seenlist
            list_index = user["seenlist"].index(id)
            user["seenlist"].pop(list_index)

    # if in movie_list, remove it
    for id in user["movie_list"]:
        if id == feature_id:
            # match found, remove from movie_list
            list_index = user["movie_list"].index(id)
            user["movie_list"].pop(list_index)

    # if in tv_list, remove it
    for id in user["tv_list"]:
        if id == feature_id:
            # match found, remove from tv_list
            list_index = user["tv_list"].index(id)
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

    flash(f'"{title}" deleted from your Library')
    return redirect(url_for("library", username=session["user"]))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)   # Must change this to false before submission -----
