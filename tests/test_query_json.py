from sqlalchemy import func

from rqlalchemy import select

from .fixtures import User
from .test_query import to_dict


class TestQueryJSON:
    def test_simple_sort(self, session, users):
        res = select(User).rql("sort((raw,balance))").execute(session)
        exp = sorted(users, key=lambda u: u.raw["balance"])
        assert res
        assert res == exp

    def test_simple_sort_desc(self, session, users):
        res = select(User).rql("sort(-(raw,balance))").execute(session)
        exp = sorted(users, key=lambda u: u.raw["balance"], reverse=True)
        assert res
        assert res == exp

    def test_complex_sort(self, session, users):
        res = (
            select(User)
            .rql("sort((raw,balance),(raw,registered),(raw,birthdate))")
            .execute(session)
        )
        exp = sorted(
            users,
            key=lambda u: (u.raw["balance"], u.raw["registered"], u.raw["birthdate"]),
        )
        assert res
        assert res == exp

    def test_in_operator(self, session, users):
        res = select(User).rql("in((raw,state),(FL,TX))").execute(session)
        exp = [u for u in users if u.raw["state"] in ("FL", "TX")]
        assert res
        assert res == exp

    def test_out_operator(self, session, users):
        res = select(User).rql("out((raw,state),(FL,TX))").execute(session)
        exp = [u for u in users if u.raw["state"] not in ("FL", "TX")]
        assert res
        assert res == exp

    def test_contains_string(self, session, users):
        res = select(User).rql("contains((raw,email),besto.com)").execute(session)
        exp = [u for u in users if "besto.com" in u.raw["email"]]
        assert res
        assert res == exp

    def test_excludes_string(self, session, users):
        res = select(User).rql("excludes((raw,email),besto.com)").execute(session)
        exp = [u for u in users if "besto.com" not in u.raw["email"]]
        assert res
        assert res == exp

    def test_contains_array(self, session, users):
        res = select(User).rql("contains((raw,tags),aliqua)").execute(session)
        exp = [u for u in users if "aliqua" in u.raw["tags"]]
        assert res
        assert res == exp

    def test_excludes_array(self, session, users):
        res = select(User).rql("excludes((raw,tags),aliqua)").execute(session)
        exp = [u for u in users if "aliqua" not in u.raw["tags"]]
        assert res
        assert res == exp

    def test_select_1_deep(self, session, users):
        res = select(User).rql("select((raw,guid),(raw,state),(raw,isActive))").execute(session)
        exp = [
            {"guid": u.raw["guid"], "state": u.raw["state"], "isActive": u.raw["isActive"]}
            for u in users
        ]
        assert res
        assert res == exp

    def test_select_2_deep(self, session, users):
        res = select(User).rql("select((misc,preferences,favorite_fruit))").execute(session)
        exp = [{"favorite_fruit": u.misc["preferences"]["favorite_fruit"]} for u in users]
        assert res
        assert res == exp

    def test_values(self, session, users):
        res = select(User).rql("values((raw,state))").execute(session)
        exp = [u.raw["state"] for u in users]
        assert res
        assert res == exp

    def test_filter_by_json_key_1_deep_string(self, session, users):
        res = select(User).rql("eq((misc,eye_color),blue)").execute(session)
        exp = [u for u in users if u.misc["eye_color"] == "blue"]
        assert res
        assert res == exp

    def test_filter_by_json_key_1_deep_bool(self, session, users):
        res = select(User).rql("eq((misc,likes_apples),true)").execute(session)
        exp = [u for u in users if u.misc["likes_apples"] is True]
        assert res
        assert res == exp

    def test_filter_by_json_key_1_deep_integer(self, session, users):
        res = select(User).rql("eq((misc,unread_messages),8)").execute(session)
        exp = [u for u in users if u.misc["unread_messages"] == 8]
        assert res
        assert res == exp

    def test_filter_by_json_key_1_deep_float(self, session, users):
        res = select(User).rql("gt((misc,balance),1000.0)").execute(session)
        exp = [u for u in users if u.misc["balance"] > 1000]
        assert res
        assert res == exp

    def test_filter_by_json_key_2_deep(self, session, users):
        res = select(User).rql("eq((misc,preferences,favorite_fruit),banana)").execute(session)
        exp = [u for u in users if u.misc["preferences"]["favorite_fruit"] == "banana"]
        assert res
        assert res == exp

    def test_filter_by_json_key_3_deep_and_index(self, session, users):
        res = select(User).rql("lt((misc,location,coordinates,1),-18.4)").execute(session)
        exp = [u for u in users if u.misc["location"]["coordinates"][1] < -18.4]
        assert res
        assert res == exp

    def test_aggregate(self, session):
        res = (
            select(User).rql("aggregate((raw,state),sum((misc,unread_messages)))").execute(session)
        )
        exp = to_dict(
            session.execute(
                select(
                    User.raw["state"].label("state"),
                    func.sum(User.misc["unread_messages"].as_integer()).label("sum"),
                ).group_by(User.raw["state"].label("state"))
            ).all()
        )

        assert res
        assert res == exp

    def test_aggregate_count(self, session):
        res = select(User).rql("aggregate((raw,gender),count((raw,user_id)))").execute(session)
        exp = to_dict(
            session.execute(
                select(
                    User.raw["gender"].label("gender"),
                    func.count(User.raw["user_id"]).label("count"),
                ).group_by(User.raw["gender"].label("gender"))
            ).all()
        )

        assert res
        assert res == exp

    def test_aggregate_with_filter(self, session):
        res = (
            select(User)
            .rql("aggregate((raw,state),sum((misc,unread_messages)))&eq((raw,isActive),true)")
            .execute(session)
        )
        exp = to_dict(
            session.execute(
                select(
                    User.raw["state"].label("state"),
                    func.sum(User.misc["unread_messages"].as_integer()).label("sum"),
                )
                .filter(User.raw["isActive"].as_boolean())
                .group_by(User.raw["state"].label("state"))
            ).all()
        )

        assert res
        assert res == exp

    def test_like_with_relationship_1_deep(self, session, users):
        res = select(User).rql("like((raw,name),*Jackson*)").execute(session)
        exp = [u for u in users if "Jackson" in u.raw["name"]]
        assert res
        assert res == exp

    def test_like_with_relationship_2_deep(self, session, users):
        res = select(User).rql("like((misc,preferences,favorite_fruit),*ana*)").execute(session)
        exp = [u for u in users if "ana" in u.misc["preferences"]["favorite_fruit"]]
        assert res
        assert res == exp
