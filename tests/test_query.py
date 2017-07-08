# -*- coding: utf-8 -*-

import pytest

from fixtures import User
from operator import itemgetter


class TestQuery:

    def test_simple_sort(self, client, db):
        rep = client.get('/users?sort(distance)')
        assert rep.json == sorted(rep.json, key=itemgetter('distance'))

    def test_simple_sort_desc(self, client, db):
        rep = client.get('/users?sort(-distance)')
        assert rep.json == sorted(rep.json, key=itemgetter('distance'), reverse=True)

    def test_complex_sort(self, client, db):
        rep = client.get('/users?sort(distance,last_seen,birthdate)')
        assert rep.json == sorted(rep.json, key=itemgetter('distance', 'last_seen', 'birthdate'))

    def test_in_operator(self, client, db):
        rep = client.get('/users?in(state,(FL,TX))')
        assert {u['state'] for u in rep.json} == {'TX', 'FL'}

    def test_out_operator(self, client, db):
        rep = client.get('/users?out(state,(FL,TX))')
        assert rep.json
        assert {u['state'] for u in rep.json}.isdisjoint({'TX', 'FL'})

    def test_contains(self, client, db):
        pass

    def test_excludes(self, client, db):
        pass

    def test_limit(self, client, db):
        pass

    @pytest.mark.parametrize('user_id', (1, 2, 3))
    def test_eq_operator(self, client, db, user_id):
        rep = client.get('/users?user_id={}'.format(user_id))

        assert User.query.get(user_id).username == rep.json[0]['username']

    @pytest.mark.parametrize('distance', (10, 20, 30))
    def test_lt_operator(self, client, db, distance):
        rep = client.get('/users?lt(distance,{})'.format(distance))

        assert all([u['distance'] < distance for u in rep.json])
