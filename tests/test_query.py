from statistics import mean

import pytest
from sqlalchemy import func

from rqlalchemy import RQLSelectError
from rqlalchemy import select

from .fixtures import User


def to_dict(it):
    return [row._asdict() for row in it]


class TestQuery:
    def test_simple_sort(self, session, users):
        res = select(User).rql("sort(balance)").execute(session)
        exp = sorted(users, key=lambda u: u.balance)
        assert res
        assert res == exp

    def test_simple_sort_desc(self, session, users):
        res = select(User).rql("sort(-balance)").execute(session)
        exp = sorted(users, key=lambda u: u.balance, reverse=True)
        assert res
        assert res == exp

    def test_complex_sort(self, session, users):
        res = select(User).rql("sort(balance,registered,birthdate)").execute(session)
        exp = sorted(users, key=lambda u: (u.balance, u.registered, u.birthdate))
        assert res
        assert res == exp

    def test_in_operator(self, session, users):
        res = select(User).rql("in(state,(FL,TX))").execute(session)
        exp = [u for u in users if u.state in ("FL", "TX")]
        assert res
        assert res == exp

    def test_out_operator(self, session, users):
        res = select(User).rql("out(state,(FL,TX))").execute(session)
        exp = [u for u in users if u.state not in ("FL", "TX")]
        assert res
        assert res == exp

    def test_contains_string(self, session, users):
        res = select(User).rql("contains(email,besto.com)").execute(session)
        exp = [u for u in users if "besto.com" in u.email]
        assert res
        assert res == exp

    def test_excludes_string(self, session, users):
        res = select(User).rql("excludes(email,besto.com)").execute(session)
        exp = [u for u in users if "besto.com" not in u.email]
        assert res
        assert res == exp

    def test_contains_array(self, session, users):
        res = select(User).rql("contains(tags,aliqua)").execute(session)
        exp = [u for u in users if "aliqua" in u.tags]
        assert res
        assert res == exp

    def test_excludes_array(self, session, users):
        res = select(User).rql("excludes(tags,aliqua)").execute(session)
        exp = [u for u in users if "aliqua" not in u.tags]
        assert res
        assert res == exp

    def test_limit(self, session, users):
        res = select(User).rql("limit(2)").execute(session)
        exp = [u for u in users][:2]
        assert res
        assert res == exp

    def test_select(self, session, users):
        rql_res = select(User).rql("select(user_id,state)").execute(session)
        res = [{"user_id": u.user_id, "state": u.state} for u in users]
        assert res
        assert rql_res == res

    def test_values(self, session, users):
        res = select(User).rql("values(state)").execute(session)
        exp = [u.state for u in users]
        assert res
        assert res == exp

    def test_sum(self, session, users):
        res = select(User).rql("sum(balance)").execute(session)
        exp = sum([u.balance for u in users])
        assert res == exp

    def test_mean(self, session, users):
        res = select(User).rql("mean(balance)").execute(session)
        # SQLAlchemy average is cast to float instead of Decimal?
        exp = mean([float(u.balance) for u in users])
        # python 3.12 uses a more precise sum algorithm which affects the float
        # mean, so use pytest.approx to account for that.
        assert res == pytest.approx(exp)

    def test_max(self, session, users):
        res = select(User).rql("max(balance)").execute(session)
        exp = max([u.balance for u in users])
        assert res == exp

    def test_min(self, session, users):
        res = select(User).rql("min(balance)").execute(session)
        exp = min([u.balance for u in users])
        assert res == exp

    def test_first(self, session, users):
        res = select(User).rql("first()").execute(session)
        exp = [users[0]]

        assert len(res) == 1
        assert res == exp

    def test_one(self, session, users):
        guid = "658c407c-6c19-470e-9aa6-8c2b86cddb4b"
        res = select(User).rql(f"guid={guid}&one()").execute(session)
        exp = [u for u in users if u.guid == guid]

        assert len(res) == 1
        assert res == exp

    def test_one_no_results_found(self, session, users):
        with pytest.raises(RQLSelectError) as exc:
            select(User).rql("guid=lero&one()").execute(session)
        assert exc.value.args[0] == "No result found for one()"

    def test_one_multiple_results_found(self, session, users):
        with pytest.raises(RQLSelectError) as exc:
            select(User).rql("state=FL&one()").execute(session)
        assert exc.value.args[0] == "Multiple results found for one()"

    def test_distinct(self, session, users):
        res = select(User).rql("select(gender)&distinct()").execute(session)
        exp = [{"gender": gender} for gender in {u.gender for u in users}]

        assert len(res) == 2
        assert res == exp or res == exp[::-1]

    def test_count(self, session, users):
        res = select(User).rql("count()").execute(session)
        exp = len(users)
        assert res == exp

    @pytest.mark.parametrize("user_id", (1, 2, 3))
    def test_eq_operator(self, session, user_id, users):
        res = select(User).rql("user_id={}".format(user_id)).execute(session)
        exp = [u for u in users if u.user_id == user_id]
        assert res
        assert res == exp

    @pytest.mark.parametrize("balance", (1000, 2000, 3000))
    def test_gt_operator(self, session, balance, users):
        res = select(User).rql("gt(balance,{})".format(balance)).execute(session)
        exp = [u for u in users if u.balance > balance]
        assert res
        assert res == exp

    def test_aggregate(self, session):
        res = select(User).rql("aggregate(state,sum(balance))").execute(session)
        exp = to_dict(
            session.execute(
                select(User.state, func.sum(User.balance).label("sum")).group_by(User.state)
            ).all()
        )

        assert res
        assert res == exp

    def test_aggregate_count(self, session):
        res = select(User).rql("aggregate(gender,count(user_id))").execute(session)
        exp = to_dict(
            session.execute(
                select(User.gender, func.count(User.user_id).label("count")).group_by(User.gender)
            ).all()
        )

        assert res
        assert res == exp

    def test_aggregate_with_filter(self, session):
        res = select(User).rql("aggregate(state,sum(balance))&is_active=true").execute(session)
        exp = to_dict(
            session.execute(
                select(User.state, func.sum(User.balance).label("sum"))
                .filter(User.is_active.is_(True))
                .group_by(User.state)
            ).all()
        )

        assert res
        assert res == exp

    def test_like_with_relationship_1_deep(self, session, blogs, users):
        res = select(User).rql("like((blogs, title), *1*)").execute(session)
        exp = [b.user for b in blogs if "1" in b.title]
        assert res == exp

    def test_like_with_relationship_2_deep(self, session, posts):
        res = select(User).rql("like((blogs, posts, title), *Post 1*)").execute(session)
        exp = [p.blog.user for p in posts if "Post 1" in p.title]
        assert res == exp
