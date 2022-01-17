import sys
import json
import itertools
import requests
import urllib.parse as urlparse
from   urllib.parse import urlencode

import bs4
from bs4 import BeautifulSoup
import psycopg2

conn = psycopg2.connect("dbname=fbsr_pontun user=fbsr_pontun host=127.0.0.1 password=''")
cur  = conn.cursor()

base = "https://www.lupine-shop.com"
base_path = "/en/"

visited_urls = set()
to_visit_urls = {'https://www.lupine-shop.com/en/Betty-warmwhite-4900-Kelvin-optional/i026-005', }#base + base_path, }
to_visit_urls.add('https://www.lupine-shop.com/en/Wilma-helmetlight/i1600-002M')
to_visit_urls.add('https://www.lupine-shop.com/en/SL-F-Barmount-35-mm-CNC-machined/i235')
to_visit_urls.add('https://www.lupine-shop.com/en/Lightcable-for-E-Bikes/i2299')
to_visit_urls.add('https://www.lupine-shop.com/en/SL-X-for-E-Bikes/i4800')
to_visit_urls.add('https://www.lupine-shop.com/en/Blika-headlamp/i0150-205')
to_visit_urls.add('https://www.lupine-shop.com/en/Piko-All-in-One/i4500-206')
to_visit_urls.add('https://www.lupine-shop.com/en/SL-X-Mount-Bosch-Intuvia-Nyon/i251')
to_visit_urls.add('https://www.lupine-shop.com/en/Penta/i0750')
to_visit_urls.add('https://www.lupine-shop.com/en/SL-Nano-Canyon/i7800CN')
to_visit_urls.add('https://www.lupine-shop.com/en/SL-Nano-Newmen-Kit/i7600NM-30')
to_visit_urls.add('https://www.lupine-shop.com/en/LED-Lightsets/')
#to_visit_urls = {base + base_path, }
product_dict = {}
validate_list = []

session = requests.Session()
#response = session.get(base + "/en/csrftoken")
#import pdb; pdb.set_trace()
#csrf_token = response.headers['x-csrf-token']
#session.cookies.set_cookie(requests.cookies.create_cookie(domain='www.lupine-shop.com', name='__csrf_token-3', value=csrf_token))

def get_product_details(url, response):
    s = BeautifulSoup(response,"html.parser")

    try:
        title = s.find('h1', attrs={'class': 'product-detail-name'}).text.strip()
    except AttributeError:
        title = None
        return


    try:
        price = float(s.find('meta', attrs={'itemprop': 'price'}).attrs['content'])
    except AttributeError:
        price = None

    #try:
    #    delivery = s.find_all(attrs={'class': 'delivery--text'})[0].text.strip()
    #except IndexError:
    #    delivery = None

    try:
        sku = s.find('span', attrs={'itemprop': 'sku'}).text.strip()
    except AttributeError:
        print("WARNING NO SKU")
        import pdb; pdb.set_trace()
        sku = None

    if not url.endswith(sku):
        print(f"WARNING STRANGE URL? {url} {sku}")
        validate_list.append((sku, url))
        return


    try:
        availability = s.find('link', attrs={'itemprop': 'availability'}).href
    except AttributeError:
        availability = None

    _props = s.find_all('tr', attrs={'class': 'properties-row'})
    props = []
    for prop in _props:
        assert list(list(prop.children)[3].children)[1].name == "span" 
        props.append((
            list(prop.children)[1].text.strip().strip(':'), 
            list(list(prop.children)[3].children)[1].text.strip()
        ))


    options = []
    option_choices = []
    try:
        choice_lookup_url = json.loads(s.find('div', attrs={'class': 'product-detail-configurator'}).find('form').attrs['data-variant-switch-options'])["url"]
        for group in s.find_all('div', attrs={'class': 'product-detail-configurator-group'}):
            group_title = group.find('div', attrs={'class': 'product-detail-configurator-group-title'}).text.strip()

            choices = []
            for option in group.find_all('div', attrs={'class': 'product-detail-configurator-option'}):
                assert len(option.find_all('label')) == 1
                assert len(option.find_all('input')) == 1
                label = option.find('label').text.strip()
                input = option.find('input')
                try:
                    if input.attrs['checked'] == 'checked':
                        option_choices.append((group_title, label))
                except KeyError:
                    pass
                optionid, optionval = input.attrs['id'].split("-")

                choices.append((label, optionval))
            options.append((group_title, choices, optionid))
        for choices in itertools.product(*[option[1] for option in options]):
            combination = {options[i][2]: choice[1] for i, choice in enumerate(choices)}
            add_url(choice_lookup(choice_lookup_url, combination))
    except AttributeError as e:
        pass # engir variantar

    option_choices = dict(option_choices) 
    props = dict(props)

    props = {x: " - ".join([z for y, z in option_choices.items() if x == y] + [z for y, z in props.items() if x == y]) for x in set(list(option_choices.keys()) + list(props.keys()))}
    print(f"  > Found product {title} SKU {sku} price {price}")
    print(f"    >> Props: {dict(props)}")
    print(f"    >> Options: {dict(option_choices)}")
    return {'url': url, 'title': title, 'sku': sku, 'price': price, 'props': list(props.items())}

def add_url(url):
    if url is None:
        return
    if "/en/" not in url:
        return
    if url in visited_urls:
        return
    if not url.startswith(base):
        return
    if "lupine-shop.com/media" in url:
        return
    if url.endswith("pdf"):
        return
    if "anfrage-formular" in url:
        return
    if "en/payment" in url:
        return
    if "en/checkout" in url:
        return
    if url in to_visit_urls:
        return
    if url.endswith("payment"):
        return
    for i in ("en/widgets", "en/account", "en/Information", "b2b/en"):
        if i in url:
            return

    print(f"Adding {url} to visit list")
    to_visit_urls.add(url)


choices_looked_up = set()
def choice_lookup(url, choices):
    parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(parts[4]))
    query.update({'options': json.dumps(choices)})
    parts[4] = urlencode(query)
    new_url = urlparse.urlunparse(parts)
    if new_url in choices_looked_up:
        return None
    else:
        choices_looked_up.add(new_url) 
        return session.get(url, data={'options': json.dumps(choices)}).json()['url']


def visit(url):
    visited_urls.add(url)
    urlp = urlparse.urlparse(url)
    r = session.get(url)
    s = BeautifulSoup(r.text,"html.parser")

    listing = s.find_all(attrs={'class': 'cms-element-product-listing'})
    products = s.find_all(attrs={'class': 'product-box'})
    print(f"{url} listing={len(listing)}, products={len(products)}")

    # Skelli ollum urlum a sidunni i heimsoknarlistann
    for i in s.find_all("a"):
        try:
            href = i.attrs['href'] 
            if href.startswith("/"):
                href = base + href
            add_url(href)
        except KeyError as e:
            print(f"Error {e}")

    if len(listing) > 0:
        # Thetta er listing sida
        print(f'Listing site {url}')

        try:
            if 'disabled' not in s.find('li', attrs={'class': 'page-next'}).find('input').attrs:
                # Thad er active next linkur
                p = s.find('li', attrs={'class': 'page-next'}).find('input').attrs["value"]
                add_url(urlp._replace(query=f'p={p}').geturl())
            else:
                print(f"Not visiting additional pages of listing")
        except AttributeError:
            print(f"Not visiting additional pages of listing")
    else:
        print(f'Product url {url}')
        product = get_product_details(url, r.text)
        if product is not None:
            assert product['sku'] is not None
            product_dict[product['sku']] = product


def main(listing_id):
    i = 0
    while len(to_visit_urls) > 0:
        url = to_visit_urls.pop()
        visit(url)
        print(f"Visited {len(visited_urls):5d} to visit {len(to_visit_urls):5d}")
        i += 1

    for sku, url in validate_list:
        if sku not in product_dict.keys():
            print(f"SKU {sku} visited only via strange url {url}")

    saved = 0 
    for i in product_dict.values():
        try:
            print(f"Saving {i['sku']:8s} {i['title']} {i['price']} {i['url']}")
            cur.execute(f"INSERT INTO items (listing_id, item_name, vendor_id, vendor_url, price) VALUES ({listing_id}, %s, %s, %s, %s) RETURNING id", (i['title'], i['sku'], i['url'], i['price']))
            item_id = cur.fetchone()

            for prop, val in i['props']:
                cur.execute("INSERT INTO item_properties (item_id, original, adjusted, value) VALUES (%s, %s, %s, %s)", (item_id, prop, prop, val))
            conn.commit()
            saved += 1
        except Exception as e:
            print(e)
            import pdb; pdb.set_trace()
    print(f"Saved {saved} items to database")


if __name__ == "__main__":
    assert len(sys.argv) > 1, "Missing listing id"
    main(int(sys.argv[1]))
