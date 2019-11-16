# RQLAlchemy

[![Build Status](https://travis-ci.org/pjwerneck/rqlalchemy.svg?branch=develop)](https://travis-ci.org/pjwerneck/rqlalchemy)

Resource Query Language extension for SQLAlchemy

## Overview

Resource Query Language (RQL) is a query language designed for use in URIs, with object-style data structures.

rqlalchemy is an RQL extension for SQLAlchemy. It easily allows exposing SQLAlchemy tables or models as an HTTP API endpoint and performing complex queries using only querystring parameters.

## Installing

```
pip install rqlalchemy
```

## Usage

RQL queries can be supported by an application using SQLAlchemy by adding the `rqlalchemy.RQLQueryMixIn` class as a mix-in class to your base `Query` class:

```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Query as BaseQuery

from rqlalchemy import RQLQueryMixIn

# create the declarative base
Base = declarative_base()

# create the custom query class
class RQLQuery(BaseQuery, RQLQueryMixIn):
    _rql_default_limit = 10
    _rql_max_limit = 100

# assign the custom query class to the declarative base
Base.query_class = RQLQuery
```

With that in place, you can perform RQL queries by passing the querystring to the query `rql()` method. For example, if you have a Flask HTTP API with an users collection endpoint querying your `User` model:

```python
from urllib.parse import unquote

from flask import request

@app.route('/users')
def get_users_collection():
    qs = unquote(request.query_string.decode(request.charset))
    query = session.query(User).rql(qs)
    users = query.rql_all()

    return render_response(users)
```

### Aggregates

As with the base SQLAlchemy Query class, you can retrieve results with the `all()` method, or by iterating over the query, however, if you want to support RQL expressions with aggregate functions or querying functions that result in a subset of columns, you must retrieve the results with `rql_all()`.

### Pagination

RQLAlchemy offers limit/offset pagination with the `rql_paginate()` method, which returns the requested page, the RQL expressions for previous and next pages if available, and the total number of items.

```python
from urllib.parse import unquote

from flask import request

@app.route('/users')
def get_users_collection():
    qs = unquote(request.query_string.decode(request.charset))
    query = session.query(User).rql(qs)
    page, previous_page, next_page, total = query.rql_paginate()

    response = {"data": page,
                "total": total,
               }

    if previous_page:
        response["previous"] = '/users?' + previous_page

    if next_page:
        response["next"] = '/users?' + next_page

    return render_response(response)
```

Keep in mind that pagination requires a limit, either a `_rql_default_limit` value, a querystring `limit(x)`, or the `limit` parameter to the `rql()` method. Calling `rql_paginate()` without a limit will raise `RQLQueryError`.


## Reference Table

| RQL                     | SQLAlchemy                                         | Obs.                                                                                                                            |
|-------------------------|----------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| QUERYING                |                                                    |                                                                                                                                 |
| select(a,b,c,...)       | .query(Model.a, Model.b, Model.c,...)              |                                                                                                                                 |
| values(a)               | [o.a for o in query.from_self(a)]                  |                                                                                                                                 |
| limit(count,start?)     | .limit(count).offset(start)                        |                                                                                                                                 |
| sort(attr1)             | .order_by(attr)                                    |                                                                                                                                 |
| sort(-attr1)            | .order_by(attr.desc())                             |                                                                                                                                 |
| distinct()              | .distinct()                                        |                                                                                                                                 |
| first()                 | .limit(1)                                          |                                                                                                                                 |
| one()                   | [query.one()]                                      |                                                                                                                                 |
| FILTERING               |                                                    |                                                                                                                                 |
| eq(attr,value)          | .filter(Model.attr == value)                       |                                                                                                                                 |
| ne(attr,value)          | .filter(Model.attr != value)                       |                                                                                                                                 |
| lt(attr,value)          | .filter(Model.attr < value)                        |                                                                                                                                 |
| le(attr,value)          | .filter(Model.attr <= value)                       |                                                                                                                                 |
| gt(attr,value)          | .filter(Model.attr > value)                        |                                                                                                                                 |
| ge(attr,value)          | .filter(Model.attr >= value)                       |                                                                                                                                 |
| in(attr,value)          | .filter(Model.attr.in_(value)                      |                                                                                                                                 |
| out(attr,value)         | .filter(not_(Model.attr.in_(value)))               |                                                                                                                                 |
| contains(attr,value)    | .filter(Model.contains(value))                     | Produces a LIKE expression when filtering against a string, or an IN expression when filtering against an iterable relationship |
| excludes(attr,value)    | .filter(not_(Model.contains(value)))               | See above.                                                                                                                      |
| and(expr1,expr2,...)    | .filter(and_(expr1, expr2, ...))                   |                                                                                                                                 |
| or(expr1,expr2,...)     | .filter(or_(expr1, expr2, ...))                    |                                                                                                                                 |
| AGGREGATING             |                                                    | All aggregation functions return scalar results.                                                                                |
| aggregate(a,b\(c\),...) | .query(Model.a, func.b(Model.c)).group_by(Model.a) |                                                                                                                                 |
| sum(attr)               | .query(func.sum(Model.attr))                       |                                                                                                                                 |
| mean(attr)              | .query(func.avg(Model.attr))                       |                                                                                                                                 |
| max(attr)               | .query(func.max(Model.attr))                       |                                                                                                                                 |
| min(attr)               | .query(func.min(Model.attr))                       |                                                                                                                                 |
| count()                 | .query(func.count())                               |                                                                                                                                 |
