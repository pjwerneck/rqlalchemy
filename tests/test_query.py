import pytest
from fixtures import Blog
from fixtures import Post
from fixtures import User
from sqlalchemy import func
from sqlalchemy import not_

from rqlalchemy import RQLSelectError
from rqlalchemy.query import select


def to_dict(it):
    return [row._asdict() for row in it]


class TestQuery:
    def test_simple_sort(self, session):
        res = select(User).rql("sort(balance)").rql_all(session)
        exp = session.scalars(select(User).order_by(User.balance)).all()
        assert res
        assert res == exp

    def test_simple_sort_desc(self, session):
        res = select(User).rql("sort(-balance)").rql_all(session)
        exp = session.scalars(select(User).order_by(User.balance.desc())).all()
        assert res
        assert res == exp

    def test_complex_sort(self, session):
        res = select(User).rql("sort(balance,registered,birthdate)").rql_all(session)
        exp = session.scalars(select(User).order_by(User.balance, User.registered, User.birthdate)).all()
        assert res
        assert res == exp

    def test_in_operator(self, session):
        res = select(User).rql("in(state,(FL,TX))").rql_all(session)
        exp = session.scalars(select(User).filter(User.state.in_(["FL", "TX"]))).all()
        assert res
        assert res == exp

    def test_out_operator(self, session):
        res = select(User).rql("out(state,(FL,TX))").rql_all(session)
        exp = session.scalars(select(User).filter(not_(User.state.in_(["FL", "TX"])))).all()
        assert res
        assert res == exp

    def test_contains_string(self, session):
        res = select(User).rql("contains(email,besto.com)").rql_all(session)
        exp = session.scalars(select(User).filter(User.email.contains("besto.com"))).all()
        assert res
        assert res == exp

    def test_excludes_string(self, session):
        res = select(User).rql("excludes(email,besto.com)").rql_all(session)
        exp = session.scalars(select(User).filter(not_(User.email.contains("besto.com")))).all()
        assert res
        assert res == exp

    def test_contains_array(self, session):
        res = select(User).rql("contains(tags,aliqua)").rql_all(session)
        exp = session.scalars(select(User).filter(User.tags.contains("aliqua"))).all()
        assert res
        assert res == exp

    def test_excludes_array(self, session):
        res = select(User).rql("excludes(tags,aliqua)").rql_all(session)
        exp = session.scalars(select(User).filter(not_(User.tags.contains("aliqua")))).all()
        assert res
        assert res == exp

    def test_limit(self, session):
        res = select(User).rql("limit(2)").rql_all(session)
        exp = session.scalars(select(User).limit(2)).all()
        assert res
        assert res == exp

    def test_select(self, session):
        rql_res = select(User).rql("select(user_id,state)").rql_all(session)
        res = to_dict(session.execute(select(User.user_id, User.state)))
        assert res
        assert rql_res == res

    def test_values(self, session):
        res = select(User).rql("values(state)").rql_all(session)
        exp = [v[0] for v in session.execute(select(User.state))]
        assert res
        assert res == exp

    def test_sum(self, session):
        res = select(User).rql("sum(balance)").rql_all(session)
        exp = session.scalar(select(func.sum(User.balance)))
        assert res == exp

    def test_mean(self, session):
        res = select(User).rql("mean(balance)").rql_all(session)
        exp = session.scalar(select(func.avg(User.balance)))
        assert res == exp

    def test_max(self, session):
        res = select(User).rql("max(balance)").rql_all(session)
        exp = session.scalar(select(func.max(User.balance)))
        assert res == exp

    def test_min(self, session):
        res = select(User).rql("min(balance)").rql_all(session)
        exp = session.scalar(select(func.min(User.balance)))
        assert res == exp

    def test_first(self, session):
        res = select(User).rql("first()").rql_all(session)
        exp = [session.scalars(select(User)).first()]

        assert len(res) == 1
        assert res == exp

    def test_one(self, session):
        res = select(User).rql("guid=658c407c-6c19-470e-9aa6-8c2b86cddb4b&one()").rql_all(session)
        exp = [session.scalars(select(User).filter(User.guid == "658c407c-6c19-470e-9aa6-8c2b86cddb4b")).one()]

        assert len(res) == 1
        assert res == exp

    def test_one_no_results_found(self, session):
        with pytest.raises(RQLSelectError) as exc:
            select(User).rql("guid=lero&one()").rql_all(session)
        assert exc.value.args[0] == "No result found for one()"

    def test_one_multiple_results_found(self, session):
        with pytest.raises(RQLSelectError) as exc:
            select(User).rql("state=FL&one()").rql_all(session)
        assert exc.value.args[0] == "Multiple results found for one()"

    def test_distinct(self, session):
        res = select(User).rql("select(gender)&distinct()").rql_all(session)
        exp = to_dict(session.execute(select(User.gender).distinct()))

        assert len(res) == 2
        assert res == exp

    def test_count(self, session):
        res = select(User).rql("count()").rql_all(session)
        exp = session.scalar(select(func.count()).select_from(User))
        assert res == exp

    @pytest.mark.parametrize("user_id", (1, 2, 3))
    def test_eq_operator(self, session, user_id):
        res = select(User).rql("user_id={}".format(user_id)).rql_all(session)
        assert res
        assert session.scalar(select(User).filter_by(user_id=user_id)).name == res[0].name

    @pytest.mark.parametrize("balance", (1000, 2000, 3000))
    def test_gt_operator(self, session, balance):
        res = select(User).rql("gt(balance,{})".format(balance)).rql_all(session)
        assert res
        assert all([u.balance > balance for u in res])

    def test_aggregate(self, session):
        res = select(User).rql("aggregate(state,sum(balance))").rql_all(session)
        exp = to_dict(session.execute(select(User.state, func.sum(User.balance).label("sum")).group_by(User.state)).all())

        assert res
        assert res == exp

    def test_aggregate_count(self, session):
        res = select(User).rql("aggregate(gender,count(user_id))").rql_all(session)
        exp = to_dict(session.execute(select(User.gender, func.count(User.user_id).label("count")).group_by(User.gender)).all())

        assert res
        assert res == exp

    def test_aggregate_with_filter(self, session):
        res = select(User).rql("aggregate(state,sum(balance))&is_active=true").rql_all(session)
        exp = to_dict(session.execute(
            select(User.state, func.sum(User.balance).label("sum"))
            .filter(User.is_active == True)
            .group_by(User.state))
            .all()
        )

        assert res
        assert res == exp

    def test_like_with_relationship_1_deep(self, session, blogs):
        res = select(User).rql("like((blogs, title), *1*)").rql_all(session)
        exp = session.scalars(select(User).join(Blog).filter(Blog.title.like("%1%"))).all()
        assert res == exp

    def test_like_with_relationship_2_deep(self, session, posts):
        res = select(User).rql("like((blogs, posts, title), *Post 1*)").rql_all(session)
        exp = session.scalars(select(User).join(Blog).join(Post).filter(Post.title.like("%Post 1%"))).all()
        assert res == exp
