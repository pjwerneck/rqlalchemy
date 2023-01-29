import pytest
from fixtures import User

from rqlalchemy import RQLQueryError


class TestPagination:
    def test_pagination_no_limit_raises_error(self, session):
        with pytest.raises(RQLQueryError):
            session.query(User).rql("").rql_paginate()

    def test_pagination_no_filter(self, session):
        res = session.query(User).rql("limit(10)").rql_paginate()
        page, previous_page, next_page, total = res

        assert previous_page is None
        assert next_page == "limit(10,10)"
        assert total == 1000

        exp = session.query(User).limit(10).all()
        assert page
        assert page == exp

    def test_pagination_with_filter(self, session):
        res = session.query(User).rql("and(in(state,(FL,TX)),limit(10))").rql_paginate()
        page, previous_page, next_page, total = res

        assert previous_page is None
        assert next_page == "and(in(state,(FL,TX)),limit(10,10))"
        assert total == 34

        exp = session.query(User).filter(User.state.in_(("FL", "TX"))).limit(10).all()
        assert page
        assert page == exp

    def test_pagination_with_filter_and_order(self, session):
        res = session.query(User).rql("and(in(state,(FL,TX)),limit(10),sort(name))").rql_paginate()
        page, previous_page, next_page, total = res

        assert previous_page is None
        assert next_page == "and(in(state,(FL,TX)),limit(10,10),sort(name))"
        assert total == 34

        exp = session.query(User).filter(User.state.in_(("FL", "TX"))).order_by(User.name).limit(10).all()
        assert page
        assert page == exp

    def test_pagination_with_filter_and_order_all_pages(self, session):
        next_page = "and(in(state,(FL,TX)),limit(10),sort(name))"
        query = session.query(User).filter(User.state.in_(("FL", "TX"))).order_by(User.name)

        # page 1
        res = session.query(User).rql(next_page).rql_paginate()
        page, previous_page, next_page, total = res

        assert previous_page is None
        assert next_page == "and(in(state,(FL,TX)),limit(10,10),sort(name))"
        assert total == 34

        exp = query.limit(10).all()
        assert len(page) == 10
        assert page == exp

        # page 2
        res = session.query(User).rql(next_page).rql_paginate()
        page, previous_page, next_page, total = res

        assert previous_page == "and(in(state,(FL,TX)),limit(10,0),sort(name))"
        assert next_page == "and(in(state,(FL,TX)),limit(10,20),sort(name))"
        assert total == 34

        exp = query.limit(10).offset(10).all()
        assert len(page) == 10
        assert page == exp

        # page 3
        res = session.query(User).rql(next_page).rql_paginate()
        page, previous_page, next_page, total = res

        assert previous_page == "and(in(state,(FL,TX)),limit(10,10),sort(name))"
        assert next_page == "and(in(state,(FL,TX)),limit(10,30),sort(name))"
        assert total == 34

        exp = query.limit(10).offset(20).all()
        assert len(page) == 10
        assert page == exp

        # page 4
        res = session.query(User).rql(next_page).rql_paginate()
        page, previous_page, next_page, total = res

        assert previous_page == "and(in(state,(FL,TX)),limit(10,20),sort(name))"
        assert next_page is None
        assert total == 34

        exp = query.limit(10).offset(30).all()
        assert len(page) == 4
        assert page == exp
