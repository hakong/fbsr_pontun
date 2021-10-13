import sys
import itertools
import requests
import urllib.parse as urlparse

import bs4
from bs4 import BeautifulSoup
import psycopg2

conn = psycopg2.connect("dbname=fbsr_pontun user=fbsr_pontun host=127.0.0.1 password=''")
cur  = conn.cursor()

base = "https://www.lupine-shop.com"
base_path = "/en/"

visited_urls = set()
to_visit_urls = {'https://www.lupine-shop.com/en/new-in-the-shop/1842/sl-ax', }#base + base_path, }
to_visit_urls = {'https://www.lupine-shop.com/en/accessoires-and-parts/o-rings/1065/o-ring-neo/piko/piko-r', }#base + base_path, }
to_visit_urls = {'https://www.lupine-shop.com/en/led-lightsets/headlamps/1847/wilma-headlamp', }#base + base_path, }
to_visit_urls = {base + base_path, }
product_dict = {}

session = requests.Session()
response = session.get(base + "/en/csrftoken")
csrf_token = response.headers['x-csrf-token']
session.cookies.set_cookie(requests.cookies.create_cookie(domain='www.lupine-shop.com', name='__csrf_token-3', value=csrf_token))

def get_product_details(url, response):
    s = BeautifulSoup(response,"html.parser")

    try:
        price = float(s.find_all('meta', attrs={'itemprop': 'price'})[0].attrs['content'])
    except IndexError:
        price = None

    #try:
    #    delivery = s.find_all(attrs={'class': 'delivery--text'})[0].text.strip()
    #except IndexError:
    #    delivery = None

    try:
        sku = s.find_all('span', attrs={'itemprop': 'sku'})[0].text.strip()
    except IndexError:
        sku = None

    try:
        title = s.find_all('h1', attrs={'class': 'product--title'})[0].text.strip()
    except IndexError:
        title = None

    _props = s.find_all('li', attrs={'class': 'base-info--entry'})
    props = []
    for prop in _props:
        if 'entry--sku' in prop.attrs['class']:
            continue
        assert list(prop.children)[1].attrs['class'][0] == 'entry--label'  , list(prop.children)[1].attrs['class']
        assert list(prop.children)[3].attrs['class'][0] == 'entry--content', list(prop.children)[3].attrs['class'] 
        if list(prop.children)[1].text.strip().strip(':').lower() == "homepage":
            continue
        props.append((list(prop.children)[1].text.strip().strip(':'), list(prop.children)[3].text.strip()))

    confform = s.find_all(attrs={'class': 'configurator--form'})

    options = []
    if len(confform) > 0:
        assert len(confform) == 1
        assert confform[0]['method'] == 'post'
        label = None
        options = []
        for item in confform[0].children:
            if isinstance(item, bs4.element.NavigableString):
                continue
            if item.name == "p":
                label = item.text.strip().strip(":")
                continue
            if item.name == "div": # contains a select option
                choices = []
                for choice in list(item.children)[1]:
                    if isinstance(choice, bs4.element.NavigableString):
                        continue
                    choices.append({'value': choice.attrs['value'], 'text': choice.text.strip()})
                    if 'selected' in choice.attrs:
                        props.append((label, choice.text.strip()))
                options.append({
                    'label'    : label,
                    'form_name': list(item.children)[1].attrs['name'],
                    'choices'  : choices
                })

    print(f"  > Found product {title} SKU {sku} price {price} {dict(props)}")
    return {'url': url, 'title': title, 'sku': sku, 'price': price, 'props': props}, options

def visit(url):
    visited_urls.add(url)
    urlp = urlparse.urlparse(url)
    r = session.get(url)
    s = BeautifulSoup(r.text,"html.parser")

    listing = s.find_all(attrs={'class': 'listing--content'})
    products = s.find_all(attrs={'class': 'product--box'})
    print(f"{url} listing={len(listing)}, products={len(products)}")

    for i in s.find_all("a"):
        try:
            if "href" not in i.attrs:
                print(i)
                continue
            href = i.attrs['href'] 
            if href.startswith("/"):
                href = base + href
            if not href.startswith(base):
                continue
            if href in visited_urls:
                continue
            to_visit_urls.add(href)
        except KeyError as e:
            print(f"Error {e}")
            import pdb; pdb.set_trace()

    if len(listing) > 0:
        if urlparse.parse_qs(urlp.query).get('p', None) is None:
            assert urlp.query == ''
            to_visit_urls.add(urlp._replace(query='p=1').geturl())
            return
        elif urlparse.parse_qs(urlp.query).get('p', None) is not None:
            page = int(urlparse.parse_qs(urlp.query).get('p', None)[0])
            if len(products) > 0:
                to_visit_urls.add(urlp._replace(query=f'p={page+1}').geturl())
            else:
                print(f"Not visiting additional pages of listing since len(products)={len(products)}")
    else:
        product, options = get_product_details(url, r.text)
        product_dict[product['sku']] = product

        if len(options) > 0:
            for choices in itertools.product(*[x['choices'] for x in options]):
                form_data = {x['form_name']: choices[i]['value'] for i, x in enumerate(options)}
                form_data['__csrf_token'] = csrf_token
                xx = session.post(url, form_data, headers={'Referer': url})
                product, _options = get_product_details(url, session.post(url, form_data).text)
                product_dict[product['sku']] = product
                assert len(_options) == len(options)
                for i in range(len(_options)):
                    assert len(_options[i]['choices']) == len(options[i]['choices'])
                    for j in range(len(_options[i]['choices'])):
                        assert options[i]['choices'][j] == _options[i]['choices'][j]

    

def main(listing_id):
    i = 0
    while len(to_visit_urls) > 0:
        url = to_visit_urls.pop()
        visit(url)
        i += 1

        for url in to_visit_urls.copy():
            if "lupine-shop.com/media" in url or url.endswith("pdf") or "anfrage-formular" in url or "en/payment" in url or "en/checkout" in url:
                to_visit_urls.remove(url)

    saved = 0 
    for i in product_dict.values():
        if i['title'] is None:
            continue

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
