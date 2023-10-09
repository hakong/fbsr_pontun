import sys
import pandas as pd
import itertools

import psycopg2

# Fetch environment variables
dbname = os.environ.get('DB_NAME', 'fbsr_pontun')
user = os.environ.get('DB_USER', 'fbsr_pontun')
host = os.environ.get('DB_HOST', '127.0.0.1')
password = os.environ.get('DB_PASSWORD', '')

# Use the environment variables in the connection string
conn = psycopg2.connect(f"dbname={dbname} user={user} host={host} password={password}")

cur  = conn.cursor()

def main(listing_id, filename):
    df = pd.read_csv(filename)

    saved, skipped, added = 0, 0, set()
    for idx, row in df.iterrows():
        name, email, kt = row['Name'], row['Email'], row['Reference']
        if pd.isnull(kt) or len(kt) not in (10, 11):
            print(f"Skipping {name:30s} - kennitala skrytin <{kt}>")
            continue
        if "@" not in str(email) or email in added:
            print(f"Skipping {name:30s} - email vantar eda thegar skrad <{email}> <{kt}>")
            continue

        cur.execute(f"INSERT INTO listing_members (listing_id, name, email) VALUES (%s, %s, %s)", (listing_id, name, email))
        added.add(email)
        saved += 1
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
    assert len(sys.argv) > 2, "Usage import_memberlist.py <listing_id> <filename>"
    main(int(sys.argv[1]), sys.argv[2])
