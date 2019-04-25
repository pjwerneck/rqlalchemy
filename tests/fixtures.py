# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime

from rqlalchemy import RQLQueryMixIn

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Query as BaseQuery
from sqlalchemy.orm import validates


Base = declarative_base()


class RQLQuery(BaseQuery, RQLQueryMixIn):
    pass


Base.query_class = RQLQuery


class User(Base):
    __tablename__ = 'user'

    user_id = sa.Column(sa.Integer, primary_key=True)
    full_name = sa.Column(sa.String(200))
    username = sa.Column(sa.String(80), unique=True)
    email = sa.Column(sa.String(120), unique=True)
    gender = sa.Column(sa.Enum('Male', 'Female'))
    birthdate = sa.Column(sa.Date)
    last_seen = sa.Column(sa.DateTime)
    distance = sa.Column(sa.Integer)
    active = sa.Column(sa.Boolean)
    city = sa.Column(sa.String(40))
    state = sa.Column(sa.String(2))

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
