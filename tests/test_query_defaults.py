# -*- coding: utf-8 -*-

from unittest.mock import patch

from rqlalchemy.query import select

from .fixtures import User


class TestQueryDefaults:
    @patch("rqlalchemy.RQLSelect._rql_default_limit", 10)
    def test_default_limit(self, session):
        res = session.scalars(select(User).rql("")).all()
        assert len(res) == 10

    @patch("rqlalchemy.RQLSelect._rql_max_limit", 100)
    def test_max_limit(self, session):
        res = session.scalars(select(User).rql("limit(110)")).all()
        assert len(res) == 100

    def test_escaped_querystring(self, session):
        res = session.scalars(select(User).rql("email=mavischerry%40nspire.com")).all()
        exp = session.scalars(select(User).filter(User.email == "mavischerry@nspire.com")).all()
        assert res
        assert res == exp
