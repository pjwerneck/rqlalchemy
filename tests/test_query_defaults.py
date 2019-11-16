# -*- coding: utf-8 -*-

from unittest.mock import patch

from fixtures import User


class TestQueryDefaults:
    @patch("fixtures.RQLQuery._rql_default_limit", 10)
    def test_default_limit(self, session):
        res = session.query(User).rql("").all()
        assert len(res) == 10

    @patch("fixtures.RQLQuery._rql_max_limit", 100)
    def test_max_limit(self, session):
        res = session.query(User).rql("limit(110)").all()
        assert len(res) == 100

    def test_escaped_querystring(self, session):
        res = session.query(User).rql("email=mavischerry%40nspire.com").all()
        exp = session.query(User).filter(User.email == "mavischerry@nspire.com").all()
        assert res
        assert res == exp
