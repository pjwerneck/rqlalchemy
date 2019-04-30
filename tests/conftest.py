# -*- coding: utf-8 -*-

import json
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fixtures import Base
from fixtures import RQLQuery
from fixtures import Tag
from fixtures import User


@pytest.fixture(scope='session')
def engine():
    return create_engine('sqlite:///:memory:', echo=True)


@pytest.yield_fixture(scope='session')
def session(engine):

    Base.metadata.create_all(engine)

    session_ = sessionmaker(bind=engine, query_cls=RQLQuery)

    # load fixtures
    fpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'users.json')

    localsession = session_()
    with open(fpath) as f:
        users = json.load(f)

        for raw in users:
            obj = User(
                user_id=raw['index'],
                guid=raw['guid'],
                name=raw['name'],
                email=raw['email'],
                gender=raw['gender'],
                birthdate=raw['birthdate'],
                registered=raw['registered'],
                is_active=raw['isActive'],
                street_address=raw['street_address'],
                city=raw['city'],
                state=raw['state'],
                tags=raw['tags'],
                balance=raw['balance'],
            )

            localsession.add(obj)

    localsession.commit()

    yield session_()

    Base.metadata.drop_all(engine)
