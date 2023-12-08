# -*- coding: utf-8 -*-

import json
import os

import pytest
from fixtures import Base
from fixtures import Blog
from fixtures import Post
from fixtures import Tag
from fixtures import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


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
