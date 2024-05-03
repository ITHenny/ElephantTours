# -*- coding: utf-8 -*-
"""!@file
@brief Example Python program with Doxygen style comments.
"""
from application.__init__ import pg
import psycopg2.extras
from flask import flash
import re
from datetime import date, datetime


class User:
    """
    ! Класс пользователя
    """
    cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def __init__(self, username, password, firstname, secondname, email, passport, date, whoissued, role=8):
        """
        Метод инициализирует объект класса User


        :param username: Имя пользователя
        :param email: Почта пользователя
        :param password: Пароль пользователя
        """
        self.username = username
        self.email = email
        self.password = password
        self.firstname = firstname
        self.secondname = secondname
        self.passport = passport
        self.date = date
        self.whoissued = whoissued
        self.role = role

    @staticmethod
    def isValid(username, email, password, passport, dateVid):
        """
        Метод проверяет введенные пользователем данные при регистрации на валидность

        :param username: Имя пользователя
        :param email: Почта пользователя
        :param password: Пароль пользователя
        :return: True или Fasle

        """
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        account = cursor.fetchone()
        format = "%Y-%m-%d"

        print(dateVid, type(dateVid))
        if account:
            return False
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return False
        elif not re.match(r"[A-Za-z0-9]+", username):
            return False
        elif not len(passport) == 10:
            return False
        elif not datetime.strptime(dateVid, format) < datetime.today():
            return False
        elif not username or not password or not email:
            return False
        else:
            return True

    def insertUser(self):
        """
        Метод добавляет пользователя в таблицу users
        :return: None
        """
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "INSERT INTO users (username, password, firstname, secondname, email, passport, date, whoissued, roles_idroles) VALUES (%s,%s,%s, %s, %s,%s,%s, %s, %s)",
            (self.username, self.password, self.firstname, self.secondname, self.email, self.passport, self.date,
             self.whoissued, self.role),
        )
        pg.commit()
        flash("You have successfully registered!")


class Tour:
    """
    ! Класс тура
    """

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
            longdesc,
    ):
        """
        Метод инициализирует объект класса Tour
        :param id: id тура
        :param tourName: Название тура
        :param description: Описание тура
        :param imgMeta: Ссылка на фото тура
        :param price: Цена тура
        :param hotelName: Название отеля
        :param street: Название улицы
        :param house: Номер дома
        :param city: Название города
        :param country: Название страны
        :param stars: Количество звезд
        """
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
        self.longdesc = longdesc

    @staticmethod
    def getToursByFilters(request):
        """
        Метод врзващает список туров основываясь на фильтрах, выбранных пользователем
        :param request: Форма с фильтрами
        :return: Список туров
        """
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
        """
        Метод формирует SQL запрос основываясь на списке фильтров
        :param sql: список частей SQL запроса
        :return: список туров
        """
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
        """
        Метод возвращает тур по ID
        :param id: id тура
        :return: Объект класса Tour
        """
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        sql = f"SELECT * FROM tours JOIN hotels ON (tours.hotels_idhotels = hotels.idhotels) JOIN cities ON (hotels.cities_idcities = cities.idcities)  WHERE idtours = {id}"
        cursor.execute(sql)
        sql = cursor.fetchall()
        sql = sql[0]
        tour = Tour(
            id=sql[0],
            tourName=sql[1],
            description=sql[2],
            imgMeta=sql[7],
            price=sql[3],
            hotelName=sql[10],
            street=sql[12],
            house=sql[13],
            city=sql[18],
            country=sql[19],
            stars=sql[15],
            longdesc=sql[8]
        )
        return tour

    @staticmethod
    def insertLoveTour(tour_id, user_id):
        """
        Метод доавляет тур в избранное
        :param tour_id: ID тура
        :param user_id: ID пользователя
        :return: None
        """
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            f"SELECT * from tours_has_users WHERE users_idusers={user_id} AND tours_idtours={tour_id}"
        )
        sql = cursor.fetchall()
        if len(sql) == 0:
            cursor.execute(
                "INSERT INTO tours_has_users (tours_idtours, users_idusers) VALUES (%s,%s)",
                (tour_id, user_id),
            )
            pg.commit()
            flash("Liked!")

    @staticmethod
    def deleteLoveTour(tour_id, user_id):
        """
        Метод убирает тур из избранного
        :param tour_id: ID тура
        :param user_id: ID пользователя
        :return: None
        """
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "DELETE FROM tours_has_users WHERE tours_idtours=%s AND users_idusers=%s",
            (tour_id, user_id),
        )
        pg.commit()
        flash("Deleted!")


class Hotel:
    """
    ! Класс отеля
    """

    @staticmethod
    def getHotelsbyFilters(request):
        """
        Метод врзващает список отелей основываясь на фильтрах, выбранных пользователем
        :param request: Форма с фильтрами
        :return: Список отелей
        """
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
        """
        Метод формирует SQL запрос основываясь на списке фильтров
        :param sql: список частей SQL запроса
        :return: список отелей
        """
        if len(sql) > 1:
            str_sql = (
                    "SELECT * FROM hotels JOIN cities ON (hotels.cities_idcities = cities.idcities) WHERE "
                    + "AND".join(sql)
            )
        elif len(sql) == 1:
            str_sql = (
                    "SELECT * FROM hotels JOIN cities ON (hotels.cities_idcities = cities.idcities) WHERE "
                    + sql[0]
            )
        else:
            str_sql = (
                "SELECT * FROM hotels JOIN cities ON (hotels.cities_idcities = cities.idcities)"
            )
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(str_sql)
        hotels = cursor.fetchall()
        return hotels

    @staticmethod
    def deleteLoveHotel(hotel_id, user_id):
        """
        Метод убирает отель из избранного
        :param tour_id: ID отеля
        :param user_id: ID пользователя
        :return: None
        """
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            "DELETE FROM hotels_has_users WHERE hotels_idhotels=%s AND users_idusers=%s",
            (hotel_id, user_id),
        )
        pg.commit()
        flash("Deleted!")

    @staticmethod
    def insertLoveHotel(hotel_id, user_id):
        """
        Метод доавляет отель в избранное
        :param tour_id: ID отеля
        :param user_id: ID пользователя
        :return: None
        """
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            f"SELECT * from hotels_has_users WHERE users_idusers={user_id} AND hotels_idhotels={hotel_id}"
        )
        sql = cursor.fetchall()
        if len(sql) == 0:
            cursor.execute(
                "INSERT INTO hotels_has_users (hotels_idhotels, users_idusers) VALUES (%s,%s)",
                (hotel_id, user_id),
            )
            pg.commit()
            flash("Liked!")


class Review:
    def __init__(self, userid, text, tourid):
        self.userid = userid
        self.text = text
        self.tourid = tourid

    def createReview(self):
        cursor = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("INSERT INTO reviews (reviw, users_idusers) VALUES (%s, %s)", (self.text, self.userid))
        cursor.execute(f"SELECT idreview FROM reviews WHERE users_idusers = {self.userid}")
        reviewid = cursor.fetchall()
        reviewid = reviewid[-1]
        cursor.execute(f"INSERT INTO tours_has_reviews (tours_idtours, reviews_idreview) VALUES ({self.tourid}, {reviewid[0]})")
        pg.commit()

