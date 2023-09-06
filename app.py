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
            "password": generate_password_hash(request.form.get("password"))
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
                    existing_user["password"], request.form.get("password")):
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


@app.route("/library/<username>", methods=["GET", "POST"])
def library(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("library.html", username=username)

    return redirect(url_for("home"))


@app.route("/search", methods=["GET", "POST"])
def search():
    # get the movie/show title from the search input
    title = request.form.get("search")
    # get the movie/show ID from the API
    url = f"""https://api.themoviedb.org/3/search/multi?query={title}&
        include_adult=false&language=en-US&page=1"""
    # get json data
    json_data = get_api_data(url)
    print(json_data)
    # get the movie or show id fron json results
    media_id = json_data['results'][0]['id']
    # get media type
    media_type = json_data['results'][0]['media_type']
    # get the movie or show details
    media_data = get_media_details(media_id, media_type)
    media_certificate = get_media_certificate(media_id, media_type)
    if media_type == "movie":
        return render_template(
            "movie-search-result.html", media_data=media_data,
            media_certificate=media_certificate, media_type=media_type)
    if media_type == "tv":
        print(media_data)
        return render_template(
            "tv-search-result.html", media_data=media_data,
            media_certificate=media_certificate)


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


@app.route("/add_watchlist", methods=["GET", "POST"])
def add_watchlist():
    print(request.form.get("media_type"))
    if request.method == "POST" and request.form.get("media_type") == "movie":
        movie = {
            "title": request.form.get("title"),
            "genres": request.form.get("genres"),
            "overview": request.form.get("overview"),
            "certificate": request.form.get("certificate"),
            "release_date": request.form.get("release_date"),
            "runtime": request.form.get("runtime"),
            "created_by": session["user"]
         }
        mongo.db.movies.insert_one(movie)
        flash("Task Successfully Added")
        return redirect(url_for("home"))    
    return render_template("library.html")


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)   # Must change this to false before submission -----
