# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime

from flask import Flask
from flask import jsonify
from flask import request
from flask_sqlalchemy import BaseQuery
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates


sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from flask_rql import RQLQueryMixIn

db = SQLAlchemy()


class RQLQuery(BaseQuery, RQLQueryMixIn):
    pass

db.Model.query_class = RQLQuery


class User(db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200))
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    gender = db.Column(db.Enum('Male', 'Female'))
    birthdate = db.Column(db.Date)
    last_seen = db.Column(db.DateTime)
    distance = db.Column(db.Integer)
    active = db.Column(db.Boolean)
    city = db.Column(db.String(40))
    state = db.Column(db.String(2))

    @validates('birthdate')
    def validate_birthdate(self, key, value):
        return datetime.strptime(value, '%m/%d/%Y').date()

    @validates('last_seen')
    def validate_last_seen(self, key, value):
        return datetime.strptime(value, '%m/%d/%Y')

    def __iter__(self):
        yield 'user_id', self.user_id
        yield 'full_name', self.full_name
        yield 'username', self.username
        yield 'email', self.email
        yield 'gender', self.gender.lower()
        yield 'birthdate', self.birthdate.isoformat()
        yield 'last_seen', self.last_seen.isoformat()
        yield 'distance', self.distance
        yield 'active', self.active
        yield 'city', self.city
        yield 'state', self.state


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = True
    app.config['TESTING'] = True

    db.init_app(app)

    @app.route('/users')
    def list_users():
        return jsonify([dict(u) for u in User.query.rql(request).all()])

    return app
