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
    url = """https://api.themoviedb.org/3/tv/popular?language=en-US&page=1
        &without_genres=10767"""
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

        register = {
            "username": request.form.get("signup-username").lower(),
            "password": generate_password_hash(
                        request.form.get("signup-password")),
            "movie_list": [],
            "tv_list": [],
            "watchlist": [],
            "seenlist": []
        }
        mongo.db.users.insert_one(register)

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
    if session["user"]:
        # get user data from DB
        user = mongo.db.users.find_one({"username": session["user"]})
        # split the db lists from user
        movies = user["movie_list"]
        tv_shows = user["tv_list"]
        # get movie data
        movie_data = []
        for movie in movies:
            movie_id = movie["feature_id"]
            movie = mongo.db.movie_data.find_one(
                {"_id": ObjectId(movie_id)})
            movie_data.append(movie)
        tv_data = []
        # get tv data
        for tv_show in tv_shows:
            tv_show_id = tv_show["feature_id"]
            tv_show = mongo.db.tv_show_data.find_one(
                {"_id": ObjectId(tv_show_id)})
            tv_data.append(tv_show)
        return render_template(
            "library.html", movie_data=movie_data, tv_data=tv_data)
    return render_template("home.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    # get the movie/show title from the search input
    title = request.form.get("search")
    # get the movie/show ID from the API
    url = f"""https://api.themoviedb.org/3/search/multi?query={title}&
        include_adult=false&language=en-US&page=1"""
    # get json data
    json_data = get_api_data(url)
    # get the movie or show id fron json results
    media_id = json_data['results'][0]['id']
    # get media type
    media_type = json_data['results'][0]['media_type']
    # get the movie or show details
    media_data = get_media_details(media_id, media_type)
    media_certificate = get_media_certificate(media_id, media_type)
    return render_template(
            "search-result.html", media_data=media_data,
            media_certificate=media_certificate, media_type=media_type)


@app.route("/popular_feature/<title>")
def popular_feature(title):
    # get the movie/show ID from the API
    url = f"""https://api.themoviedb.org/3/search/multi?query={title}&
        include_adult=false&language=en-US&page=1"""
    # get json data
    json_data = get_api_data(url)
    # get the movie or show id fron json results
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
    if media_type == "movie":
        url = f"""https://api.themoviedb.org/3/{media_type}/
                {media_id}?language=en-US"""
    if media_type == "tv":
        url = f"""https://api.themoviedb.org/3/{media_type}/
                {media_id}?language=en-US"""
    # get json data
    json_data = get_api_data(url)
    return json_data


# use different API request format to get movie/show certificate
def get_media_certificate(media_id, media_type):
    if media_type == "movie":
        url = f"https://api.themoviedb.org/3/movie/{media_id}/release_dates"
        # get json data
        json_data = get_api_data(url)
        for item in json_data["results"]:
            if item["iso_3166_1"] == "GB":
                return item["release_dates"][0]["certification"]
    if media_type == "tv":
        url = f"https://api.themoviedb.org/3/tv/{media_id}/content_ratings"
        # get json data
        json_data = get_api_data(url)
        for item in json_data["results"]:
            if item["iso_3166_1"] == "GB":
                return item["rating"]


# get API request data
def get_api_data(url):
    # store the url response
    response = requests.get(url, headers=headers)
    return response.json()

# @app.route("/autocomplete", methods=["POST"])
# def autocomplete():
#     title = request.form.get("search")
#     # store the api url with the title included
#     url = f"""https://api.themoviedb.org/3/search/multi?query={title}&
#         include_adult=false&language=en-US&page=1"""
#     # get json data
#     json_data = get_api_data(url)
#     return render_template("search-result.html", json_data=json_data)


@app.route("/add_review/<feature_id>/<media_type>", methods=["GET", "POST"])
def add_review(feature_id, media_type):
    print("in function")
    if request.method == "POST" and media_type == "movie":
        review = request.form.get("review")
        mongo.db.movie_data.update_one({"_id": ObjectId(feature_id)}, {
                "$set": {"review": review}})
        flash("Review Edited")
        return redirect(url_for(
            "feature_details", feature_id=feature_id, media_type=media_type))


@app.route("/add_watchlist", methods=["GET", "POST"])
def add_watchlist():
    # get user data from DB
    user = mongo.db.users.find_one({"username": session["user"]})
    if request.method == "POST" and request.form.get("media_type") == "movie":
        # if movie is in the movie_data collection assign it to movie_in_db
        movie_in_db = mongo.db.movie_data.find_one(
            {"title": request.form.get("title")})
        # if movie_in_db has a value
        if movie_in_db:
            # get the ObjectId of the DB entry and create a Dict item
            movie_id = movie_in_db["_id"]
            # get the movie title
            title = request.form.get("title")
            # check if title is already in watchlist
            for item in user["watchlist"]:
                if title in item["title"]:
                    flash("Already in Watchlist")
                    return redirect(url_for(
                        "library", username=session["user"]))
            # create dict object to be added to DB
            movie = {
                "feature_id": ObjectId(movie_id),
                "title": request.form.get("title"),
                "media_type": request.form.get("media_type")
                }
            # add movie to the watchlist
            user["watchlist"].append(movie)
            # add movie to the movie_list
            user["movie_list"].append(movie)
            # update the DB movie_list & watchliat
            mongo.db.users.update_many(
                {"username": session["user"]},
                {"$set": {
                    "movie_list": user["movie_list"],
                    "watchlist": user["watchlist"]
                    }}
                )
        # if movie_in_db has a None value
        else:
            # create a dict object containing the movie data and add it to DB
            movie = {
                "title": request.form.get("title"),
                "genres": request.form.get("genres"),
                "overview": request.form.get("overview"),
                "certificate": request.form.get("certificate"),
                "release_date": request.form.get("release_date"),
                "runtime": request.form.get("runtime"),
                "poster": request.form.get("poster"),
                "media_type": request.form.get("media_type")
            }
            mongo.db.movie_data.insert_one(movie)
            # now that the movie exists in the database, grab the ObjectId
            movie_id = mongo.db.movie_data.find_one(
                {"title": request.form.get("title")})["_id"]
            # create dict object to be added to DB
            movie = {
                "feature_id": ObjectId(movie_id),
                "title": request.form.get("title"),
                "media_type": request.form.get("media_type")
                }
            # add movie to the watchlist
            user["watchlist"].append(movie)
            # add movie to the movie_list
            user["movie_list"].append(movie)
            # update the DB movie_list & watchliat
            mongo.db.users.update_many(
                {"username": session["user"]},
                {"$set": {
                    "movie_list": user["movie_list"],
                    "watchlist": user["watchlist"]
                    }}
                )
        flash("Added to Watchlist")
        return redirect(url_for("library", username=session["user"]))

    if request.method == "POST" and request.form.get("media_type") == "tv":
        # if show exists in tv_show_data collection assign it to tv_show_in_db
        tv_show_in_db = mongo.db.tv_show_data.find_one(
            {"title": request.form.get("title")})
        # if tv_show_in_db has a value
        if tv_show_in_db:
            # get the ObjectId of the DB entry and create a Dict item
            tv_show_id = tv_show_in_db["_id"]
            # get the tv show title
            title = request.form.get("title")
            # check title already in watchlist
            for item in user["watchlist"]:
                if title in item["title"]:
                    flash("Already in Watchlist")
                    return redirect(url_for(
                        "library", username=session["user"]))
            # create dict object to be added to DB
            tv_show = {
                "feature_id": ObjectId(tv_show_id),
                "title": request.form.get("title"),
                "media_type": request.form.get("media_type")
                }
            # add to the watchlist
            user["watchlist"].append(tv_show)
            # add to the tv_list
            user["tv_list"].append(tv_show)
            # update the DB watchlist array with the new one
            mongo.db.users.update_many(
                {"username": session["user"]},
                {"$set": {
                    "tv_list": user["tv_list"],
                    "watchlist": user["watchlist"]
                    }}
                )
        # if tv_show_in_db has a None value
        else:
            # create a dict object containing the tv show data and add it to DB
            tv_show = {
                "title": request.form.get("title"),
                "genres": request.form.get("genres"),
                "overview": request.form.get("overview"),
                "certificate": request.form.get("certificate"),
                "release_date": request.form.get("release_date"),
                "runtime": request.form.get("runtime"),
                "poster": request.form.get("poster"),
                "media_type": request.form.get("media_type")
            }
            mongo.db.tv_show_data.insert_one(tv_show)
            # now that the tv show exists in the database, grab the ObjectId
            tv_show_id = mongo.db.tv_show_data.find_one(
                {"title": request.form.get("title")})["_id"]
            # create dict object to be added to DB
            tv_show = {
                "feature_id": ObjectId(tv_show_id),
                "title": request.form.get("title"),
                "media_type": request.form.get("media_type")
                }
            # add to the watchlist
            user["watchlist"].append(tv_show)
            # append the watchlist_item dict to the watchlist array in user
            user["tv_list"].append(tv_show)
            # update the DB watchlist array with the new one
            mongo.db.users.update_many(
                {"username": session["user"]},
                {"$set": {
                    "tv_list": user["tv_list"],
                    "watchlist": user["watchlist"]
                    }}
                )
        flash("Added to Watchlist")
        return redirect(url_for("library", username=session["user"]))


@app.route("/add_seenlist", methods=["GET", "POST"])
def add_seenlist():
    if request.method == "POST" and request.form.get(
            "media_type") == "movie":
        print("its a movie")
        # get user data from DB
        user = mongo.db.users.find_one({"username": session["user"]})
        # if the movie data already exists in the DB
        if request.form.get("feature_id"):
            feature_id = request.form.get("feature_id")
            print("its in the database")
            if len(user["seenlist"]) > 0:
                for feature in user["seenlist"]:
                    if str(feature_id) == str(feature["feature_id"]):
                        flash("Already in Seenlist")
                        return redirect(url_for("library"))
                    else:
                        print("else")
                        continue
            else:
                for feature in user["watchlist"]:
                    if str(feature_id) == str(feature["feature_id"]):
                        print("its not in the seenlist")
                        item_index = user["watchlist"].index(feature)
                        watchlist_item = user["watchlist"].pop(item_index)
                        user["seenlist"].append(watchlist_item)
                        mongo.db.users.update_many(
                            {"username": session["user"]},
                            {"$set": {
                                "seenlist": user["seenlist"],
                                "watchlist": user["watchlist"]
                                }}
                            )
                        flash("Added to Seenlist")
                        return redirect(url_for("library"))
        else:
            print("its NOT in any list")
            # create a dict object containing the tv show data and add it to DB
            submit = {
                "title": request.form.get("title"),
                "genres": request.form.get("genres"),
                "overview": request.form.get("overview"),
                "certificate": request.form.get("certificate"),
                "release_date": request.form.get("release_date"),
                "runtime": request.form.get("runtime"),
                "poster": request.form.get("poster"),
                "media_type": request.form.get("media_type"),
            }
            mongo.db.movie_data.insert_one(submit)
            # now that the movie exists in the database, grab the ObjectId
            movie_id = mongo.db.movie_data.find_one(
                {"title": request.form.get("title")})["_id"]
            # create dict object to be added to DB
            movie = {
                "feature_id": ObjectId(movie_id),
                "title": request.form.get("title"),
                "media_type": request.form.get("media_type")
                }
            # add to the seenlist
            user["seenlist"].append(movie)
            # append the watchlist_item dict to the watchlist array in user
            user["movie_list"].append(movie)
            # update the DB watchlist array with the new one
            mongo.db.users.update_many(
                {"username": session["user"]},
                {"$set": {
                    "seenlist": user["watchlist"],
                    "movie_list": user["movie_list"]
                    }}
                )
            flash("Added to Seenlist")
            return redirect(url_for("library"))

    if request.method == "POST" and request.form.get(
            "media_type") == "tv":
        print("its a tv show")
        # get user data from DB
        user = mongo.db.users.find_one({"username": session["user"]})
        # if the movie data already exists in the DB
        if request.form.get("feature_id"):
            feature_id = request.form.get("feature_id")
            print("its in the database")
            if len(user["seenlist"]) > 0:
                for feature in user["seenlist"]:
                    if str(feature_id) == str(feature["feature_id"]):
                        flash("Already in Seenlist")
                        return redirect(url_for("library"))
                    else:
                        print("else")
                        continue
            else:
                for feature in user["watchlist"]:
                    if str(feature_id) == str(feature["feature_id"]):
                        print("its not in the seenlist")
                        item_index = user["watchlist"].index(feature)
                        watchlist_item = user["watchlist"].pop(item_index)
                        user["seenlist"].append(watchlist_item)
                        mongo.db.users.update_many(
                            {"username": session["user"]},
                            {"$set": {
                                "seenlist": user["seenlist"],
                                "watchlist": user["watchlist"]
                                }}
                            )
                        flash("Added to Seenlist")
                        return redirect(url_for("library"))
        else:
            print("its NOT in any list")
            # create a dict object containing the tv show data and add it to DB
            submit = {
                "title": request.form.get("title"),
                "genres": request.form.get("genres"),
                "overview": request.form.get("overview"),
                "certificate": request.form.get("certificate"),
                "release_date": request.form.get("release_date"),
                "runtime": request.form.get("runtime"),
                "poster": request.form.get("poster"),
                "media_type": request.form.get("media_type"),
            }
            mongo.db.tv_show_data.insert_one(submit)
            # now that the movie exists in the database, grab the ObjectId
            tv_show_id = mongo.db.tv_show_data.find_one(
                {"title": request.form.get("title")})["_id"]
            # create dict object to be added to DB
            tv_show = {
                "feature_id": ObjectId(tv_show_id),
                "title": request.form.get("title"),
                "media_type": request.form.get("media_type")
                }
            # add to the seenlist
            user["seenlist"].append(tv_show)
            # append the watchlist_item dict to the watchlist array in user
            user["tv_list"].append(tv_show)
            # update the DB watchlist array with the new one
            mongo.db.users.update_many(
                {"username": session["user"]},
                {"$set": {
                    "seenlist": user["seenlist"],
                    "tv_list": user["tv_list"]
                    }}
                )
            flash("Added to Seenlist")
            return redirect(url_for("library", username=session["user"]))


@app.route(
    "/feature_details/<feature_id>/<media_type>", methods=["GET", "POST"])
def feature_details(feature_id, media_type):
    if media_type == "movie":
        media_data = mongo.db.movie_data.find_one(
            {"_id": ObjectId(feature_id)})
        return render_template("feature-details.html", media_data=media_data)
    else:
        media_data = mongo.db.tv_show_data.find_one(
            {"_id": ObjectId(feature_id)})
        return render_template("feature-details.html", media_data=media_data)


@app.route("/delete_feature/<feature_id>/<media_type>")
def delete_feature(feature_id, media_type):
    if media_type == "movie":
        mongo.db.movie_data.delete_one({"_id": ObjectId(feature_id)})
    else:
        mongo.db.tv_show_data.delete_one({"_id": ObjectId(feature_id)})

    flash("Deleted from Library")
    return redirect(url_for("library", username=session["user"]))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)   # Must change this to false before submission -----
