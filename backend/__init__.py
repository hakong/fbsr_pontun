import logging
import datetime

from flask import Flask, g, request
from flask_json import FlaskJSON, JsonError, json_response, as_json

import psycopg2
import psycopg2.extras
import psycopg2.pool


logger = logging.getLogger(__name__)

app = Flask(__name__)
json = FlaskJSON(app)

app.config.from_object('backend.config')

app.config['pgpool'] = psycopg2.pool.SimpleConnectionPool(1, 20, **app.config['DATABASE'])


@app.template_filter()
def isk(value):
    value = round(float(value))
    return "{:,.0f} kr.".format(value).replace(",",".")

#class CustomJSONEncoder(JSONEncoder):
#    def default(self, obj):
#        try:
#            if isinstance(obj, datetime.datetime):
#                return obj.isoformat()
#            iterable = iter(obj)
#        except TypeError:
#            pass
#        else:
#            return list(iterable)
#        return JSONEncoder.default(self, obj)

#app.json_encoder = CustomJSONEncoder

def get_db():
    if 'db' not in g:
        g.db = app.config['pgpool'].getconn()
    return g.db, g.db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

#conn = psycopg2.connect(app.config['DATABASE'])
#cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

@app.teardown_appcontext
def close_conn(e):
    db = g.pop('db', None)
    if db is not None:
        app.config['pgpool'].putconn(db)

from . import views
from . import admin
from . import api
