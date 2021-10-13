import logging
import string
import datetime

import flask
from flask import Flask

from . import app, helpers, get_db


logger = logging.getLogger(__name__)


#@app.route('/')
#def index():
#    return flask.render_template('index.html')

@app.route('/a/<path:filename>')
def admin_index():
    return flask.send_from_directory(app.config['ADMIN_FRONTEND_FOLDER'], filename)

@app.route('/l/<path:filename>')
def listing_index(filename):
    if filename == "":
        filename = "index.html"
    return flask.send_from_directory(app.config['LISTING_FRONTEND_FOLDER'], filename)


@app.route('/', methods=["GET", "POST"])
def signup():
    conn, cur = get_db()
    cur.execute("SELECT l.id, l.title, l.opens, l.closes FROM listings l WHERE l.opens < current_timestamp AND l.closes >= current_timestamp", )
    listings = [dict(x) for x in cur.fetchall()]

    if len(listings) < 1:
        return flask.render_template('empty.html', url=flask.request.url)

    id = flask.request.args.get("id", None)
    for i, lst in enumerate(listings):
        try:
            listings[i]['selected'] = lst['id'] == int(id)
        except:
            listings[i]['selected'] = False

    if flask.request.method == "POST":
        email = flask.request.form.get("email", "").lower()
        try:
            listing_id = int(flask.request.form.get("listing", None))
        except:
            listing_id = None

        cur.execute("SELECT id, name, email, listing_key, locked, confirmed, signup, last_movement FROM listing_members WHERE listing_id=%s AND LOWER(email)=%s", (listing_id, email))
        row = cur.fetchone() 

        logger.warning(f"Email {email} id {listing_id} {[l['id'] for l in listings]} {row}")
        if row is None or (listing_id not in [l["id"] for l in listings]):
            return flask.render_template('signup.html', listings=listings, url=flask.request.url, error=f"Netfang <{email}> fannst ekki á skrá. Vertu viss um að nota sama netfang og skráð er á D4H.")
        elif row['locked'] is not None \
            or row['confirmed'] is not None \
            or row['last_movement'] is not None \
            or (row['signup'] is not None and (row['signup'] + datetime.timedelta(minutes=10) > datetime.datetime.now())):
            return flask.render_template('signup.html', listings=listings, url=flask.request.url, error=f"Þegar er búið að senda tölvupóst á netfangið <{email}> með upplýsingum um pöntunarsíðu.")
        else:
            res = [l for l in listings if l['id'] == listing_id][0]

            member_key = row['listing_key'] if row['listing_key'] is not None else  helpers.get_random_token()

            txt = flask.render_template("email.signup.txt", 
                closes=res['closes'], name=row['name'], vendor=res['title'], 
                url=f"https://{app.config['HOSTNAME']}/l/?token={member_key}",
            )

            logger.warning(f"Sending signup email to {email}")
            cur.execute("UPDATE listing_members SET listing_key=%s, signup=current_timestamp WHERE id=%s", (member_key, row["id"]))
            helpers.queue_email(row["id"], f"Pöntun frá {res['title']} - Hlekkur í pöntunarsíðu", txt)
            conn.commit()
            return flask.render_template('signup.html', listings=listings, url=flask.request.url, message=f"Þér ætti nú að hafa borist tölvupóstur með hlekk á pöntunarsíðu.")
    else:
        return flask.render_template('signup.html', url=flask.request.url, listings=listings)


# TODO CANCEL ORDER

@app.route('/b/cancel')
def cancel():
    token = flask.request.args.get("token")
    conn, cur = get_db()
    cur.execute("SELECT l.id, l.title, l.opens, l.closes, l.signup_key, lm.id AS listing_member_id, lm.name, lm.email, lm.locked, lm.confirmed, lm.listing_key FROM listings l INNER JOIN listing_members lm ON lm.listing_id = l.id WHERE (lm.confirmation_key = %(ck)s AND lm.confirmation_key IS NOT NULL) OR (lm.listing_key = %(ck)s AND lm.confirmation_key IS NULL AND lm.listing_key IS NOT NULL) AND l.opens < current_timestamp AND l.closes >= current_timestamp", {'ck': token})
    res = cur.fetchone()
    if res is None:
        return flask.render_template('404.html', error='Engin gild pöntun fannst fyrir þennan lykil.'), 404
    elif res['confirmed'] is not None:
        return flask.render_template('404.html', error='Pöntun hefur þegar verið staðfest.'), 403
    elif res['confirmed'] is None:
        partial = bool(flask.request.args.get("partial", 0))

        if partial:
            assert res['locked'] is not None
            cur.execute("UPDATE listing_members SET locked=NULL, confirmation_key=NULL WHERE id=%s", (res['listing_member_id'], ))
            conn.commit()
            return flask.render_template("message.html", 
                heading="Karfa opnuð aftur", 
                alert="success", 
                message="Hætt hefur verið við staðfestingarferli. Nú er karfan aftur opin á sömu slóð og áður.",
                url=f"/l/?token={res['listing_key']}"
            )
        else:
            # empty cart and 
            cur.execute("DELETE FROM cart_items WHERE listing_member_id=%s", (res['listing_member_id'], ))
            cur.execute("UPDATE listing_members SET listing_key=NULL, locked=NULL, confirmation_key=NULL, signup=NULL, last_movement=NULL WHERE id=%s", (res['listing_member_id'], ))
            conn.commit()

            return flask.render_template("message.html", 
                heading="Hætt við pöntun", 
                alert="success", 
                message="Pöntun hefur verið eytt. Ef þér snýst hugur þá má fara aftur á skráningarsíðu pöntunar til að hefja pöntunarferli frá byrjun.",
                url=f"/b/signup?token={res['signup_key']}"
            )


@app.route('/b/confirm')
def confirm():
    token = flask.request.args.get("token")
    conn, cur = get_db()
    cur.execute("SELECT l.id, l.title, l.opens, l.closes, lm.id AS listing_member_id, lm.name, lm.email, lm.locked, lm.confirmed, lm.listing_key FROM listings l INNER JOIN listing_members lm ON lm.listing_id = l.id WHERE lm.confirmation_key = %(ck)s AND l.opens < current_timestamp AND l.closes >= current_timestamp", {'ck': token})
    res = cur.fetchone()
    if res is None:
        return flask.render_template('404.html', error='Engin gild pöntun fannst fyrir þennan lykil.'), 404
    elif res['confirmed'] is not None:
        return flask.redirect(f"/l/?token={res['listing_key']}", code=302)
    else:
        cur.execute("UPDATE listing_members SET confirmed=current_timestamp WHERE listing_key=%(lk)s", {'lk': res['listing_key']})

        cart_items = helpers.get_cart(res['listing_member_id'])
        qty = 0
        total = 0
        for row in cart_items:
            total += row['total_price_isk']
            qty   += row['quantity']

        txt = flask.render_template("email.receipt.txt", 
            vendor=res['title'], name=res['name'], 
            qty=qty, total=int(round(total)), items=cart_items,
        )

        logger.warning(f"Sending receipt email to {res['email']}")
        helpers.queue_email(res['listing_member_id'], f"Pöntun staðfest - kvittun", txt)
        conn.commit()
        return flask.redirect(f"/l/?token={res['listing_key']}", code=302)



