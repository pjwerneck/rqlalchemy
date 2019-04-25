
import pytest
from sqlalchemy import func
from sqlalchemy import not_

from fixtures import User


class TestQuery:

    def test_simple_sort(self, session):
        res = session.query(User).rql('sort(distance)').rql_all()
        exp = session.query(User).order_by(User.distance).all()
        assert res
        assert res == exp

    def test_simple_sort_desc(self, session):
        res = session.query(User).rql('sort(-distance)').rql_all()
        exp = session.query(User).order_by(User.distance.desc()).all()
        assert res
        assert res == exp

    def test_complex_sort(self, session):
        res = session.query(User).rql('sort(distance,last_seen,birthdate)').rql_all()
        exp = session.query(User).order_by(User.distance, User.last_seen, User.birthdate).all()
        assert res
        assert res == exp

    def test_in_operator(self, session):
        res = session.query(User).rql('in(state,(FL,TX))').rql_all()
        exp = session.query(User).filter(User.state.in_(['FL', 'TX'])).all()
        assert res
        assert res == exp

    def test_out_operator(self, session):
        res = session.query(User).rql('out(state,(FL,TX))').rql_all()
        exp = session.query(User).filter(not_(User.state.in_(['FL', 'TX']))).all()
        assert res
        assert res == exp

    def test_contains(self, session):
        res = session.query(User).rql('contains(email,wired.com)').rql_all()
        exp = session.query(User).filter(User.email.contains('wired.com')).all()
        assert res
        assert res == exp

    def test_excludes(self, session):
        res = session.query(User).rql('excludes(email,wired.com)').rql_all()
        exp = session.query(User).filter(not_(User.email.contains('wired.com'))).all()
        assert res
        assert res == exp

    def test_limit(self, session):
        res = session.query(User).rql('limit(2)').rql_all()
        exp = session.query(User).limit(2).all()
        assert res
        assert res == exp

    def test_select(self, session):
        rql_res = session.query(User).rql('select(user_id,state)').rql_all()
        res = [row._asdict() for row in session.query(User.user_id, User.state)]
        assert res
        assert rql_res == res

    def test_values(self, session):
        res = session.query(User).rql('values(state)').rql_all()
        exp = [v[0] for v in session.query(User.state)]
        assert res
        assert res == exp

    def test_sum(self, session):
        res = session.query(User).rql('sum(distance)').rql_all()
        exp = [session.query(func.sum(User.distance)).scalar()]
        assert len(res) == 1
        assert res == exp

    def test_mean(self, session):
        res = session.query(User).rql('mean(distance)').rql_all()
        exp = session.query(func.avg(User.distance)).scalar()
        assert res == exp

    def test_max(self, session):
        res = session.query(User).rql('max(distance)').rql_all()
        exp = session.query(func.max(User.distance)).scalar()
        assert res == exp

    def test_min(self, session):
        res = session.query(User).rql('min(distance)').rql_all()
        exp = session.query(func.min(User.distance)).scalar()
        assert res == exp

    def test_first(self, session):
        res = session.query(User).rql('first()').rql_all()
        exp = [session.query(User).first()]

        assert len(res) == 1
        assert res == exp

    def test_one(self, session):
        pass

    def test_count(self, session):
        res = session.query(User).rql('count()').rql_all()
        exp = session.query(User).count()
        assert res == exp

    def test_distinct(self, session):
        pass

    @pytest.mark.parametrize('user_id', (1, 2, 3))
    def test_eq_operator(self, session, user_id):
        res = session.query(User).rql('user_id={}'.format(user_id)).rql_all()
        assert res
        assert session.query(User).get(user_id).username == res[0].username

    @pytest.mark.parametrize('distance', (10, 20, 30))
    def test_lt_operator(self, session, distance):
        res = session.query(User).rql('lt(distance,{})'.format(distance))
        assert res
        assert all([u.distance < distance for u in res])
