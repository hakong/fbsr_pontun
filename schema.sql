--DROP SCHEMA public CASCADE; CREATE SCHEMA public;

CREATE TABLE IF NOT EXISTS listings (
	id serial PRIMARY KEY NOT NULL,
	title character varying(1000) NOT NULL,
	opens timestamp without time zone NOT NULL,
	closes timestamp without time zone NOT NULL,
	currency character varying NOT NULL,
	exchange_rate double precision NOT NULL
);


CREATE TABLE IF NOT EXISTS items (
	id serial PRIMARY KEY NOT NULL,
	listing_id integer REFERENCES listings(id) NOT NULL,
	item_name character varying(1000) NOT NULL,
	vendor_id character varying(1000) NOT NULL,
	vendor_url character varying (1000) NULL,
	vendor_img_url character varying(1000) NULL,
	description text NOT NULL DEFAULT '',
	price double precision NOT NULL,
	UNIQUE(listing_id, vendor_id)
);

CREATE TABLE IF NOT EXISTS item_properties (
	id serial PRIMARY KEY NOT NULL,
	item_id integer REFERENCES items(id) NOT NULL,
	original character varying(1000) NOT NULL,
	adjusted character varying(1000) NOT NULL,
	value character varying(1000) NOT NULL,
	UNIQUE(item_id, original)
);

CREATE TABLE IF NOT EXISTS listing_members (
	id serial PRIMARY KEY NOT NULL,
	listing_id integer REFERENCES listings(id) NOT NULL,
	name character varying(1000) NOT NULL,
	email character varying(1000) NOT NULL,
	locked timestamp without time zone NULL,
	confirmed timestamp without time zone NULL,
	signup timestamp without time zone NULL,
	last_movement timestamp without time zone NULL,
	listing_key character varying(1000) NULL,
	confirmation_key character varying(1000) NULL,
	UNIQUE(listing_key),
	UNIQUE(confirmation_key),
	UNIQUE(listing_id, email)
);

CREATE TABLE IF NOT EXISTS cart_items (
	id serial PRIMARY KEY NOT NULL,
	listing_member_id integer REFERENCES listing_members(id) NOT NULL,
	item_id integer REFERENCES items(id) NOT NULL,
	quantity integer not null CHECK (quantity > 0 AND quantity < 10000),
	UNIQUE(listing_member_id, item_id)
);

SELECT si.shipment_id, i.item_id, SUM(si.quantity * it.price) as summa_pontun, s
FROM shipment_items si 
	INNER JOIN items it ON it.id = si.item_id
	INNER JOIN shipments s ON s.id = si.shipment_id
;

--WITH shipments_rates AS (
--	SELECT s.id AS shipment_id, SUM(si.quantity * it.price) AS estimated_cost, s.total_cost, SUM(si.quantity * it.price) / s.total_cost AS actual_rate
--		FROM shipments s
--			INNER JOIN shipment_items si ON si.shipment_id = s.id
--			INNER JOIN items it ON si.item_id = it.id
--		GROUP BY s.id, s.total_cost
--	)
--SELECT lm.id, lm.name, lm.email, SUM(sa.quantity * i.price * sr.actual_rate) AS total_cost, SUM(p.amount) AS total_payments
--FROM listing_members lm
--	LEFT JOIN shipment_allocation sa ON sa.listing_members_id = lm.id
--	LEFT JOIN shipment_items si ON sa.items_id = si.item_id
--	LEFT JOIN items i ON i.id = sa.items_id
--	LEFT JOIN shipments_rates sr ON sr.shipment_id = si.shipment_id
--	LEFT JOIN payments p ON p.listing_members_id = lm.id
--WHERE lm.listing_id = 1
--GROUP BY lm.id, lm.name, lm.email;


CREATE TABLE IF NOT EXISTS shipments (
	id serial PRIMARY KEY NOT NULL,
	listing_id integer REFERENCES listings(id) NOT NULL,
	arrival timestamp without time zone,
	total_cost integer NOT NULL,
	comment text NOT NULL
);

CREATE TABLE IF NOT EXISTS shipment_items (
	id serial PRIMARY KEY NOT NULL,
	shipment_id integer REFERENCES shipments(id) NOT NULL,
	item_id integer REFERENCES items(id),
	quantity integer NOT NULL CHECK (quantity > 0),
	UNIQUE(shipment_id, item_id)
);

CREATE TABLE IF NOT EXISTS shipment_allocation (
	id serial PRIMARY KEY NOT NULL,
	shipment_id integer REFERENCES shipments(id) NOT NULL,
	item_id integer REFERENCES items(id) NOT NULL,
	listing_member_id integer REFERENCES listing_members(id) NOT NULL,
	quantity integer NOT NULL CHECK (quantity > 0),
	UNIQUE(shipment_id, item_id, listing_member_id)
);

CREATE TABLE IF NOT EXISTS payments (
	id serial PRIMARY KEY NOT NULL,
	listing_member_id integer REFERENCES listing_members(id) NOT NULL,
	time timestamp without time zone,
	amount integer NOT NULL,
	comment text
);

CREATE TABLE IF NOT EXISTS emails (
	id serial PRIMARY KEY NOT NULL,
	listing_member_id integer REFERENCES listing_members(id) NOT NULL,
	scheduled timestamp without time zone NOT NULL,
	sent timestamp without time zone,
	subject text not null,
	body text not null
);


CREATE OR REPLACE VIEW shipment_rates AS (
		SELECT
				s.id AS shipment_id,
				s.listing_id AS listing_id,
				SUM(si.quantity * it.price) AS estimated_cost,
				s.total_cost,
				s.total_cost / SUM(si.quantity * it.price) AS actual_rate
		FROM shipments s
				INNER JOIN shipment_items si ON si.shipment_id = s.id
				INNER JOIN items it ON si.item_id = it.id
		GROUP BY s.id, s.total_cost
);

CREATE OR REPLACE VIEW settlement AS (
		SELECT *, total_cost - total_payments as remainder, ordered_quantity - received_quantity as missing_quantity
		FROM (
				SELECT lm.id, lm.name, lm.email, lm.listing_id,
						ARRAY(SELECT row_to_json(t)::jsonb FROM (
								SELECT p.id, p.time, p.amount, p.comment FROM payments p WHERE p.listing_member_id = lm.id
						) as t) AS payments,
						COALESCE((
								SELECT SUM(sa.quantity)
								FROM shipment_allocation sa
								WHERE sa.listing_member_id = lm.id
								), 0)::integer AS received_quantity,
						COALESCE((
								SELECT SUM(ci.quantity)
								FROM cart_items ci
								WHERE ci.listing_member_id = lm.id
								), 0)::integer AS ordered_quantity,
						COALESCE((
								SELECT SUM(sa.quantity * i.price * sr.actual_rate)
								FROM shipment_allocation sa
										INNER JOIN items i ON i.id = sa.item_id
										INNER JOIN shipment_rates sr ON sr.shipment_id = sa.shipment_id
								WHERE sa.listing_member_id = lm.id
								), 0) AS total_cost,
						COALESCE((
								SELECT SUM(sa.quantity * i.price * l.exchange_rate)
								FROM shipment_allocation sa
										INNER JOIN items i ON i.id = sa.item_id
										INNER JOIN listings l ON i.listing_id = l.id
								WHERE sa.listing_member_id = lm.id
								), 0) AS estimated_cost,
						COALESCE((
								SELECT SUM(p.amount)
								FROM payments p
								WHERE p.listing_member_id = lm.id
								), 0) AS total_payments
				FROM listing_members lm
				WHERE lm.confirmed IS NOT NULL
		) as tbl
);

CREATE OR REPLACE VIEW member_details AS (
		SELECT 
				l.id as listing_id, l.title as vendor, l.opens, l.closes,
				lm.id AS listing_member_id, lm.name, lm.email, lm.locked, lm.confirmed, lm.listing_key, lm.confirmation_key, lm.last_movement, lm.signup,
				received_quantity, ordered_quantity, missing_quantity,
				s.payments, s.total_cost, s.estimated_cost, s.total_payments, s.remainder,
				ARRAY(SELECT row_to_json(t)::jsonb FROM (
						SELECT 
								i.vendor_id,
								i.item_name, 
								i.vendor_url,
								i.price as fk_price, 
								i.price * l.exchange_rate as estimated_price,  
								ci.quantity,  
								ci.quantity * i.price * l.exchange_rate as estimated_total_cost
						FROM cart_items ci
								INNER JOIN items i ON i.id = ci.item_id
						WHERE ci.listing_member_id = lm.id
				) as t) as items_ordered,
				ARRAY(SELECT row_to_json(t)::jsonb FROM (
						SELECT 
								i.vendor_id,
								i.item_name, 
								i.vendor_url,
								i.price as fk_price, 
								i.price * l.exchange_rate as estimated_price,  
								SUM(sa.quantity) AS quantity,  
								SUM(sa.quantity * i.price * sr.actual_rate) as actual_total_cost, 
								SUM(sa.quantity * i.price * l.exchange_rate) as estimated_total_cost
						FROM shipment_allocation sa
								INNER JOIN items i ON i.id = sa.item_id
								INNER JOIN shipment_rates sr ON sr.shipment_id = sa.shipment_id
						WHERE sa.listing_member_id = lm.id
						GROUP BY i.vendor_id, i.item_name, i.vendor_url, i.price -- THERE CAN BE MULTIPLE SHIPMENTS
				) as t) as items_received,
				ARRAY(SELECT row_to_json(t)::jsonb FROM (
						SELECT 
								i.vendor_id,
								i.item_name,
								i.vendor_url,
								ci.quantity as ordered_quantity,
								COALESCE(SUM(sa.quantity), 0) as received_quantity,
								ci.quantity - COALESCE(SUM(sa.quantity), 0) as missing_quantity
						FROM cart_items ci 
								INNER JOIN items i ON ci.item_id = i.id
								LEFT JOIN shipment_allocation sa ON sa.listing_member_id = ci.listing_member_id AND sa.item_id = ci.item_id
						WHERE ci.listing_member_id = lm.id
						GROUP BY i.vendor_id, i.item_name, i.vendor_url, ci.quantity
				) as t WHERE t.missing_quantity > 0) as items_not_received
		FROM listing_members lm 
				INNER JOIN listings l ON l.id = lm.listing_id 
				LEFT JOIN settlement s ON s.id = lm.id
);


--INSERT INTO listings (title, opens, closes, currency, exchange_rate, signup_key) VALUES ('Lupine', current_timestamp, '2020-11-15 23:59:59', 'EUR', 134, 'yeeg8eequ1Wei0Ah');
--INSERT INTO listing_members (listing_id, name, email) VALUES (1, 'Kári Hreinsson', 'kari@kari.is'); 
