import os.path

from application.__init__ import app, pg, imgFolder
import psycopg2.extras
from flask import Flask, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from application.models import User, Tour, Hotel, Review
from http import HTTPStatus


@app.route("/")
def hello():
    """
    Функция отображает страницу по адресу "/"
    :return: HTML страница и сессия пользователя, если тот вошел в систему
    """
    if "loggedin" in session:
        # User is loggedin show them the home page
        return render_template("index.html", username=session["username"])
    # User is not loggedin redirect to home page
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Функция проверяет введенные пользователем данные при входе в систему, создает сессию пользователя и отображает страницу по адресу "/login"
    :return: HTML страница
    """
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

        if int(account["roles_idroles"]) != 8:
            flash("Incorrect username/password")
            return render_template("login.html", error="Неверный логин или пароль")

        if account and check_password_hash(account["password"], password):
            password_rs = account["password"]
            # If account exists in users table in out database
            # Create session data, we can access this data in other routes
            session["loggedin"] = True
            session["id"] = account["idusers"]
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
    """
    Функция проверяет введенные данные при регистрации, добавляет пользователя в таблицу users и отображает страницу по адресу "/register"
    :return:
    """
    # todo: переделать регистрацию
    cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if (
            request.method == "POST"
            and "username" in request.form
            and "password" in request.form
            and "email" in request.form
            and "name" in request.form
            and "secondName" in request.form
            and "passport" in request.form
            and "kem" in request.form
            and "date" in request.form
    ):
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        _hashed_password = generate_password_hash(password)
        name = request.form["name"]
        secondName = request.form["secondName"]
        passport = request.form["passport"]
        kem = request.form["kem"]
        date = request.form["date"]

        if not User.isValid(username, email, password, passport, date):
            flash("Invalid Data")

        user = User(username, _hashed_password, name, secondName, email, passport, date, kem)
        user.insertUser()

        return redirect("/", code=HTTPStatus.FOUND)
    elif request.method == "POST":
        # Form is empty... (no POST data)
        flash("Please fill out the form!")
    return render_template("register.html")


@app.route("/logout")
def logout():
    """
    Функция прекращает сессию пользователя
    :return: Перенаправляет на страницу с адресом "/"
    """
    # Remove session data, this will log the user out
    session.pop("loggedin", None)
    session.pop("id", None)
    session.pop("username", None)

    # Redirect to login page
    return redirect("/", code=HTTPStatus.FOUND)


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    """
    Функция отображает профиль пользователя по адресу "/profile/<username>"
    :param username: имя пользователя
    :return: HTML страница
    """
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
        "select * from tours JOIN tours_has_users ON tours.idtours = tours_has_users.tours_idtours WHERE users_idusers=%s;",
        (session["id"],),
    )
    tours = cursor.fetchall()
    cursor.execute(
        "select * from hotels JOIN hotels_has_users ON hotels.idhotels = hotels_has_users.hotels_idhotels WHERE users_idusers=%s;",
        (session["id"],),
    )
    hotels = cursor.fetchall()
    return render_template(
        "Profile.html", username=username, email=email[0], tours=tours, hotels=hotels
    )


@app.route("/tours", methods=["GET", "POST"])
def tours():
    """
    Функция отображает страницу туров и обрабатывает POST запросы с фильтрами по адресу "/tours"
    :return: HTML страница
    """
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
    """
    Функция отображает страницу отелей и обрабатывает POST запросы с фильтрами по адресу "/hotels"
    :return: HTML страница
    """
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
        "SELECT * FROM hotels JOIN cities ON hotels.cities_idcities = cities.idcities"
    )
    hotels = cursor.fetchall()
    if "loggedin" in session:
        username = session["username"]
    else:
        username = None
    return render_template("hotels.html", username=username, hotels=hotels)


@app.route("/tours/<int:id>", methods=["GET", "POST"])
def tourPage(id):
    """
    Функция отображает конкретный тур, основываясь на его ID по адресу "/tours/<int:id>"
    :param id: ID тура
    :return: HTML страница
    """

    if request.method == "POST":
        if request.form["form-name"] == "review-form":
            review = Review(session['id'], request.form["review"], id)
            review.createReview()

    tour = Tour.getTourByID(id)
    cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(
        f"SELECT users.username, reviews.reviw FROM reviews JOIN tours_has_reviews ON (reviews.idreview = tours_has_reviews.reviews_idreview) JOIN users ON (reviews.users_idusers = users.idusers) WHERE tours_idtours = {id}")
    reviews = cursor.fetchall()
    return render_template("tourpage.html", tour=tour, username=session["username"], reviews=reviews)


@app.route("/agentLogin", methods=["GET", "POST"])
def agentLogin():
    """
    Функция проверяет введенные пользователем "тур-агент" данные при входе в систему, создает сессию пользователя и отображает страницу по адресу "/agentLogin"
    :return: HTML страница
    """
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
        if int(account["roles_idroles"]) != 7:
            flash("Incorrect username/password")
            return render_template("agentLogin.html", error="Неверный логин или пароль")

        if account and account["password"] == password:
            password_rs = account["password"]
            # If account exists in users table in out database
            # Create session data, we can access this data in other routes
            session["loggedin"] = True
            session["id"] = account["idusers"]
            session["username"] = account["username"]
            # Redirect to home page
            return redirect("/agent", code=HTTPStatus.FOUND)
        else:
            # Account doesnt exist or username/password incorrect
            flash("Incorrect username/password")
            return render_template("agentLogin.html", error="Неверный логин или пароль")
    return render_template("agentLogin.html", code=HTTPStatus.OK)


@app.route("/agent", methods=["GET", "POST"])
def agentPage():
    """
    Функция отображает страницу тур-агента
    :return: HTML страница
    """
    cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == "POST":
        if request.form["form-name"] == "getUser-form":
            cursor.execute("SELECT * FROM users WHERE username = %s", (request.form["userName"],))
            # Fetch one record and return result
            account = cursor.fetchone()
            if not account:
                render_template("agentPage.html", code=HTTPStatus.OK)
            cursor.execute(
                "select * from tours JOIN tours_has_users ON tours.idtours = tours_has_users.tours_idtours WHERE users_idusers=%s;",
                (account[0],),
            )
            tours = cursor.fetchall()
            cursor.execute(
                "select * from hotels JOIN hotels_has_users ON hotels.idhotels = hotels_has_users.hotels_idhotels WHERE users_idusers=%s;",
                (account[0],),
            )
            hotels = cursor.fetchall()

            return render_template("userCard.html", code=HTTPStatus.FOUND, user=account, tours=tours, hotels=hotels)

        if request.form["form-name"] == "createTour-form":
            cursor.execute(f"SELECT * FROM agencies WHERE users_idusers = {session['id']}")
            idAgencies = cursor.fetchone()
            idAgencies = idAgencies[0]
            cursor.execute(
                f"INSERT INTO tours (name, description, price, hotels_idhotels, isfire, angencies_idangencies, imgmetatour, logdesc) Values ('{request.form['name']}', '{request.form['description']}', {int(request.form['price'])}, {int(request.form['hotel'])}, {False}, {idAgencies}, '{'1.jpg'}', '{request.form['longdesc']}')"
            )
            flash('Uspeh')
            if not os.path.exists(f'{request.form["name"]}'):
                curentPath = os.path.dirname(__file__)
                print(curentPath)
                uploadFolder = os.path.join(curentPath, f'static\img\Tours\{request.form["name"]}')
                print(uploadFolder)
                os.mkdir(uploadFolder)
            img = request.files['img']
            filename = '1.jpg'
            img.save(os.path.join(uploadFolder, filename))
    cursor.execute("SELECT * FROM hotels")
    hotelsOption = cursor.fetchall()
    return render_template("agentPage.html", code=HTTPStatus.OK, hotelsOption=hotelsOption)

# todo: create self tour maker

# todo: create tour edit form for tour agent

# todo: create tour maker for tour agent

# todo: create places page

# todo: add service func
