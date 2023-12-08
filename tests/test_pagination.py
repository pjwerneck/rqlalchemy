import pytest
from fixtures import User

from rqlalchemy import RQLSelectError
from rqlalchemy.query import select


class TestPagination:
    def test_pagination_no_limit_raises_error(self, session):
        with pytest.raises(RQLSelectError):
            select(User).rql("").rql_paginate(session)

    def test_pagination_no_filter(self, session):
        res = select(User).rql("limit(10)").rql_paginate(session)

        assert res.previous_page is None
        assert res.next_page == "limit(10,10)"
        assert res.total == 1000

        exp = session.scalars(select(User).limit(10)).all()
        assert res.page
        assert res.page == exp

    def test_pagination_with_filter(self, session):
        res = select(User).rql("and(in(state,(FL,TX)),limit(10))").rql_paginate(session)

        assert res.previous_page is None
        assert res.next_page == "and(in(state,(FL,TX)),limit(10,10))"
        assert res.total == 34

        exp = session.scalars(select(User).filter(User.state.in_(("FL", "TX"))).limit(10)).all()
        assert res.page
        assert res.page == exp

    def test_pagination_with_filter_and_order(self, session):
        res = select(User).rql("and(in(state,(FL,TX)),limit(10),sort(name))").rql_paginate(session)

        assert res.previous_page is None
        assert res.next_page == "and(in(state,(FL,TX)),limit(10,10),sort(name))"
        assert res.total == 34

        exp = session.scalars(select(User).filter(User.state.in_(("FL", "TX"))).order_by(User.name).limit(10)).all()
        assert res.page
        assert res.page == exp

    def test_pagination_with_filter_and_order_all_pages(self, session):
        next_page = "and(in(state,(FL,TX)),limit(10),sort(name))"
        query = select(User).filter(User.state.in_(("FL", "TX"))).order_by(User.name)

        # page 1
        res = select(User).rql(next_page).rql_paginate(session)

        assert res.previous_page is None
        assert res.next_page == "and(in(state,(FL,TX)),limit(10,10),sort(name))"
        assert res.total == 34

        exp = session.scalars(query.limit(10)).all()
        assert len(res.page) == 10
        assert res.page == exp

        # page 2
        res = select(User).rql(res.next_page).rql_paginate(session)

        assert res.previous_page == "and(in(state,(FL,TX)),limit(10,0),sort(name))"
        assert res.next_page == "and(in(state,(FL,TX)),limit(10,20),sort(name))"
        assert res.total == 34

        exp = session.scalars(query.limit(10).offset(10)).all()
        assert len(res.page) == 10
        assert res.page == exp

        # page 3
        res = select(User).rql(res.next_page).rql_paginate(session)

        assert res.previous_page == "and(in(state,(FL,TX)),limit(10,10),sort(name))"
        assert res.next_page == "and(in(state,(FL,TX)),limit(10,30),sort(name))"
        assert res.total == 34

        exp = session.scalars(query.limit(10).offset(20)).all()
        assert len(res.page) == 10
        assert res.page == exp

        # page 4
        res = select(User).rql(res.next_page).rql_paginate(session)

        assert res.previous_page == "and(in(state,(FL,TX)),limit(10,20),sort(name))"
        assert res.next_page is None
        assert res.total == 34

        exp = session.scalars(query.limit(10).offset(30)).all()
        assert len(res.page) == 4
        assert res.page == exp
