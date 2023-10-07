import string
import logging
import random
import functools
import pickle

import flask

from . import app, helpers, get_db


logger = logging.getLogger(__name__)


def get_listing(listing_key):
    conn, cur = get_db()
    cur.execute("SELECT l.id, l.title, l.opens, l.closes, lm.id AS listing_member_id, lm.name, lm.email, lm.locked, lm.confirmed, lm.listing_key FROM listings l INNER JOIN listing_members lm ON lm.listing_id = l.id WHERE lm.listing_key = %(lkey)s AND l.opens < current_timestamp AND l.closes >= current_timestamp AND lm.listing_key IS NOT NULL", {'lkey': listing_key})
    res = cur.fetchone()
    if res is None:
        return None
    else:
        cur.execute("UPDATE listing_members SET last_movement = current_timestamp WHERE id = %(id)s", {'id': res['listing_member_id']})
        conn.commit() 
        return dict(res)

def get_cart(listing_member_id):
    conn, cur = get_db()
    cur.execute("""
        SELECT 
            i.id, 
            i.item_name, 
            i.vendor_id, 
            i.vendor_url, 
            i.vendor_url || '?number=' || i.vendor_id AS url,
            i.price, 
            l.currency, 
            i.price*l.exchange_rate as price_isk, 
            ci.quantity,
            i.price*l.exchange_rate*ci.quantity as total_price_isk, 
            ARRAY(SELECT row_to_json(t) FROM (SELECT it.original, it.adjusted, it.value FROM item_properties it WHERE it.item_id=i.id) AS t) AS properties 
        FROM items i 
            INNER JOIN listings l ON l.id = i.listing_id 
            INNER JOIN cart_items ci ON ci.item_id = i.id
        WHERE ci.listing_member_id = %(lm)s ORDER BY i.item_name""", { 'lm': listing_member_id, })
    return [dict(x) for x in cur.fetchall()]

def authenticate_listing(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        try:
            listing_key = flask.request.headers.get('Authorization', "").split(" ")[1].strip()
        except IndexError as e:
            return "", 403
            
        listing = get_listing(listing_key)
        if listing is None:
            return "", 403
        else:
            return f(listing, *args, **kwargs)
    return inner

def authenticate_admin(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        try:
            admin_key = flask.request.headers.get('Authorization', "").split(" ")[1].strip()
        except IndexError:
            admin_key = flask.request.args.get("token", None)

        if admin_key == app.config['ADMIN_PASSWORD']:
            return f(*args, **kwargs)
        else:
            return "", 403

    return inner

def get_random_token():
    choices = string.ascii_letters + string.digits
    return "".join(random.choice(choices) for i in range(20))

def queue_email(member_id, subject, content):
    conn, cur = get_db()
    cur.execute("INSERT INTO emails (listing_member_id, scheduled, subject, body) VALUES (%s, current_timestamp, %s, %s) RETURNING id", (member_id, subject, content))
    conn.commit()
    id = cur.fetchone()["id"]


