# -*- coding: utf-8 -*-

import json
import os

import pytest

from fixtures import Base
from fixtures import RQLQuery
from fixtures import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope='session')
def engine():
    return create_engine('sqlite:///:memory:', echo=False)


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
            obj = User(**raw)
            localsession.add(obj)

    localsession.commit()

    yield session_()

    Base.metadata.drop_all(engine)
