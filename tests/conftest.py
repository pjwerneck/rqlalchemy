# -*- coding: utf-8 -*-

import json
import pytest
import os

from fixtures import User
from fixtures import create_app
from fixtures import db as db_


@pytest.fixture(scope='session')
def app(request):

    app_ = create_app()

    ctx = app_.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)

    return app_


@pytest.fixture(scope='session')
def db(app, request):

    def teardown():
        db_.drop_all()

    db_.app = app
    db_.create_all()

    request.addfinalizer(teardown)

    # load fixtures
    fpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'users.json')

    with open(fpath) as f:
        users = json.load(f)

        for raw in users:
            obj = User(**raw)
            db_.session.add(obj)

        db_.session.commit()

    return db_
