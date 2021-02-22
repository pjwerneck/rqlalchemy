# -*- coding: utf-8 -*-

import datetime
import operator
from copy import deepcopy
from functools import reduce

from pyrql import RQLSyntaxError
from pyrql import parse
from pyrql import unparse
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import not_
from sqlalchemy import or_
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


class RQLQueryError(Exception):
    pass


class RQLQueryMixIn:
    """Query mix-in class with RQL functions

    """

    _rql_error_cls = RQLQueryError

    _rql_max_limit = None
    _rql_default_limit = None
    _rql_auto_scalar = False

    def rql(self, query, limit=None):
        if len(self._entities) > 1:
            raise NotImplementedError("Query must have a single entity")

        expr = query

        if not expr:
            self.rql_parsed = None
            self.rql_expr = ""

        else:
            self.rql_expr = expr

            try:
                self.rql_parsed = parse(expr)
            except RQLSyntaxError as exc:
                raise self._rql_error_cls("RQL Syntax error: %r" % (exc.args,))

        self._rql_select_clause = []
        self._rql_values_clause = None
        self._rql_scalar_clause = None
        self._rql_where_clause = None
        self._rql_order_by_clause = None
        self._rql_limit_clause = None
        self._rql_offset_clause = None
        self._rql_one_clause = None
        self._rql_distinct_clause = None
        self._rql_group_by_clause = None
        self._rql_joins = []

        self._rql_walk(self.rql_parsed)

        query = self

        for other in self._rql_joins:
            query = query.join(other)

        if self._rql_where_clause is not None:
            query = query.filter(self._rql_where_clause)

        if self._rql_order_by_clause is not None:
            query = query.order_by(*self._rql_order_by_clause)

        # limit priority is: default, method parameter, querystring parameter
        if self._rql_default_limit:
            query = query.limit(self._rql_default_limit)

        if limit is not None:
            query = query.limit(limit)

        if self._rql_limit_clause is not None:
            query = query.limit(self._rql_limit_clause)

        if self._rql_offset_clause is not None:
            query = query.offset(self._rql_offset_clause)

        if self._rql_distinct_clause is not None:
            query = query.distinct()

        return query

    def rql_expr_replace(self, replacement):
        """Replace any nodes matching the replacement name

        This can be used to generate an expression with modified
        `limit` and `offset` nodes, for pagination purposes.

        """
        parsed = deepcopy(self.rql_parsed)

        replaced = self._rql_traverse_and_replace(
            parsed, replacement["name"], replacement["args"]
        )

        if not replaced:
            parsed = {"name": "and", "args": [replacement, parsed]}

        return unparse(parsed)

    def _rql_traverse_and_replace(self, root, name, args):
        if root is None:
            return False

        if root["name"] == name:
            root["args"] = args
            return True

        else:
            for arg in root["args"]:
                if isinstance(arg, dict):
                    if self._rql_traverse_and_replace(arg, name, args):
                        return True

        return False

    def _rql_walk(self, node):
        # filtering nodes will be used by the where clause. Other
        # nodes will be saved separately by the visitor methods below
        if node:
            self._rql_where_clause = self._rql_apply(node)

    def _rql_apply(self, node):
        if isinstance(node, dict):
            name = node["name"]
            args = node["args"]

            if name in {"eq", "ne", "lt", "le", "gt", "ge"}:
                return self._rql_cmp(args, getattr(operator, name))

            try:
                method = getattr(self, "_rql_" + name)
            except AttributeError:
                raise self._rql_error_cls("Invalid query function: %s" % name)

            return method(args)

        elif isinstance(node, list):
            raise NotImplementedError

        elif isinstance(node, tuple):
            raise NotImplementedError

        return node

    def _rql_attr(self, attr):
        model = self._entities[0].type
        if isinstance(attr, str):
            try:
                return getattr(model, attr)
            except AttributeError:
                raise self._rql_error_cls("Invalid query attribute: %s" % attr)

        elif isinstance(attr, tuple) and len(attr) == 2:
            relationships = inspect(model).relationships.keys()

            if attr[0] in relationships:
                rel = getattr(model, attr[0])
                submodel = rel.mapper.class_

                column = getattr(submodel, attr[1])
                self._rql_joins.append(rel)

                return column

        raise NotImplementedError

    def _rql_value(self, value, attr=None):
        if isinstance(value, dict):
            value = self._rql_apply(value)

        return value

    def _rql_cmp(self, args, op):
        attr, value = args

        attr = self._rql_attr(attr)
        value = self._rql_value(value, attr)

        return op(attr, value)

    def _rql_and(self, args):
        args = [self._rql_apply(node) for node in args]
        args = [a for a in args if a is not None]
        if args:
            return reduce(and_, args)

    def _rql_or(self, args):
        args = [self._rql_apply(node) for node in args]
        args = [a for a in args if a is not None]
        if args:
            return reduce(or_, args)

    def _rql_in(self, args):
        attr, value = args

        attr = self._rql_attr(attr)
        value = self._rql_value(value, attr)

        return attr.in_(value)

    def _rql_out(self, args):
        attr, value = args

        attr = self._rql_attr(attr)
        value = self._rql_value(value, attr)

        return not_(attr.in_(value))

    def _rql_like(self, args):
        attr, value = args

        attr = self._rql_attr(attr)
        value = self._rql_value(value, attr)
        value = value.replace("*", "%")

        return attr.like(value)

    def _rql_limit(self, args):
        args = [self._rql_value(v) for v in args]

        self._rql_limit_clause = min(args[0], self._rql_max_limit or float("inf"))

        if len(args) == 2:
            self._rql_offset_clause = args[1]

    def _rql_sort(self, args):
        # normalize sort args with '+'
        args = [("+", v) if isinstance(v, str) else v for v in args]
        # pair signals with attributes
        args = [(p, self._rql_attr(v)) for (p, v) in args]

        attrs = [attr.desc() if p == "-" else attr for (p, attr) in args]

        self._rql_order_by_clause = attrs

    def _rql_contains(self, args):
        attr, value = args
        attr = self._rql_attr(attr)
        value = self._rql_value(value, attr)

        return attr.contains(value)

    def _rql_excludes(self, args):
        attr, value = args
        attr = self._rql_attr(attr)
        value = self._rql_value(value, attr)

        return not_(attr.contains(value))

    def _rql_select(self, args):
        attrs = [self._rql_attr(attr) for attr in args]
        self._rql_select_clause = attrs

    def _rql_values(self, args):
        (attr,) = args
        attr = self._rql_attr(attr)
        self._rql_values_clause = attr

    def _rql_distinct(self, args):
        self._rql_distinct_clause = True

    def _rql_sum(self, args):
        (attr,) = args
        attr = self._rql_attr(attr)
        self._rql_values_clause = func.sum(attr)

    def _rql_mean(self, args):
        (attr,) = args
        attr = self._rql_attr(attr)
        self._rql_scalar_clause = func.avg(attr)

    def _rql_max(self, args):
        (attr,) = args
        attr = self._rql_attr(attr)
        self._rql_scalar_clause = func.max(attr)

    def _rql_min(self, args):
        (attr,) = args
        attr = self._rql_attr(attr)
        self._rql_scalar_clause = func.min(attr)

    def _rql_count(self, args):
        self._rql_scalar_clause = func.count()

    def _rql_first(self, args):
        self._rql_limit_clause = 1

    def _rql_one(self, args):
        self._rql_one_clause = True

    def _rql_time(self, args):
        return datetime.time(*args)

    def _rql_date(self, args):
        return datetime.date(*args)

    def _rql_dt(self, args):
        return datetime.datetime(*args)

    def _rql_aggregate(self, args):
        attrs = []
        aggrs = []

        for x in args:
            if isinstance(x, dict):
                agg_label = x["name"]
                agg_func = getattr(func, x["name"])
                agg_attr = self._rql_attr(x["args"][0])

                aggrs.append(agg_func(agg_attr).label(agg_label))

            else:
                attrs.append(self._rql_attr(x))

        self._rql_group_by_clause = attrs
        self._rql_select_clause = attrs + aggrs

    def rql_all(self):

        if self._rql_scalar_clause is not None:
            return self.from_self(self._rql_scalar_clause).scalar()

        if self._rql_one_clause is not None:
            try:
                return [self.one()]
            except NoResultFound:
                raise RQLQueryError("No result found for one()")
            except MultipleResultsFound:
                raise RQLQueryError("Multiple results found for one()")

        if self._rql_values_clause is not None:
            query = self.from_self(self._rql_values_clause)
            if self._rql_distinct_clause is not None:
                query = query.distinct()

            return [row[0] for row in query]

        if self._rql_select_clause:
            query = self.from_self(*self._rql_select_clause)

            if self._rql_group_by_clause:
                query = query.group_by(*self._rql_group_by_clause)

            if self._rql_distinct_clause is not None:
                query = query.distinct()

            return [row._asdict() for row in query]

        return self.all()

    def rql_paginate(self):
        limit = self._limit
        offset = self._offset or 0
        total = 0

        if limit is None:
            raise RQLQueryError("Pagination requires a limit value")

        # build a bare query copy to calculate totals
        _total_query = self.limit(None).offset(None).order_by(None)
        # then replace the select clause with count(*) and get the first value
        total = self.session.execute(
            _total_query.statement.with_only_columns([func.count()])
        ).scalar()

        page = self.rql_all()

        if offset + limit < total:
            expr = self.rql_expr_replace(
                {"name": "limit", "args": [limit, offset + limit]}
            )
            next_page = expr
        else:
            next_page = None

        if offset > 0 and total:
            expr = self.rql_expr_replace(
                {"name": "limit", "args": [limit, offset - limit]}
            )
            previous_page = expr
        else:
            previous_page = None

        return page, previous_page, next_page, total
