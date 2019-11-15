# RQLAlchemy

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
    pass

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
    query = session.query(User).rql(query_string, limit=10)
    users = query.all()

    return render_response(users)
```


## Reference Table

| RQL                  | SQLAlchemy                                   | Obs.                                                                                                                            |
|----------------------|----------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| QUERYING             |                                              |                                                                                                                                 |
| select(a,b,c,...)    | session.query(Model.a, Model.b, Model.c,...) |                                                                                                                                 |
| values(a)            | NOT IMPLEMENTED                              |                                                                                                                                 |
| limit(count,start?)  | .limit(count).offset(start)                  |                                                                                                                                 |
| sort(attr1)          | .order_by(attr)                              |                                                                                                                                 |
| sort(-attr1)         | .order_by(attr.desc())                       |                                                                                                                                 |
| distinct()           | NOT IMPLEMENTED                              |                                                                                                                                 |
| first()              | .limit(1)                                    |                                                                                                                                 |
| one()                | NOT IMPLEMENTED                              |                                                                                                                                 |
| FILTERING            |                                              |                                                                                                                                 |
| eq(attr,value)       | .filter(Model.attr == value)                 |                                                                                                                                 |
| ne(attr,value)       | .filter(Model.attr != value)                 |                                                                                                                                 |
| lt(attr,value)       | .filter(Model.attr < value)                  |                                                                                                                                 |
| le(attr,value)       | .filter(Model.attr <= value)                 |                                                                                                                                 |
| gt(attr,value)       | .filter(Model.attr > value)                  |                                                                                                                                 |
| ge(attr,value)       | .filter(Model.attr >= value)                 |                                                                                                                                 |
| in(attr,value)       | .filter(Model.attr.in_(value)                |                                                                                                                                 |
| out(attr,value)      | .filter(not_(Model.attr.in_(value)))         |                                                                                                                                 |
| contains(attr,value) | .filter(Model.contains(value))               | Produces a LIKE expression when filtering against a string, or an IN expression when filtering against an iterable relationship |
| excludes(attr,value) | .filter(not_(Model.contains(value)))         | See above.                                                                                                                      |
| and(expr1,expr2,...) | .filter(and_(expr1, expr2, ...))             |                                                                                                                                 |
| or(expr1,expr2,...)  | .filter(or_(expr1, expr2, ...))              |                                                                                                                                 |
| rel(attr,expr)       | NOT IMPLEMENTED                              |                                                                                                                                 |
| AGGREGATING          |                                              | All aggregate functions return scalar results.                                                                                  |
| aggregate(...)       | NOT IMPLEMENTED                              |                                                                                                                                 |
| sum(attr)            | .query(func.sum(Model.attr))                 |                                                                                                                                 |
| mean(attr)           | .query(func.avg(Model.attr))                 |                                                                                                                                 |
| max(attr)            | .query(func.max(Model.attr))                 |                                                                                                                                 |
| min(attr)            | .query(func.min(Model.attr))                 |                                                                                                                                 |
| count()              | .query(func.count())                         |                                                                                                                                 |
