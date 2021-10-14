import logging
import flask

from . import app, helpers, get_db

logger = logging.getLogger(__name__)


@app.route('/api/cart/lock', methods=['PUT', ])
@helpers.authenticate_listing
def lock_cart(listing):
    if listing['locked'] is not None:
        return flask.render_template("404.html", error="Pöntun er þegar læst."), 403
    if listing['confirmed'] is not None:
        return flask.render_template("404.html", error="Pöntun er þegar staðfest."), 403

    cart_items = helpers.get_cart(listing['listing_member_id'])
    token = helpers.get_random_token()

    qty = 0
    total = 0
    for row in cart_items:
        total += row['total_price_isk']
        qty   += row['quantity']
    
    txt = flask.render_template("email.confirm.txt",
        name=listing['name'], vendor=listing['title'], 
        qty=qty, total=int(round(total)), items=cart_items,
        confirm_url=f"https://{app.config['HOSTNAME']}/b/confirm?token={token}",
        cancel_url=f"https://{app.config['HOSTNAME']}/b/cancel?token={token}&partial=1",
    )

    logger.warning(f"Sending confirmation email to {listing['email']}")
    helpers.queue_email(listing["listing_member_id"], f"Næstu skref staðfestingar á pöntun frá {listing['title']}", txt)

    conn, cur = get_db()
    cur.execute("UPDATE listing_members SET locked=current_timestamp, confirmation_key=%(ck)s WHERE listing_key=%(lk)s", {'lk': listing['listing_key'], 'ck': token})
    conn.commit()

    return dict(
        listing={
            'id':        listing['id'], 
            'title':     listing['title'], 
            'opens':     listing['opens'], 
            'closes':    listing['closes'], 
            'locked':    listing['locked'],
            'confirmed': listing['confirmed']
        }, member={
            'name':  listing['name'],
            'email': listing['email'],
        }, cart=cart_items)


@app.route('/api/cart', methods=['POST', 'DELETE'])
@helpers.authenticate_listing
def update_cart(listing):
    if listing['confirmed'] is not None or listing['locked'] is not None:
        return "", 403
    
    conn, cur = get_db()
    cart = helpers.get_cart(listing['listing_member_id'])
    if flask.request.method == "POST":
        body = flask.request.json
        if body.get('action') == 'update':
            matching_qty = [x['quantity'] for x in cart if x['id'] == body['id']][0]
            if int(body.get('quantity')) == 0:
                cur.execute("DELETE FROM cart_items WHERE listing_member_id=%(lm)s AND item_id=%(item)s", {
                    'lm': listing['listing_member_id'],
                    'item': body.get('id')
                })
                conn.commit()
            else:
                cur.execute("UPDATE cart_items SET quantity=%(qty)s WHERE listing_member_id=%(lm)s AND item_id=%(item)s", {
                    'qty': int(body.get('quantity')), 
                    'lm': listing['listing_member_id'],
                    'item': body.get('id')
                })
                conn.commit() 
        elif body.get('action') == 'add':
            try:
                existing_qty = [x['quantity'] for x in cart if x['id'] == body['id']][0]
                cur.execute("UPDATE cart_items SET quantity=%(qty)s WHERE listing_member_id=%(lm)s AND item_id=%(item)s", {
                    'qty': existing_qty + int(body.get('quantity')), 
                    'lm': listing['listing_member_id'],
                    'item': body.get('id')
                })
                conn.commit()
            except IndexError:
                # ensure that item belongs to this listing
                cur.execute("SELECT id FROM items WHERE listing_id=%(listing)s AND id=%(id)s", {"listing": listing['id'], 'id': body['id']})
                row = cur.fetchone()
                if row is None:
                    return "Item does not belong to listing", 400
                cur.execute("INSERT INTO cart_items (quantity, listing_member_id, item_id) VALUES (%(qty)s, %(lm)s, %(item)s)", {
                    'qty': int(body.get('quantity')), 
                    'lm': listing['listing_member_id'],
                    'item': body.get('id')
                })
                conn.commit()
        elif body.get('action') == 'delete':
            cur.execute("DELETE FROM cart_items WHERE listing_member_id=%(lm)s AND item_id=%(item)s", {
                'lm': listing['listing_member_id'],
                'item': body.get('id')
            })
            conn.commit()
        else:
            return "Invalid action", 404
    elif flask.request.method == "DELETE":
        cur.execute("DELETE FROM cart_items WHERE listing_member_id=%(lm)s", {'lm': listing['listing_member_id']})
        conn.commit()
    else:
        return "Invalid method", 404

    return dict(cart=helpers.get_cart(listing['listing_member_id'])) 

@app.route('/api/confirm', methods=["PUT", ])
@helpers.authenticate_admin
def admin_confirm():
    member_id = flask.request.json.get('member_id', None)
    conn, cur = get_db()
    cur.execute("""UPDATE listing_members SET confirmed=current_timestamp WHERE id=%s AND id IS NOT NULL""", (member_id, ))
    conn.commit()
    return dict(success=cur.rowcount == 1)

@app.route('/api/unconfirm', methods=["PUT", ])
@helpers.authenticate_admin
def admin_unconfirm():
    member_id = flask.request.json.get('member_id', None)
    conn, cur = get_db()
    cur.execute("""UPDATE listing_members SET confirmed=NULL, locked=NULL, confirmation_key=NULL WHERE id=%s AND id IS NOT NULL""", (member_id, ))
    conn.commit()
    return dict(success=cur.rowcount == 1)

@app.route('/api/clear', methods=["PUT", ])
@helpers.authenticate_admin
def admin_clear():
    member_id = flask.request.json.get('member_id', None)
    conn, cur = get_db()
    cur.execute("""DELETE FROM cart_items WHERE listing_member_id=%s AND listing_member_id IS NOT NULL""", (member_id, ))
    conn.commit()
    return dict(success=cur.rowcount > 0)


def get_member_details(listing_member_id):
    conn, cur = get_db()

    cur.execute("""SELECT * FROM member_details WHERE listing_member_id=%(listing_member_id)s""", {'listing_member_id': listing_member_id})
    return cur.fetchone()


@app.route('/api/listing/<int:listing_id>/payments/email', methods=["GET", "POST", ])
@helpers.authenticate_admin
def payments_email(listing_id):
    conn, cur = get_db()

    samples = [
        ('all_confirmed', 'Allir með staðfesta pöntun', "SELECT lm.id, lm.name, lm.email FROM listing_members lm WHERE lm.confirmed IS NOT NULL AND lm.listing_id = %(listing)s ORDER BY lm.name"),
        ('all_unsettled', 'Allir sem hafa ekki gert upp pöntun', "SELECT lm.id, lm.name, lm.email FROM settlement lm WHERE ROUND(lm.remainder) != 0 AND lm.listing_id = %(listing)s ORDER BY lm.name"),
    ]
    #template_str = flask.render_template("email.payment.txt").strip()
    sample_keys = [x[:2] for x in samples] 
    if flask.request.method == "GET":
        return {'samples': sample_keys}
    else: # POST
        body = flask.request.json
        
        assert 'sample' in body
        sample = body.get("sample")
        cur.execute({x[0]: x for x in samples}[sample][2], {'listing': listing_id})

        candidates = cur.fetchall()
        candidates_ids = [x["id"] for x in candidates]

        subject = body.get("subject", "")
        template_renderfor = int(body.get("template_renderfor", candidates_ids[0]))
        assert template_renderfor in candidates_ids, f"{template_renderfor} not in {candidates_ids}"
        template_str = body.get("template", flask.render_template(f"email.{sample}.txt").strip())
        template_rendered = flask.render_template_string(template_str, **get_member_details(template_renderfor))
        candidates_choice = [int(x) for x in body.get("candidates_choice", candidates_ids) if int(x) in candidates_ids]

        if body.get("send", False):
            assert len(subject) > 0
            for member_id in candidates_choice:
                content = flask.render_template_string(template_str, **get_member_details(member_id))
                helpers.queue_email(member_id, subject, content)
                


        return {
            'sample': sample,
            'samples': sample_keys,
            'candidates': candidates,
            'candidates_choice': candidates_choice,
            'template': template_str,
            'template_rendered': template_rendered,
            'template_renderfor': template_renderfor,
        }


@app.route('/api/listing/<int:listing_id>/payments/<int:payment_id>', methods=["DELETE", ])
@helpers.authenticate_admin
def payments(listing_id, payment_id):
    conn, cur = get_db()
    cur.execute("""SELECT * FROM listings WHERE id=%(id)s""", {'id': listing_id})
    listing = cur.fetchone()

    if listing is None:
        return "", 404

    cur.execute("""DELETE FROM payments WHERE id=%s AND listing_member_id IN (SELECT id FROM listing_members WHERE listing_id = %s)""", (payment_id, listing["id"], ))
    conn.commit()
    return dict(success=cur.rowcount == 1)


@app.route('/api/listing/<int:listing_id>/payments', methods=["GET", "POST", ])
@helpers.authenticate_admin
def listing_payments(listing_id):
    conn, cur = get_db()
    cur.execute("""SELECT * FROM listings WHERE id=%(id)s""", {'id': listing_id})
    listing = cur.fetchone()

    if listing is None:
        return "", 404

    if flask.request.method == "POST":
        cur.execute("""INSERT INTO payments (listing_member_id, time, amount, comment) VALUES (%s, %s, %s, %s); """, (
            flask.request.json.get("member_id"), 
            flask.request.json.get("time"), 
            flask.request.json.get("amount"), 
            flask.request.json.get("comment")
        ))
        conn.commit()

    cur.execute("""SELECT id, name, email, payments, received_quantity, ordered_quantity, missing_quantity, ROUND(total_cost) AS total_cost, ROUND(estimated_cost) AS estimated_cost, ROUND(total_payments) AS total_payments, ROUND(remainder) as remainder FROM settlement WHERE listing_id=%(listing)s""", {'listing': listing_id})
    payment_status = cur.fetchall()
    return dict(members=payment_status)

@app.route('/api/listing/<int:listing_id>/shipments', methods=["GET", "POST"])
@app.route('/api/listing/<int:listing_id>/shipments/<int:shipment_id>', methods=["GET", "PUT", "DELETE"])
@helpers.authenticate_admin
def shipments(listing_id, shipment_id=None):
    conn, cur = get_db()
    cur.execute("""SELECT * FROM listings WHERE id=%(id)s""", {'id': listing_id})
    listing = cur.fetchone()

    if flask.request.method == "POST":
        body = flask.request.json

        cur.execute("""INSERT INTO shipments (listing_id, arrival, total_cost, comment) VALUES (%s, %s, %s, %s) RETURNING id""", (
            listing_id, 
            body.get("time"), 
            body.get("amount"), 
            body.get("comment")
        ))
        id = cur.fetchone()["id"]

        for item in body["items"]:
            if item["quantity"] > 0:
                cur.execute("""INSERT INTO shipment_items (shipment_id, item_id, quantity) VALUES (%s, %s, %s)""", (id, item["id"], item["quantity"]))

                for member in item["members"]:
                    cur.execute("""INSERT INTO shipment_allocation (shipment_id, item_id, listing_member_id, quantity) VALUES (%s, %s, %s, %s)""", (id, item["id"], member["id"], member["quantity"]))

        conn.commit()
    elif flask.request.method == "PUT":
        assert shipment_id is not None

        body = flask.request.json

        cur.execute("""UPDATE shipments SET arrival=%s, total_cost=%s, comment=%s WHERE id=%s""", (
            body.get("time"), 
            body.get("amount"), 
            body.get("comment"),
            shipment_id, 
        ))

        for item in body["items"]:
            if item["quantity"] > 0:
                cur.execute("SELECT COUNT(*) AS cnt FROM shipment_items WHERE shipment_id=%s AND item_id=%s", (shipment_id, item["id"]))
                cnt = cur.fetchone()["cnt"]
                if cnt == 0:
                    cur.execute("""INSERT INTO shipment_items (shipment_id, item_id, quantity) VALUES (%s, %s, %s)""", (shipment_id, item["id"], item["quantity"]))
                else:
                    cur.execute("""UPDATE shipment_items SET quantity=%s WHERE shipment_id=%s AND item_id=%s""", (item["quantity"], shipment_id, item["id"]))

                for member in item["members"]:
                    if member["quantity"] > 0: 
                        cur.execute("SELECT COUNT(*) AS cnt FROM shipment_allocation WHERE shipment_id=%s AND item_id=%s AND listing_member_id=%s", (shipment_id, item["id"], member["id"]))
                        cnt = cur.fetchone()["cnt"]
                        if cnt == 0:
                            cur.execute("""INSERT INTO shipment_allocation (shipment_id, item_id, listing_member_id, quantity) VALUES (%s, %s, %s, %s)""", (shipment_id, item["id"], member["id"], member["quantity"]))
                        else:
                            cur.execute("""UPDATE shipment_allocation SET quantity=%s WHERE shipment_id=%s AND item_id=%s AND listing_member_id=%s""", (member["quantity"], shipment_id, item["id"], member["id"]))
                    else:
                        cur.execute("""DELETE FROM shipment_allocation WHERE shipment_id=%s AND item_id=%s AND listing_member_id=%s""", (shipment_id, item["id"], member["id"]))

            else:
                cur.execute("DELETE FROM shipment_allocation WHERE shipment_id=%s AND item_id=%s", (shipment_id, item["id"]))
                cur.execute("DELETE FROM shipment_items WHERE shipment_id=%s AND item_id=%s", (shipment_id, item["id"]))

        conn.commit()
    elif flask.request.method == "DELETE":
        cur.execute("DELETE FROM shipment_allocation WHERE shipment_id=%s", (shipment_id, ))
        cur.execute("DELETE FROM shipment_items WHERE shipment_id=%s", (shipment_id, ))
        cur.execute("DELETE FROM shipments WHERE id=%s", (shipment_id, ))
        conn.commit()
        shipment_id = None

    shipment = None
    if shipment_id is not None:
        cur.execute("""SELECT arrival, total_cost, comment FROM shipments WHERE id=%s AND listing_id=%s""", (shipment_id, listing_id))
        shipment = cur.fetchone()

    cur.execute("""
        SELECT 
            i.id, 
            i.vendor_id, 
            i.vendor_url, 
            i.vendor_url || '?number=' || i.vendor_id AS url,
            i.item_name, 
            ARRAY(SELECT row_to_json(t)::jsonb FROM (SELECT it.original, it.adjusted, it.value FROM item_properties it WHERE it.item_id=i.id) AS t) AS properties,
            ARRAY(SELECT row_to_json(t)::jsonb FROM (
                SELECT 
                    lm2.id, 
                    lm2.name, 
                    lm2.email, 
                    SUM(ci2.quantity) AS ordered_quantity, 
                    COALESCE(SUM(sa2.quantity), 0) AS allocated_quantity, 
                    SUM(ci2.quantity) - COALESCE(SUM(sa2.quantity),0) AS remaining_quantity,
                    COALESCE(SUM(sa3.quantity), 0) AS shipment_quantity
                FROM listing_members lm2 
                    INNER JOIN cart_items ci2 ON ci2.listing_member_id = lm2.id
                    LEFT JOIN shipment_allocation sa2 ON sa2.listing_member_id = lm2.id AND sa2.item_id = i.id AND sa2.shipment_id != %(exclude_shipment)s
                    LEFT JOIN shipment_allocation sa3 ON sa3.listing_member_id = lm2.id AND sa3.item_id = i.id AND sa3.shipment_id = %(exclude_shipment)s
                WHERE ci2.item_id = i.id 
                GROUP BY lm2.id, lm2.name, lm2.email
                ) AS t) AS members,
            SUM(ci.quantity) AS ordered_quantity,
            COALESCE(SUM(si.quantity), 0) AS received_quantity,
            COALESCE(SUM(sa.quantity), 0) AS allocated_quantity,
            SUM(ci.quantity) - COALESCE(SUM(si.quantity), 0) AS missing_quantity,
            COALESCE((SELECT SUM(si2.quantity) FROM shipment_items si2 WHERE si2.item_id = i.id AND si2.shipment_id = %(exclude_shipment)s), 0) AS shipment_quantity
        FROM listing_members lm
            INNER JOIN cart_items ci ON ci.listing_member_id = lm.id
            INNER JOIN items i ON i.id = ci.item_id 
            INNER JOIN listings l on l.id = i.listing_id 
            LEFT JOIN shipment_items si ON si.item_id = i.id AND si.shipment_id != %(exclude_shipment)s
            LEFT JOIN shipment_items si2 ON si2.item_id = i.id AND si2.shipment_id = %(exclude_shipment)s
            LEFT JOIN shipment_items sa ON sa.item_id = i.id AND sa.shipment_id != %(exclude_shipment)s
        WHERE lm.listing_id = %(listing)s AND lm.confirmed IS NOT NULL 
        GROUP BY i.id, i.item_name, i.vendor_id, i.vendor_url, url, properties, members
        ORDER BY i.vendor_id
    """, {'listing': listing_id, 'exclude_shipment': shipment_id})
    items = cur.fetchall()

    cur.execute("""
        SELECT
            s.id,
            s.arrival,
            s.total_cost,
            s.comment,
            COALESCE((SELECT SUM(quantity) FROM cart_items ci WHERE ci.listing_member_id IN (SELECT id FROM listing_members WHERE listing_id = %(listing)s)), 0) AS ordered_quantity,
            COALESCE((SELECT SUM(quantity) FROM shipment_items si WHERE si.shipment_id = s.id), 0) AS delivered_quantity,
            COALESCE((SELECT SUM(quantity) FROM shipment_allocation sa WHERE sa.shipment_id = s.id), 0) AS allocated_quantity
        FROM shipments s
        WHERE s.listing_id = %(listing)s
    """, {'listing': listing_id})
    shipments = cur.fetchall()

    return {'shipments': shipments, 'items': items, 'shipment': shipment}


    return dict(shipment=shipment)

@app.route('/api/listing/<int:listing_id>/order')
@helpers.authenticate_admin
def listing_order(listing_id):
    conn, cur = get_db()
    cur.execute("""SELECT * FROM listings WHERE id=%(id)s""", {'id': listing_id})
    listing = cur.fetchone()

    cur.execute("""
        SELECT 
            i.id, 
            i.vendor_id, 
            i.vendor_url, 
            i.vendor_url || '?number=' || i.vendor_id AS url,
            i.item_name, 
            i.price, i.price*exchange_rate as price_isk,
            ARRAY(SELECT row_to_json(t)::jsonb FROM (SELECT it.original, it.adjusted, it.value FROM item_properties it WHERE it.item_id=i.id) AS t) AS properties,
            sum(quantity) AS qty, 
            sum(price*quantity) AS fk_total, 
            sum(price*quantity*exchange_rate) as isk_total,
            ARRAY(SELECT row_to_json(t)::jsonb FROM (
                SELECT 
                    lm2.*,
                    ci2.item_id,
                    quantity AS qty, price*quantity AS fk_total, price*quantity*exchange_rate as isk_total, ci2.listing_member_id 
                FROM listing_members lm2
                    INNER JOIN cart_items ci2 ON ci2.listing_member_id = lm2.id
                    INNER JOIN items i2 ON i2.id = ci2.item_id 
                    INNER JOIN listings l2 ON l2.id = i2.listing_id 
                WHERE lm2.listing_id = %(listing)s AND i2.id = i.id AND lm2.confirmed IS NOT NULL 
                ORDER BY lm2.name ASC 
            ) as t) as members
        FROM listing_members lm
            INNER JOIN cart_items ci ON ci.listing_member_id = lm.id
            INNER JOIN items i ON i.id = ci.item_id 
            INNER JOIN listings l on l.id = i.listing_id 
        WHERE lm.listing_id = %(listing)s AND lm.confirmed IS NOT NULL
        GROUP BY i.id, i.item_name, i.vendor_id, i.vendor_url, url, i.price, properties, exchange_rate
        ORDER BY i.vendor_id
    """, {'listing': listing_id})
    confirmed_order = cur.fetchall()

    return dict(order=confirmed_order)

@app.route('/api/listing/<int:listing_id>/members')
@helpers.authenticate_admin
def listing_members(listing_id):
    conn, cur = get_db()
    cur.execute("""SELECT * FROM listings WHERE id=%(id)s""", {'id': listing_id})
    listing = cur.fetchone()

    cur.execute("""
        SELECT lm.*, quantities.*
        FROM listing_members lm
        INNER JOIN 
            (
                SELECT SUM(quantity) AS qty, SUM(price*quantity) AS fk_total, SUM(price*quantity*exchange_rate) as isk_total, ci.listing_member_id 
                FROM cart_items ci 
                    INNER JOIN items i on i.id = ci.item_id 
                    INNER JOIN listings l on l.id = i.listing_id 
                GROUP BY ci.listing_member_id
            ) quantities ON quantities.listing_member_id = lm.id
        WHERE listing_id=%(id)s
        ORDER BY name ASC
    """, {'id': listing_id})
    members = cur.fetchall()

    cur.execute("""
        SELECT i.vendor_id, i.vendor_url, i.vendor_url || '?number=' || i.vendor_id AS url, i.item_name, i.price, i.price*exchange_rate as price_isk,
            ARRAY(SELECT row_to_json(t)::jsonb FROM (SELECT it.original, it.adjusted, it.value FROM item_properties it WHERE it.item_id=i.id) AS t) AS properties,
            quantity AS qty, price*quantity AS fk_total, price*quantity*exchange_rate as isk_total, ci.listing_member_id 
        FROM cart_items ci 
            INNER JOIN items i ON i.id = ci.item_id 
            INNER JOIN listings l ON l.id = i.listing_id 
        WHERE l.id = %(id)s
    """, {'id': listing_id})
    entries = cur.fetchall()
    for i, member in enumerate(members):
        members[i]["entries"] = [e for e in entries if e['listing_member_id'] == member['listing_member_id']]

    return dict(members=members)

@app.route('/api/listing/<int:listing_id>')
@helpers.authenticate_admin
def listing(listing_id):
    conn, cur = get_db()
    cur.execute("""SELECT * FROM listings WHERE id=%(id)s""", {'id': listing_id})
    listing = cur.fetchone()

    return dict(listing=listing)

@app.route('/api/listing/')
@helpers.authenticate_listing
def listing_by_token(listing):
    cart_items = helpers.get_cart(listing['listing_member_id'])

    return flask.json.jsonify(
        listing={
            'id':        listing['id'], 
            'title':     listing['title'], 
            'opens':     listing['opens'], 
            'closes':    listing['closes'], 
            'locked':    listing['locked'],
            'confirmed': listing['confirmed']
        }, member={
            'name':  listing['name'],
            'email': listing['email'],
        }, cart=cart_items)

@app.route('/api/listing/items')
@helpers.authenticate_listing
def listing_items(listing):
    q = flask.request.args.get('q', "")
    c = flask.request.args.get('c', 'item_name')
    d = flask.request.args.get('d', 'asc')
    if c not in ("item_name", "vendor_id", "price"): c = "item_name"
    if d not in ("asc", "desc"): d = "asc"
    try:
        qf = q.split(" ")[0]
        if qf.strip() == "":
            qf = None
    except IndexError:
        qf = None

    conn, cur = get_db()

    cur.execute(f"""
        SELECT * FROM
            (SELECT 
                i.id, 
                i.item_name, 
                i.vendor_id, 
                i.vendor_url, 
                i.vendor_url || '?number=' || i.vendor_id AS url,
                i.description,
                i.price, 
                l.currency, 
                i.price*l.exchange_rate as price_isk, 
                ARRAY(SELECT row_to_json(t) FROM (SELECT it.original, it.adjusted, it.value FROM item_properties it WHERE it.item_id=i.id) AS t) AS properties,
                i.vendor_id || ' ' || i.item_name || ' ' || COALESCE((SELECT STRING_AGG(value, ' ') FROM (SELECT it.value FROM item_properties it WHERE it.item_id=i.id) AS tbl), '') AS search_str 
            FROM items i 
                INNER JOIN listings l ON l.id = i.listing_id 
                INNER JOIN listing_members lm ON l.id = lm.listing_id 
            WHERE lm.listing_key = %(lk)s) AS tbl
        {'WHERE LOWER(tbl.search_str) LIKE %(qf)s' if qf is not None else ''} 
        ORDER BY {c} {d.upper()}""", {'lk': listing['listing_key'], 'qf': f"%{qf.lower()}%" if qf is not None else ""})
    items = [dict(x) for x in cur.fetchall()]
    if q is not None:
        qs = q.split(" ")
        for q in qs:
            items = [x for x in items if q.lower() in x['search_str'].lower()]

    return dict(items=items)


@app.route('/api/listings')
@helpers.authenticate_admin
def listings():
    conn, cur = get_db()
    cur.execute("""
        SELECT id, title, opens, closes, currency, exchange_rate FROM listings ORDER BY closes DESC;
    """)
    listings = [dict(x) for x in cur.fetchall()]

    return dict(listings=listings)
