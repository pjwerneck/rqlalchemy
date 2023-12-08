# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from dateutil.parser import parse as parse_dt
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates

Base = declarative_base()


class Tag(Base):
    __tablename__ = "tag"

    tag_id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.user_id"))

    name = sa.Column(sa.String(30))


class User(Base):
    __tablename__ = "user"

    user_id = sa.Column(sa.Integer, primary_key=True)
    guid = sa.Column(sa.String(32), unique=True)
    name = sa.Column(sa.String(200))
    email = sa.Column(sa.String(120), unique=True)
    gender = sa.Column(sa.Enum("male", "female"))
    birthdate = sa.Column(sa.Date)
    registered = sa.Column(sa.DateTime)
    is_active = sa.Column(sa.Boolean)
    street_address = sa.Column(sa.String(200))
    city = sa.Column(sa.String(50))
    state = sa.Column(sa.String(2))
    balance = sa.Column(sa.Numeric(9, 2))

    _tags = relationship("Tag")
    tags = association_proxy("_tags", "name", creator=lambda name: Tag(name=name))

    @validates("birthdate")
    def validate_birthdate(self, key, value):
        return datetime.strptime(value, "%Y-%m-%d").date()

    @validates("registered")
    def validate_registered(self, key, value):
        return parse_dt(value)

    @validates("balance")
    def validate_balance(self, key, value):
        return Decimal(value.strip("$").replace(",", ""))

    def __iter__(self):
        yield "user_id", self.user_id
        yield "guid", self.guid
        yield "name", self.name
        yield "email", self.email
        yield "gender", self.gender.lower()
        yield "birthdate", self.birthdate.isoformat()
        yield "registered", self.registered.isoformat()
        yield "is_active", self.is_active
        yield "active", self.active
        yield "address", self.address


class Blog(Base):
    __tablename__ = "blog"
    id = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column(sa.Text)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.user_id"))

    user = relationship("User", backref="blogs")


class Post(Base):
    __tablename__ = "post"
    id = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column(sa.Text)
    blog_id = sa.Column(sa.Integer, sa.ForeignKey("blog.id"))

    blog = relationship("Blog", backref="posts")
