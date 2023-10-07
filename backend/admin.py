import logging
import flask

from . import app, helpers, get_db

logger = logging.getLogger(__name__)

@app.route('/admin')
@helpers.authenticate_admin
def admin_index_():
    conn, cur = get_db()
    cur.execute("SELECT l.id, l.title, l.opens, l.closes, l.currency, l.exchange_rate FROM listings l ORDER BY l.id DESC")
    listings = cur.fetchall()

    return flask.render_template('admin/index.html', listings=listings, token=flask.request.args.get("token", None))

@app.route('/admin/listing/<int:id>')
@helpers.authenticate_admin
def admin_listing(id: int): # ->
    conn, cur = get_db()
    cur.execute("SELECT l.id, l.title, l.opens, l.closes, l.currency, l.exchange_rate FROM listings l WHERE l.id=%s", (id, ))
    listing = cur.fetchall()[0]

    return flask.render_template('admin/listing.html', listing=listing, token=flask.request.args.get("token", None))

@app.route('/admin/listing/<int:id>/customers')
@helpers.authenticate_admin
def admin_listing_customers(id: int): # ->
    pass

@app.route('/admin/listing/<int:id>/order')
@helpers.authenticate_admin
def admin_listing_order(id: int): # ->
    pass

@app.route('/admin/listing/<int:id>/shipments')
@helpers.authenticate_admin
def admin_listing_shipments(id: int): # ->
    pass

@app.route('/admin/listing/<int:id>/settlement')
@helpers.authenticate_admin
def admin_listing_settlement(id: int): # ->
    pass
