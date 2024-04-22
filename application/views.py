from application.__init__ import app, pg
import psycopg2.extras
from flask import Flask, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from application.models import User, Tour, Hotel
from http import HTTPStatus


@app.route("/")
def hello():
    if "loggedin" in session:
        # User is loggedin show them the home page
        return render_template("index.html", username=session["username"])
    # User is not loggedin redirect to home page
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if (
            request.method == "POST"
            and "username" in request.form
            and "password" in request.form
    ):
        username = request.form["username"]
        password = request.form["password"]

        # Check if account exists using MySQL
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        # Fetch one record and return result
        account = cursor.fetchone()

        if int(account["role_id"]) != 3:
            flash("Incorrect username/password")
            return render_template("login.html", error="Неверный логин или пароль")

        if account and check_password_hash(account["password"], password):
            password_rs = account["password"]
            # If account exists in users table in out database
            # Create session data, we can access this data in other routes
            session["loggedin"] = True
            session["id"] = account["id_user"]
            session["username"] = account["username"]
            # Redirect to home page
            return redirect("/", code=HTTPStatus.FOUND)
        else:
            # Account doesnt exist or username/password incorrect
            flash("Incorrect username/password")
            return render_template("login.html", error="Неверный логин или пароль")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if (
            request.method == "POST"
            and "username" in request.form
            and "password" in request.form
            and "email" in request.form
    ):
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        _hashed_password = generate_password_hash(password)

        if not User.isValid(username, email, password):
            flash("Invalid Data")

        user = User(username, email, _hashed_password)
        user.insertUser()

        return redirect("/", code=HTTPStatus.FOUND)
    elif request.method == "POST":
        # Form is empty... (no POST data)
        flash("Please fill out the form!")
    return render_template("register.html")


@app.route("/logout")
def logout():
    # Remove session data, this will log the user out
    session.pop("loggedin", None)
    session.pop("id", None)
    session.pop("username", None)

    # Redirect to login page
    return redirect("/", code=HTTPStatus.FOUND)


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    if request.method == "POST" and request.form["form-name"] == "like-form":
        Tour.deleteLoveTour(request.form["like-form"], session["id"])
        return redirect(f"/profile/{session['username']}", code=HTTPStatus.FOUND)

    if request.method == "POST" and request.form["form-name"] == "like-form-hotel":
        Hotel.deleteLoveHotel(request.form["like-form"], session["id"])
        return redirect(f"/profile/{session['username']}", code=HTTPStatus.FOUND)

    # username = request.args.get("username", None)
    cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT email FROM users WHERE username = %s", (username,))
    email = cursor.fetchone()
    cursor.execute(
        "select * from tours JOIN tours_has_users ON tours.id_tour = tours_has_users.tour_id WHERE user_id=%s;",
        (session["id"],),
    )
    tours = cursor.fetchall()
    cursor.execute(
        "select * from hotels JOIN hotels_has_users ON hotels.id_hotel = hotels_has_users.hotel_id WHERE user_id=%s;",
        (session["id"],),
    )
    hotels = cursor.fetchall()
    return render_template(
        "Profile.html", username=username, email=email[0], tours=tours, hotels=hotels
    )


@app.route("/tours", methods=["GET", "POST"])
def tours():
    # Обрабоика отправленной формы фильтров
    if request.method == "POST":
        if request.form["form-name"] == "like-form":
            if not "loggedin" in session:
                return redirect("/login", code=HTTPStatus.FOUND)
            Tour.insertLoveTour(request.form["like-form"], session["id"])

        if request.form["form-name"] == "filter-form":
            tours = Tour.getToursByFilters(request)
            if "loggedin" in session:
                username = session["username"]
            else:
                username = None
            pg.commit()
            return render_template(
                "tours.html",
                username=username,
                tours=tours,
            )

    # Отображение всех туров
    cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM tours")
    tours = cursor.fetchall()
    if "loggedin" in session:
        username = session["username"]
    else:
        username = None
    pg.commit()
    return render_template("tours.html", username=username, tours=tours)


@app.route("/hotels", methods=["GET", "POST"])
def hotels():
    if request.method == "POST":

        if request.form["form-name"] == "like-form":
            if not "loggedin" in session:
                return redirect("/login", code=HTTPStatus.FOUND)
            Hotel.insertLoveHotel(request.form["like-form"], session["id"])
        if request.form["form-name"] == "filter-form":
            hotels = Hotel.getHotelsbyFilters(request)
            if "loggedin" in session:
                username = session["username"]
            else:
                username = None
            pg.commit()
            return render_template(
                "hotels.html",
                username=username,
                hotels=hotels,
            )

    cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(
        "SELECT * FROM hotels JOIN cities ON hotels.city_id = cities.id_city"
    )
    hotels = cursor.fetchall()
    if "loggedin" in session:
        username = session["username"]
    else:
        username = None
    return render_template("hotels.html", username=username, hotels=hotels)


@app.route("/tours/<int:id>")
def tourPage(id):
    tour = Tour.getTourByID(id)
    return render_template("tourpage.html", tour=tour, username=session["username"])


@app.route("/agentLogin")
def agentLogin():
    cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if (
            request.method == "POST"
            and "username" in request.form
            and "password" in request.form
    ):
        username = request.form["username"]
        password = request.form["password"]

        # Check if account exists using MySQL
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        # Fetch one record and return result
        account = cursor.fetchone()
        if int(account["role_id"]) != 2:
            flash("Incorrect username/password")
            return render_template("agentLogin.html", error="Неверный логин или пароль")

        if account and check_password_hash(account["password"], password):
            password_rs = account["password"]
            # If account exists in users table in out database
            # Create session data, we can access this data in other routes
            session["loggedin"] = True
            session["id"] = account["id_user"]
            session["username"] = account["username"]
            # Redirect to home page
            return redirect("/agent", code=HTTPStatus.FOUND)
        else:
            # Account doesnt exist or username/password incorrect
            flash("Incorrect username/password")
            return render_template("agentLogin.html", error="Неверный логин или пароль")
    return render_template("agentLogin.html", code=HTTPStatus.OK)


@app.route("/agent")
def agentPage():
    return render_template("index.html", code=HTTPStatus.OK)
