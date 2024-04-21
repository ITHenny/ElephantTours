from application.__init__ import pg
import psycopg2.extras
from flask import flash
import re


class User:
    cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    @staticmethod
    def isValid(username, email, password):
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        account = cursor.fetchone()
        if account:
            return False
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return False
        elif not re.match(r"[A-Za-z0-9]+", username):
            return False
        elif not username or not password or not email:
            return False
        else:
            return True

    def insertUser(self):
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "INSERT INTO users (username, email, password, role_id) VALUES (%s,%s,%s, 3)",
            (self.username, self.email, self.password),
        )
        pg.commit()
        flash("You have successfully registered!")


class Tour:
    def __init__(
        self,
        id,
        tourName,
        description,
        imgMeta,
        price,
        hotelName,
        street,
        house,
        city,
        country,
        stars,
    ):
        self.id = id
        self.tourName = tourName
        self.description = description
        self.imgMeta = imgMeta
        self.price = price
        self.hotelName = hotelName
        self.address = {
            "street": street,
            "house": house,
            "city": city,
            "country": country,
        }
        self.stars = stars

    @staticmethod
    def getToursByFilters(request):
        sql = []
        # Обработка горящих туров
        list_sql = []
        list_stars = [0, 1]
        for i in list_stars:
            if request.form.get(str(i), False):
                list_sql.append(f" is_fire = {i} ")
        if len(list_sql) > 0:
            sql.append("(" + "OR".join(list_sql) + ")")

        # Обработка цен на туры
        sql.append(
            f" price BETWEEN {int(request.form['min_price'])} AND {int(request.form['max_price'])}"
        )
        tours = Tour.createQuery(sql)
        return tours

    @staticmethod
    def createQuery(sql):
        # Составление запроса
        if len(sql) > 1:
            str_sql = "SELECT * FROM tours WHERE" + "AND".join(sql)
        elif len(sql) == 1:
            str_sql = "SELECT * FROM tours WHERE" + sql[0]
        else:
            str_sql = "SELECT * FROM tours"
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(str_sql)
        tours = cursor.fetchall()
        return tours

    @staticmethod
    def getTourByID(id):
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        sql = f"SELECT * FROM tours JOIN hotels ON (tours.hotel_id = hotels.id_hotel) JOIN cities ON (hotels.city_id = cities.id_city)  WHERE id_tour = {id}"
        cursor.execute(sql)
        sql = cursor.fetchall()
        sql = sql[0]
        tour = Tour(
            id=sql[0],
            tourName=sql[1],
            description=sql[2],
            imgMeta=sql[6],
            price=sql[7],
            hotelName=sql[9],
            street=sql[11],
            house=sql[12],
            city=sql[17],
            country=sql[18],
            stars=sql[14],
        )
        return tour

    @staticmethod
    def insertLoveTour(tour_id, user_id):
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            f"SELECT * from tours_has_users WHERE user_id={user_id} AND tour_id={tour_id}"
        )
        sql = cursor.fetchall()
        if len(sql) == 0:
            cursor.execute(
                "INSERT INTO tours_has_users (tour_id, user_id) VALUES (%s,%s)",
                (tour_id, user_id),
            )
            pg.commit()
            flash("Liked!")

    @staticmethod
    def deleteLoveTour(tour_id, user_id):
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "DELETE FROM tours_has_users WHERE tour_id=%s AND user_id=%s",
            (tour_id, user_id),
        )
        pg.commit()
        flash("Deleted!")


class Hotel:
    @staticmethod
    def getHotelsbyFilters(request):
        sql = []
        # Обработка фильтров по странам
        list_country = ["Англия", "Италия", "Франция"]
        list_sql = []

        # Поиск значений переданных в форме
        for i in list_country:
            if request.form.get(i, False):
                list_sql.append(f" country = '{i}' ")
        if len(list_sql) > 0:
            sql.append("(" + "OR".join(list_sql) + ")")

        list_sql = []
        list_stars = [1, 2, 3, 4, 5]

        for i in list_stars:
            if request.form.get(str(i), False):
                list_sql.append(f" stars = {i} ")
        if len(list_sql) > 0:
            sql.append("(" + "OR".join(list_sql) + ")")

        hotels = Hotel.createQuery(sql)
        return hotels

    @staticmethod
    def createQuery(sql):
        if len(sql) > 1:
            str_sql = (
                "SELECT * FROM hotels JOIN cities ON (hotels.city_id = cities.id_city) WHERE "
                + "AND".join(sql)
            )
        elif len(sql) == 1:
            str_sql = (
                "SELECT * FROM hotels JOIN cities ON (hotels.city_id = cities.id_city) WHERE "
                + sql[0]
            )
        else:
            str_sql = (
                "SELECT * FROM hotels JOIN cities ON (hotels.city_id = cities.id_city)"
            )
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(str_sql)
        hotels = cursor.fetchall()
        return hotels

    @staticmethod
    def deleteLoveHotel(hotel_id, user_id):
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "DELETE FROM hotels_has_users WHERE hotel_id=%s AND user_id=%s",
            (hotel_id, user_id),
        )
        pg.commit()
        flash("Deleted!")

    @staticmethod
    def insertLoveHotel(hotel_id, user_id):
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            f"SELECT * from hotels_has_users WHERE user_id={user_id} AND hotel_id={hotel_id}"
        )
        sql = cursor.fetchall()
        if len(sql) == 0:
            cursor.execute(
                "INSERT INTO hotels_has_users (hotel_id, user_id) VALUES (%s,%s)",
                (hotel_id, user_id),
            )
            pg.commit()
            flash("Liked!")
