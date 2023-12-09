# RQLAlchemy

[![Build Status](https://github.com/pjwerneck/rqlalchemy/actions/workflows/pytest.yml/badge.svg?branch=develop)](https://github.com/pjwerneck/rqlalchemy/actions/workflows/pytest.yml)

## Resource Query Language extension for SQLAlchemy

**Overview**

Resource Query Language (RQL) is a query language designed for use in URIs, with object-style data structures.

`rqlalchemy` is an RQL extension for SQLAlchemy, making it easy to expose SQLAlchemy tables or models as an HTTP API endpoint and perform complex queries using only query string parameters.

**Installing**

```bash
pip install rqlalchemy
```

**Usage**

Support RQL queries in your application by using the `select()` construct provided by RQLAlchemy. After creating the selectable, use the `rql()` method to apply the RQL query string, and then use the `execute()` method with the session to retrieve the results.

For example, in a Flask HTTP API with a users collection endpoint querying the `User` model:

```python
from urllib.parse import unquote
from flask import request

from rqlalchemy import select

@app.route('/users')
def get_users_collection():
    qs = unquote(request.query_string.decode(request.charset))
    users = select(User).rql(qs).execute(session)

    return render_response(users)
```

The `.execute()` method handles the session and adjusts the results accordingly, returning scalars, lists of dicts, or a single scalar result when appropriate. There's no need to use `session.execute()` or `session.scalars()` directly unless you want to handle the results yourself.

**Pagination**

RQLAlchemy offers limit/offset pagination with the `rql_paginate()` method, returning the requested page, RQL expressions for previous and next pages if available, and the total number of items.

```python
from urllib.parse import unquote
from flask import request

from rqlalchemy import select

@app.route('/users')
def get_users_collection():
    qs = unquote(request.query_string.decode(request.charset))
    res = select(User).rql(qs).rql_paginate(session)

    response = {
        "data": res.page,
        "total": res.total,
    }

    if res.previous_page:
        response["previous"] = '/users?' + res.previous_page

    if res.next_page:
        response["next"] = '/users?' + res.next_page

    return render_response(response)
```

Pagination requires a limit, as a `RQLSelect._rql_default_limit` value, a query string `limit(x)`, or the `limit` parameter to the `rql()` method. Calling `rql_paginate()` without a limit will raise `RQLQueryError`.

**Reference Table**

| RQL                     | SQLAlchemy equivalent                              | Observation                                                                                                                     |
|-------------------------|----------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| QUERYING                |                                                    |                                                                                                                                 |
| select(a,b,c,...)       | select(Model.a, Model.b, Model.c,...)              |                                                                                                                                 |
| values(a)               | [o.a for o in query.from_self(a)]                  |                                                                                                                                 |
| limit(count,start?)     | .limit(count).offset(start)                        |                                                                                                                                 |
| sort(attr1)             | .order_by(attr)                                    |                                                                                                                                 |
| sort(-attr1)            | .order_by(attr.desc())                             |                                                                                                                                 |
| distinct()              | .distinct()                                        |                                                                                                                                 |
| first()                 | .limit(1)                                          |                                                                                                                                 |
| one()                   | [query.one()]                                      |                                                                                                                                 |
| FILTERING               |                                                    |                                                                                                                                 |
| eq(attr,value)          | .where(Model.attr == value)                        |                                                                                                                                 |
| ne(attr,value)          | .where(Model.attr != value)                        |                                                                                                                                 |
| lt(attr,value)          | .where(Model.attr < value)                         |                                                                                                                                 |
| le(attr,value)          | .where(Model.attr <= value)                        |                                                                                                                                 |
| gt(attr,value)          | .where(Model.attr > value)                         |                                                                                                                                 |
| ge(attr,value)          | .where(Model.attr >= value)                        |                                                                                                                                 |
| in(attr,value)          | .where(Model.attr.in_(value)                       |                                                                                                                                 |
| out(attr,value)         | .where(not_(Model.attr.in_(value)))                |                                                                                                                                 |
| contains(attr,value)    | .where(Model.contains(value))                      | Produces a LIKE expression when querying against a string, or an IN expression when querying against an iterable relationship   |
| excludes(attr,value)    | .where(not_(Model.contains(value)))                | See above.                                                                                                                      |
| and(expr1,expr2,...)    | .where(and_(expr1, expr2, ...))                    |                                                                                                                                 |
| or(expr1,expr2,...)     | .where(or_(expr1, expr2, ...))                     |                                                                                                                                 |
| AGGREGATING             |                                                    | All aggregation functions return scalar results.                                                                                |
| aggregate(a,b\(c\),...) | select(Model.a, func.b(Model.c)).group_by(Model.a) |                                                                                                                                 |
| sum(attr)               | select(func.sum(Model.attr))                       |                                                                                                                                 |
| mean(attr)              | select(func.avg(Model.attr))                       |                                                                                                                                 |
| max(attr)               | select(func.max(Model.attr))                       |                                                                                                                                 |
| min(attr)               | select(func.min(Model.attr))                       |                                                                                                                                 |
| count()                 | select(func.count())                               |                                                                                                                                 |

