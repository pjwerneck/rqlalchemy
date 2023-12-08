# -*- coding: utf-8 -*-

import datetime
import operator
from copy import deepcopy
from functools import reduce
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Sequence
from typing import Union

from pyrql import RQLSyntaxError
from pyrql import parse
from pyrql import unparse
from sqlalchemy import ColumnElement
from sqlalchemy import Row
from sqlalchemy import RowMapping
from sqlalchemy import Select
from sqlalchemy import func
from sqlalchemy import sql
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session
from sqlalchemy.orm import decl_api
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import _typing
from sqlalchemy.sql import elements

ArgsType = List[Any]
BinaryOperator = Callable[[Any, Any], Any]


class PaginatedResults(NamedTuple):
    page: Any
    total: int
    previous_page: Optional[str] = None
    next_page: Optional[str] = None


class RQLSelectError(Exception):
    pass


class RQLSelect(Select):
    inherit_cache = True
    _rql_error_cls = RQLSelectError

    _rql_max_limit = None
    _rql_default_limit = None
    _rql_auto_scalar = False

    def __init__(self, *entities: _typing._ColumnsClauseArgument[Any]):
        super().__init__(*entities)
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
        self._rql_aliased_models = {}

    @property
    def _rql_select_entities(self) -> List[decl_api.DeclarativeMeta]:
        return [t._annotations["parententity"].entity for t in self._raw_columns]

    @property
    def _rql_select_limit(self):
        return self._limit_clause.value if self._limit_clause is not None else None

    @property
    def _rql_select_offset(self):
        return self._offset_clause.value if self._offset_clause is not None else None

    def rql(self, query: str = "", limit: Optional[int] = None) -> "RQLSelect":
        if len(self._rql_select_entities) > 1:
            raise NotImplementedError("Select must have only one entity")

        if not query:
            self.rql_parsed = None
        else:
            self.rql_expression = query

            try:
                self.rql_parsed: Dict[str, Any] = parse(query)
            except RQLSyntaxError as e:
                raise self._rql_error_cls(f"RQL Syntax error: {e.args}") from e

        self._rql_walk(self.rql_parsed)

        select_ = self

        for other in self._rql_joins:
            select_ = select_.outerjoin(other)

        if self._rql_where_clause is not None:
            select_ = select_.filter(self._rql_where_clause)

        if self._rql_order_by_clause is not None:
            select_ = select_.order_by(*self._rql_order_by_clause)

        if self._rql_default_limit is not None:
            select_ = select_.limit(self._rql_default_limit)

        if limit is not None:
            select_ = select_.limit(limit)

        if self._rql_limit_clause is not None:
            select_ = select_.limit(self._rql_limit_clause)

        if self._rql_offset_clause is not None:
            select_ = select_.offset(self._rql_offset_clause)

        if self._rql_distinct_clause is not None:
            select_ = select_.distinct()

        return select_

    def execute(self, session: Session) -> Sequence[Union[Union[Row, RowMapping], Any]]:
        """
        Executes the sql expression differently based on which clauses included:
        - For single aggregates a scalar is returned
        - In case the one clause is included only a single row is returned
        - In case a select clause is included only the requisite fields are returned
        - Otherwise scalars are returned
        """
        if self._rql_scalar_clause is not None:
            if self._rql_scalar_clause.__class__.__name__ == "count":
                return session.scalar(select(self._rql_scalar_clause).select_from(self.subquery()))
            return session.scalar(self.with_only_columns(self._rql_scalar_clause))

        if self._rql_one_clause is not None:
            try:
                return [session.scalars(self).one()]
            except NoResultFound as e:
                raise RQLSelectError("No result found for one()") from e
            except MultipleResultsFound as e:
                raise RQLSelectError("Multiple results found for one()") from e

        if self._rql_values_clause is not None:
            query = self.with_only_columns(self._rql_values_clause)
            if self._rql_distinct_clause is not None:
                query = query.distinct()

            return [row[0] for row in session.execute(query)]

        if self._rql_select_clause:
            query = self.with_only_columns(*self._rql_select_clause)

            if self._rql_group_by_clause:
                query = query.group_by(*self._rql_group_by_clause)

            if self._rql_distinct_clause is not None:
                query = query.distinct()

            return [row._asdict() for row in session.execute(query)]

        return session.scalars(self).all()

    def rql_paginate(self, session: Session) -> PaginatedResults:
        """
        Convenience function for pagination. Returns:
        - the page given to the rql query
        - the count by setting the limit, offset and order by to None
        - next and last page rql queries if more records are available for pagination
        """

        limit = self._rql_select_limit
        offset = self._rql_select_offset or 0

        if limit is None:
            raise RQLSelectError("Pagination requires a limit value")

        page = self.execute(session)

        total_query = self.limit(None).offset(None).order_by(None)
        total_query_count = sql.select(func.count()).select_from(total_query.subquery())
        total = session.scalar(total_query_count)

        if offset + limit < total:
            expr = self.rql_expr_replace({"name": "limit", "args": [limit, offset + limit]})
            next_page = expr
        else:
            next_page = None

        if offset > 0 and total:
            expr = self.rql_expr_replace({"name": "limit", "args": [limit, offset - limit]})
            previous_page = expr
        else:
            previous_page = None

        return PaginatedResults(
            page=page, total=total, previous_page=previous_page, next_page=next_page
        )

    def rql_expr_replace(self, replacement: Dict[str, Any]) -> str:
        """Replace any nodes matching the replacement name

        This can be used to generate an expression with modified
        `limit` and `offset` nodes, for pagination purposes.

        """
        parsed = deepcopy(self.rql_parsed)

        replaced = self._rql_traverse_and_replace(parsed, replacement["name"], replacement["args"])

        if not replaced:
            parsed = {"name": "and", "args": [replacement, parsed]}

        return unparse(parsed)

    def _rql_traverse_and_replace(self, root: Dict[str, Any], name: str, args: ArgsType) -> bool:
        if root is None:
            return False

        if root["name"] == name:
            root["args"] = args
            return True

        else:
            for arg in root["args"]:
                if isinstance(arg, dict) and self._rql_traverse_and_replace(arg, name, args):
                    return True

        return False

    def _rql_walk(self, node: Dict[str, Any]) -> None:
        if node:
            self._rql_where_clause = self._rql_apply(node)

    def _rql_apply(self, node: Dict[str, Any]) -> Any:
        if isinstance(node, dict):
            name = node["name"]
            args = node["args"]

            if name in {"eq", "ne", "lt", "le", "gt", "ge"}:
                return self._rql_compare(args, getattr(operator, name))

            try:
                method = getattr(self, f"_rql_{name}")
            except AttributeError as e:
                raise self._rql_error_cls(f"Invalid query function: {name}") from e

            return method(args)

        elif isinstance(node, (list, tuple)):
            raise NotImplementedError

        return node

    def _rql_attr(self, attr):
        model = self._rql_select_entities[0]

        if isinstance(attr, str):
            try:
                return getattr(model, attr)
            except AttributeError as e:
                raise self._rql_error_cls(f"Invalid query attribute: {attr}") from e

        elif isinstance(attr, tuple):
            # Every entry in attr but the last should be a relationship name.
            for name in attr[:-1]:
                if name not in inspect(model).relationships:
                    raise AttributeError(f'{model} has no relationship "{name}"')

                relation = getattr(model, name)
                self._rql_joins.append(relation)
                model = relation.mapper.class_
            return getattr(model, attr[-1])
        raise NotImplementedError

    def _rql_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            value = self._rql_apply(value)

        return value

    def _rql_compare(self, args: ArgsType, op: BinaryOperator) -> elements.BinaryExpression:
        attr, value = args
        attr = self._rql_attr(attr=attr)
        value = self._rql_value(value)

        return op(attr, value)

    def _rql_and(self, args: ArgsType) -> Optional[elements.BooleanClauseList]:
        args = [self._rql_apply(node) for node in args]
        if args := [a for a in args if a is not None]:
            return reduce(sql.and_, args)

    def _rql_or(self, args: ArgsType) -> Optional[elements.BooleanClauseList]:
        args = [self._rql_apply(node) for node in args]
        if args := [a for a in args if a is not None]:
            return reduce(sql.or_, args)

    def _rql_in(self, args: ArgsType) -> elements.BinaryExpression:
        attr, value = args
        attr = self._rql_attr(attr=attr)
        value = self._rql_value([str(v) for v in value])

        return attr.in_(value)

    def _rql_out(self, args: ArgsType) -> elements.BinaryExpression:
        attr, value = args
        attr = self._rql_attr(attr=attr)
        value = self._rql_value([str(v) for v in value])

        return sql.not_(attr.in_(value))

    def _rql_like(self, args: ArgsType) -> elements.BinaryExpression:
        attr, value = args
        attr = self._rql_attr(attr=attr)
        value = self._rql_value(value)
        value = value.replace("*", "%")

        return attr.like(value)

    def _rql_limit(self, args: ArgsType) -> None:
        args = [self._rql_value(v) for v in args]

        self._rql_limit_clause = min(args[0], self._rql_max_limit or float("inf"))

        if len(args) == 2:
            self._rql_offset_clause = args[1]

    def _rql_sort(self, args: ArgsType) -> None:
        args = [("+", v) if isinstance(v, str) else v for v in args]
        args = [(p, self._rql_attr(attr=v)) for (p, v) in args]
        attrs = [attr.desc() if p == "-" else attr for (p, attr) in args]

        self._rql_order_by_clause = attrs

    def _rql_contains(self, args: ArgsType) -> ColumnElement[bool]:
        attr, value = args
        attr = self._rql_attr(attr=attr)
        value = self._rql_value(value)

        return attr.contains(value)

    def _rql_excludes(self, args: ArgsType) -> ColumnElement[bool]:
        attr, value = args
        attr = self._rql_attr(attr=attr)
        value = self._rql_value(value)

        return sql.not_(attr.contains(value))

    def _rql_select(self, args: ArgsType) -> None:
        attrs = [self._rql_attr(attr) for attr in args]

        self._rql_select_clause = attrs

    def _rql_values(self, args: ArgsType) -> None:
        (attr,) = args
        attr = self._rql_attr(attr)

        self._rql_values_clause = attr

    def _rql_distinct(self, *_) -> None:
        self._rql_distinct_clause = True

    def _rql_sum(self, args: ArgsType) -> None:
        (attr,) = args
        attr = self._rql_attr(attr=attr)
        self._rql_scalar_clause = func.sum(attr)

    def _rql_mean(self, args: ArgsType) -> None:
        (attr,) = args
        attr = self._rql_attr(attr=attr)

        self._rql_scalar_clause = func.avg(attr)

    def _rql_max(self, args: ArgsType) -> None:
        (attr,) = args
        attr = self._rql_attr(attr=attr)

        self._rql_scalar_clause = func.max(attr)

    def _rql_min(self, args: ArgsType) -> None:
        (attr,) = args
        attr = self._rql_attr(attr=attr)

        self._rql_scalar_clause = func.min(attr)

    def _rql_count(self, *_) -> None:
        self._rql_scalar_clause = func.count()

    def _rql_first(self, *_) -> None:
        self._rql_limit_clause = 1

    def _rql_one(self, *_) -> None:
        self._rql_one_clause = True

    def _rql_time(self, args: ArgsType) -> datetime.time:
        return datetime.time(*args)

    def _rql_date(self, args: ArgsType) -> datetime.date:
        return datetime.date(*args)

    def _rql_dt(self, args: ArgsType) -> datetime.datetime:
        return datetime.datetime(*args)

    def _rql_aggregate(self, args: ArgsType) -> None:
        attributes = []
        aggregations = []

        for argument in args:
            if isinstance(argument, dict):
                aggregate_label = argument["name"]
                aggregate_function = getattr(func, argument["name"])
                aggregate_attribute = self._rql_attr(argument["args"][0])

                aggregations.append(aggregate_function(aggregate_attribute).label(aggregate_label))

            else:
                attributes.append(self._rql_attr(argument))

        self._rql_group_by_clause = attributes
        self._rql_select_clause = attributes + aggregations


def select(*entities: _typing._ColumnsClauseArgument[Any], **__kw: Any) -> RQLSelect:
    if __kw:
        raise _typing._no_kw()
    return RQLSelect(*entities)
