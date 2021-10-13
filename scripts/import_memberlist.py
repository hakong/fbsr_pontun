import sys
import pandas as pd
import itertools

import psycopg2

conn = psycopg2.connect("dbname=fbsr_pontun user=fbsr_pontun host=127.0.0.1 password=''")
cur  = conn.cursor()

def main(listing_id, filename):
    df = pd.read_csv(filename)

    saved, skipped, added = 0, 0, set()
    for idx, row in df.iterrows():
        name, email = row['Name'], row['Email']
        if "@" in str(email) and email not in added:
            cur.execute(f"INSERT INTO listing_members (listing_id, name, email) VALUES (%s, %s, %s)", (listing_id, name, email))
            added.add(email)
            saved += 1
        else:
            print(f"Skipping {name} / {email}")
            skipped += 1
    print(f"Saved {saved} skipped {skipped}")
    conn.commit()
    import pdb; pdb.set_trace()
    #        cur.execute(f"INSERT INTO items (listing_id, item_name, vendor_id, vendor_url, price) VALUES ({listing_id}, %s, %s, %s, %s) RETURNING id", (i['title'], i['sku'], i['url'], i['price']))
    #        item_id = cur.fetchone()

    #        for prop, val in i['props']:
    #            cur.execute("INSERT INTO item_properties (item_id, original, adjusted, value) VALUES (%s, %s, %s, %s)", (item_id, prop, prop, val))
    #        conn.commit()
    #        saved += 1
    #    except Exception as e:
    #        print(e)
    #        import pdb; pdb.set_trace()
    #print(f"Saved {saved} items to database")



if __name__ == "__main__":
    assert len(sys.argv) > 2, "Missing listing id or filename"
    main(int(sys.argv[1]), sys.argv[2])
