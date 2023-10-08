--
-- PostgreSQL database dump
--

-- Dumped from database version 11.14 (Debian 11.14-0+deb10u1)
-- Dumped by pg_dump version 11.14 (Debian 11.14-0+deb10u1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: cart_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cart_items (
    id integer NOT NULL,
    listing_member_id integer NOT NULL,
    item_id integer NOT NULL,
    quantity integer NOT NULL,
    CONSTRAINT cart_items_quantity_check CHECK (((quantity > 0) AND (quantity < 10000)))
);


--
-- Name: cart_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cart_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cart_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cart_items_id_seq OWNED BY public.cart_items.id;


--
-- Name: emails; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.emails (
    id integer NOT NULL,
    listing_member_id integer NOT NULL,
    scheduled timestamp without time zone NOT NULL,
    sent timestamp without time zone,
    subject text NOT NULL,
    body text NOT NULL
);


--
-- Name: emails_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.emails_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: emails_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.emails_id_seq OWNED BY public.emails.id;


--
-- Name: item_properties; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.item_properties (
    id integer NOT NULL,
    item_id integer NOT NULL,
    original character varying(1000) NOT NULL,
    adjusted character varying(1000) NOT NULL,
    value character varying(1000) NOT NULL
);


--
-- Name: item_properties_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.item_properties_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: item_properties_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.item_properties_id_seq OWNED BY public.item_properties.id;


--
-- Name: items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.items (
    id integer NOT NULL,
    listing_id integer NOT NULL,
    item_name character varying(1000) NOT NULL,
    vendor_id character varying(1000) NOT NULL,
    vendor_url character varying(1000),
    vendor_img_url character varying(1000),
    price double precision NOT NULL,
    description text DEFAULT ''::text NOT NULL
);


--
-- Name: items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.items_id_seq OWNED BY public.items.id;


--
-- Name: listing_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.listing_members (
    id integer NOT NULL,
    listing_id integer NOT NULL,
    name character varying(1000) NOT NULL,
    email character varying(1000) NOT NULL,
    locked timestamp without time zone,
    confirmed timestamp without time zone,
    listing_key character varying(1000),
    confirmation_key character varying(1000),
    last_movement timestamp without time zone,
    signup timestamp without time zone
);


--
-- Name: listing_members_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.listing_members_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: listing_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.listing_members_id_seq OWNED BY public.listing_members.id;


--
-- Name: listings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.listings (
    id integer NOT NULL,
    title character varying(1000) NOT NULL,
    opens timestamp without time zone NOT NULL,
    closes timestamp without time zone NOT NULL,
    currency character varying NOT NULL,
    exchange_rate double precision NOT NULL
);


--
-- Name: listings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.listings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: listings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.listings_id_seq OWNED BY public.listings.id;


--
-- Name: payments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payments (
    id integer NOT NULL,
    listing_member_id integer NOT NULL,
    "time" timestamp without time zone,
    amount integer NOT NULL,
    comment text
);


--
-- Name: shipment_allocation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shipment_allocation (
    id integer NOT NULL,
    shipment_id integer NOT NULL,
    item_id integer NOT NULL,
    listing_member_id integer NOT NULL,
    quantity integer NOT NULL,
    CONSTRAINT shipment_allocation_quantity_check CHECK ((quantity > 0))
);


--
-- Name: shipment_rates; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.shipment_rates AS
SELECT
    NULL::integer AS shipment_id,
    NULL::integer AS listing_id,
    NULL::double precision AS estimated_cost,
    NULL::integer AS total_cost,
    NULL::double precision AS actual_rate;


--
-- Name: settlement; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.settlement AS
 SELECT tbl.id,
    tbl.name,
    tbl.email,
    tbl.listing_id,
    tbl.payments,
    tbl.received_quantity,
    tbl.ordered_quantity,
    tbl.total_cost,
    tbl.estimated_cost,
    tbl.total_payments,
    (tbl.total_cost - (tbl.total_payments)::double precision) AS remainder,
    (tbl.ordered_quantity - tbl.received_quantity) AS missing_quantity
   FROM ( SELECT lm.id,
            lm.name,
            lm.email,
            lm.listing_id,
            ARRAY( SELECT (row_to_json(t.*))::jsonb AS row_to_json
                   FROM ( SELECT p.id,
                            p."time",
                            p.amount,
                            p.comment
                           FROM public.payments p
                          WHERE (p.listing_member_id = lm.id)) t) AS payments,
            (COALESCE(( SELECT sum(sa.quantity) AS sum
                   FROM public.shipment_allocation sa
                  WHERE (sa.listing_member_id = lm.id)), (0)::bigint))::integer AS received_quantity,
            (COALESCE(( SELECT sum(ci.quantity) AS sum
                   FROM public.cart_items ci
                  WHERE (ci.listing_member_id = lm.id)), (0)::bigint))::integer AS ordered_quantity,
            COALESCE(( SELECT sum((((sa.quantity)::double precision * i.price) * sr.actual_rate)) AS sum
                   FROM ((public.shipment_allocation sa
                     JOIN public.items i ON ((i.id = sa.item_id)))
                     JOIN public.shipment_rates sr ON ((sr.shipment_id = sa.shipment_id)))
                  WHERE (sa.listing_member_id = lm.id)), (0)::double precision) AS total_cost,
            COALESCE(( SELECT sum((((sa.quantity)::double precision * i.price) * l.exchange_rate)) AS sum
                   FROM ((public.shipment_allocation sa
                     JOIN public.items i ON ((i.id = sa.item_id)))
                     JOIN public.listings l ON ((i.listing_id = l.id)))
                  WHERE (sa.listing_member_id = lm.id)), (0)::double precision) AS estimated_cost,
            COALESCE(( SELECT sum(p.amount) AS sum
                   FROM public.payments p
                  WHERE (p.listing_member_id = lm.id)), (0)::bigint) AS total_payments
           FROM public.listing_members lm
          WHERE (lm.confirmed IS NOT NULL)) tbl;


--
-- Name: member_details; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.member_details AS
 SELECT l.id AS listing_id,
    l.title AS vendor,
    l.opens,
    l.closes,
    lm.id AS listing_member_id,
    lm.name,
    lm.email,
    lm.locked,
    lm.confirmed,
    lm.listing_key,
    lm.confirmation_key,
    lm.last_movement,
    lm.signup,
    s.received_quantity,
    s.ordered_quantity,
    s.missing_quantity,
    s.payments,
    s.total_cost,
    s.estimated_cost,
    s.total_payments,
    s.remainder,
    ARRAY( SELECT (row_to_json(t.*))::jsonb AS row_to_json
           FROM ( SELECT i.vendor_id,
                    i.item_name,
                    i.vendor_url,
                    i.price AS fk_price,
                    (i.price * l.exchange_rate) AS estimated_price,
                    ci.quantity,
                    (((ci.quantity)::double precision * i.price) * l.exchange_rate) AS estimated_total_cost
                   FROM (public.cart_items ci
                     JOIN public.items i ON ((i.id = ci.item_id)))
                  WHERE (ci.listing_member_id = lm.id)) t) AS items_ordered,
    ARRAY( SELECT (row_to_json(t.*))::jsonb AS row_to_json
           FROM ( SELECT i.vendor_id,
                    i.item_name,
                    i.vendor_url,
                    i.price AS fk_price,
                    (i.price * l.exchange_rate) AS estimated_price,
                    sum(sa.quantity) AS quantity,
                    sum((((sa.quantity)::double precision * i.price) * sr.actual_rate)) AS actual_total_cost,
                    sum((((sa.quantity)::double precision * i.price) * l.exchange_rate)) AS estimated_total_cost
                   FROM ((public.shipment_allocation sa
                     JOIN public.items i ON ((i.id = sa.item_id)))
                     JOIN public.shipment_rates sr ON ((sr.shipment_id = sa.shipment_id)))
                  WHERE (sa.listing_member_id = lm.id)
                  GROUP BY i.vendor_id, i.item_name, i.vendor_url, i.price) t) AS items_received,
    ARRAY( SELECT (row_to_json(t.*))::jsonb AS row_to_json
           FROM ( SELECT i.vendor_id,
                    i.item_name,
                    i.vendor_url,
                    ci.quantity AS ordered_quantity,
                    COALESCE(sum(sa.quantity), (0)::bigint) AS received_quantity,
                    (ci.quantity - COALESCE(sum(sa.quantity), (0)::bigint)) AS missing_quantity
                   FROM ((public.cart_items ci
                     JOIN public.items i ON ((ci.item_id = i.id)))
                     LEFT JOIN public.shipment_allocation sa ON (((sa.listing_member_id = ci.listing_member_id) AND (sa.item_id = ci.item_id))))
                  WHERE (ci.listing_member_id = lm.id)
                  GROUP BY i.vendor_id, i.item_name, i.vendor_url, ci.quantity) t
          WHERE (t.missing_quantity > 0)) AS items_not_received
   FROM ((public.listing_members lm
     JOIN public.listings l ON ((l.id = lm.listing_id)))
     LEFT JOIN public.settlement s ON ((s.id = lm.id)));


--
-- Name: payments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.payments_id_seq OWNED BY public.payments.id;


--
-- Name: shipment_allocation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.shipment_allocation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: shipment_allocation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.shipment_allocation_id_seq OWNED BY public.shipment_allocation.id;


--
-- Name: shipment_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shipment_items (
    id integer NOT NULL,
    shipment_id integer NOT NULL,
    item_id integer,
    quantity integer NOT NULL,
    CONSTRAINT shipment_items_quantity_check CHECK ((quantity > 0))
);


--
-- Name: shipment_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.shipment_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: shipment_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.shipment_items_id_seq OWNED BY public.shipment_items.id;


--
-- Name: shipments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shipments (
    id integer NOT NULL,
    listing_id integer NOT NULL,
    arrival timestamp without time zone,
    total_cost integer NOT NULL,
    comment text NOT NULL
);


--
-- Name: shipments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.shipments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: shipments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.shipments_id_seq OWNED BY public.shipments.id;


--
-- Name: cart_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cart_items ALTER COLUMN id SET DEFAULT nextval('public.cart_items_id_seq'::regclass);


--
-- Name: emails id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.emails ALTER COLUMN id SET DEFAULT nextval('public.emails_id_seq'::regclass);


--
-- Name: item_properties id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_properties ALTER COLUMN id SET DEFAULT nextval('public.item_properties_id_seq'::regclass);


--
-- Name: items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.items ALTER COLUMN id SET DEFAULT nextval('public.items_id_seq'::regclass);


--
-- Name: listing_members id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.listing_members ALTER COLUMN id SET DEFAULT nextval('public.listing_members_id_seq'::regclass);


--
-- Name: listings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.listings ALTER COLUMN id SET DEFAULT nextval('public.listings_id_seq'::regclass);


--
-- Name: payments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments ALTER COLUMN id SET DEFAULT nextval('public.payments_id_seq'::regclass);


--
-- Name: shipment_allocation id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipment_allocation ALTER COLUMN id SET DEFAULT nextval('public.shipment_allocation_id_seq'::regclass);


--
-- Name: shipment_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipment_items ALTER COLUMN id SET DEFAULT nextval('public.shipment_items_id_seq'::regclass);


--
-- Name: shipments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments ALTER COLUMN id SET DEFAULT nextval('public.shipments_id_seq'::regclass);


--
-- Name: cart_items cart_items_listing_member_id_item_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cart_items
    ADD CONSTRAINT cart_items_listing_member_id_item_id_key UNIQUE (listing_member_id, item_id);


--
-- Name: cart_items cart_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cart_items
    ADD CONSTRAINT cart_items_pkey PRIMARY KEY (id);


--
-- Name: emails emails_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.emails
    ADD CONSTRAINT emails_pkey PRIMARY KEY (id);


--
-- Name: item_properties item_properties_item_id_original_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_properties
    ADD CONSTRAINT item_properties_item_id_original_key UNIQUE (item_id, original);


--
-- Name: item_properties item_properties_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_properties
    ADD CONSTRAINT item_properties_pkey PRIMARY KEY (id);


--
-- Name: items items_listing_id_vendor_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.items
    ADD CONSTRAINT items_listing_id_vendor_id_key UNIQUE (listing_id, vendor_id);


--
-- Name: items items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.items
    ADD CONSTRAINT items_pkey PRIMARY KEY (id);


--
-- Name: listing_members listing_members_confirmation_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.listing_members
    ADD CONSTRAINT listing_members_confirmation_key_key UNIQUE (confirmation_key);


--
-- Name: listing_members listing_members_listing_id_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.listing_members
    ADD CONSTRAINT listing_members_listing_id_email_key UNIQUE (listing_id, email);


--
-- Name: listing_members listing_members_listing_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.listing_members
    ADD CONSTRAINT listing_members_listing_key_key UNIQUE (listing_key);


--
-- Name: listing_members listing_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.listing_members
    ADD CONSTRAINT listing_members_pkey PRIMARY KEY (id);


--
-- Name: listings listings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.listings
    ADD CONSTRAINT listings_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: shipment_allocation shipment_allocation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipment_allocation
    ADD CONSTRAINT shipment_allocation_pkey PRIMARY KEY (id);


--
-- Name: shipment_allocation shipment_allocation_shipment_id_item_id_listing_member_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipment_allocation
    ADD CONSTRAINT shipment_allocation_shipment_id_item_id_listing_member_id_key UNIQUE (shipment_id, item_id, listing_member_id);


--
-- Name: shipment_items shipment_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipment_items
    ADD CONSTRAINT shipment_items_pkey PRIMARY KEY (id);


--
-- Name: shipment_items shipment_items_shipment_id_item_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipment_items
    ADD CONSTRAINT shipment_items_shipment_id_item_id_key UNIQUE (shipment_id, item_id);


--
-- Name: shipments shipments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT shipments_pkey PRIMARY KEY (id);


--
-- Name: shipment_rates _RETURN; Type: RULE; Schema: public; Owner: -
--

CREATE OR REPLACE VIEW public.shipment_rates AS
 SELECT s.id AS shipment_id,
    s.listing_id,
    sum(((si.quantity)::double precision * it.price)) AS estimated_cost,
    s.total_cost,
    ((s.total_cost)::double precision / sum(((si.quantity)::double precision * it.price))) AS actual_rate
   FROM ((public.shipments s
     JOIN public.shipment_items si ON ((si.shipment_id = s.id)))
     JOIN public.items it ON ((si.item_id = it.id)))
  GROUP BY s.id, s.total_cost;


--
-- Name: cart_items cart_items_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cart_items
    ADD CONSTRAINT cart_items_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.items(id);


--
-- Name: cart_items cart_items_listing_member_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cart_items
    ADD CONSTRAINT cart_items_listing_member_id_fkey FOREIGN KEY (listing_member_id) REFERENCES public.listing_members(id);


--
-- Name: emails emails_listing_member_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.emails
    ADD CONSTRAINT emails_listing_member_id_fkey FOREIGN KEY (listing_member_id) REFERENCES public.listing_members(id);


--
-- Name: item_properties item_properties_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_properties
    ADD CONSTRAINT item_properties_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.items(id) ON DELETE CASCADE;


--
-- Name: items items_listing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.items
    ADD CONSTRAINT items_listing_id_fkey FOREIGN KEY (listing_id) REFERENCES public.listings(id);


--
-- Name: listing_members listing_members_listing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.listing_members
    ADD CONSTRAINT listing_members_listing_id_fkey FOREIGN KEY (listing_id) REFERENCES public.listings(id);


--
-- Name: payments payments_listing_member_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_listing_member_id_fkey FOREIGN KEY (listing_member_id) REFERENCES public.listing_members(id);


--
-- Name: shipment_allocation shipment_allocation_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipment_allocation
    ADD CONSTRAINT shipment_allocation_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.items(id);


--
-- Name: shipment_allocation shipment_allocation_listing_member_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipment_allocation
    ADD CONSTRAINT shipment_allocation_listing_member_id_fkey FOREIGN KEY (listing_member_id) REFERENCES public.listing_members(id);


--
-- Name: shipment_allocation shipment_allocation_shipment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipment_allocation
    ADD CONSTRAINT shipment_allocation_shipment_id_fkey FOREIGN KEY (shipment_id) REFERENCES public.shipments(id);


--
-- Name: shipment_items shipment_items_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipment_items
    ADD CONSTRAINT shipment_items_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.items(id);


--
-- Name: shipment_items shipment_items_shipment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipment_items
    ADD CONSTRAINT shipment_items_shipment_id_fkey FOREIGN KEY (shipment_id) REFERENCES public.shipments(id);


--
-- Name: shipments shipments_listing_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT shipments_listing_id_fkey FOREIGN KEY (listing_id) REFERENCES public.listings(id);


--
-- PostgreSQL database dump complete
--

