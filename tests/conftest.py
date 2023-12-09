# -*- coding: utf-8 -*-

import json
import os
import re

import pytest
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from .fixtures import Base
from .fixtures import Blog
from .fixtures import Post
from .fixtures import User


@pytest.fixture(scope="session")
def engine():
    return create_engine("sqlite:///:memory:", echo=True)


@pytest.fixture(scope="session")
def session(engine):
    Base.metadata.create_all(engine)

    session_ = sessionmaker(bind=engine)

    # load fixtures
    fpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "users.json")

    localsession = session_()
    with open(fpath) as f:
        users = json.load(f)

        for raw in users:
            obj = User(
                user_id=raw["index"],
                guid=raw["guid"],
                name=raw["name"],
                email=raw["email"],
                gender=raw["gender"],
                birthdate=raw["birthdate"],
                registered=raw["registered"],
                is_active=raw["isActive"],
                street_address=raw["street_address"],
                city=raw["city"],
                state=raw["state"],
                tags=raw["tags"],
                balance=raw["balance"],
                raw=raw,
                misc={
                    "eye_color": raw["eyeColor"],
                    "likes_apples": raw["favoriteFruit"] == "apple",
                    "unread_messages": int(
                        re.search(r"You have (\d+) unread messages", raw["greeting"]).group(1)
                    ),
                    "latitude": raw["latitude"],
                    "preferences": {
                        "favorite_fruit": raw["favoriteFruit"],
                    },
                    "location": {
                        "type": "Point",
                        "coordinates": [raw["longitude"], raw["latitude"]],
                    },
                    "balance": float(raw["balance"].strip("$").replace(",", "")),
                },
            )
            localsession.add(obj)

    localsession.commit()

    yield session_()

    Base.metadata.drop_all(engine)


@pytest.fixture(scope="session")
def blogs(session):
    blogs = []
    for uid in range(3):
        user = session.get(User, uid)
        for blog_no in range(3):
            blog = Blog(title=f"Blog {blog_no} for {user.name}", user=user)
            blogs.append(blog)
            session.add(blog)
    session.commit()
    yield (blogs)


@pytest.fixture(scope="session")
def posts(blogs, session):
    posts = []
    for blog in blogs:
        # Skip all those belonging to user 3 so that we have some blogs with
        # posts and some without.
        if blog.user.user_id == 2:
            continue
        for post_no in range(3):
            post = Post(title=f'Post {post_no} of blog "{blog.title}"', blog=blog)
            session.add(post)
            posts.append(post)
    session.commit()
    yield (posts)


@pytest.fixture(name="users")
def _users(session):
    return session.scalars(select(User)).all()
