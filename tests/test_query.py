
from operator import attrgetter

import pytest

from fixtures import User


class TestQuery:

    def test_simple_sort(self, session):
        res = session.query(User).rql('sort(distance)').all()
        assert res
        assert res == sorted(res, key=attrgetter('distance'))

    def test_simple_sort_desc(self, session):
        res = session.query(User).rql('sort(-distance)').all()
        assert res
        assert res == sorted(res, key=attrgetter('distance'), reverse=True)

    def test_complex_sort(self, session):
        res = session.query(User).rql('sort(distance,last_seen,birthdate)').all()
        assert res
        assert res == sorted(res, key=attrgetter('distance', 'last_seen', 'birthdate'))

    def test_in_operator(self, session):
        res = session.query(User).rql('in(state,(FL,TX))').all()
        assert res
        assert {u.state for u in res} == {'TX', 'FL'}

    def test_out_operator(self, session):
        res = session.query(User).rql('out(state,(FL,TX))')
        assert res
        assert {u.state for u in res}.isdisjoint({'TX', 'FL'})

    def test_contains(self, session):
        pass

    def test_excludes(self, session):
        pass

    def test_limit(self, session):
        pass

    @pytest.mark.parametrize('user_id', (1, 2, 3))
    def test_eq_operator(self, session, user_id):
        res = session.query(User).rql('user_id={}'.format(user_id)).all()
        assert res
        assert session.query(User).get(user_id).username == res[0].username

    @pytest.mark.parametrize('distance', (10, 20, 30))
    def test_lt_operator(self, session, distance):
        res = session.query(User).rql('lt(distance,{})'.format(distance))
        assert res
        assert all([u.distance < distance for u in res])
