import pickle
import time
import logging
import smtplib, ssl
from email.message import EmailMessage

logger = logging.getLogger(__name__)

from . import get_redis, app, get_db

def main():    
   
    first = True
    with app.app_context():
        r = get_redis()
        while True:
            _msg = r.rpop(app.config['REDIS_EMAIL_KEY'])
            
            if not first:
                if  _msg is None:
                    time.sleep(1)
                    continue
                else:
                    _msg = pickle.loads(_msg)
            first = False

            conn, cur = get_db()
            cur.execute("SELECT e.id, lm.email, e.subject, e.body FROM emails e INNER JOIN listing_members lm ON lm.id = e.listing_member_id WHERE sent IS NULL") 
            emails = cur.fetchall()
            if len(emails) == 0:
                continue

            context = ssl.create_default_context()
            s = smtplib.SMTP(app.config['SMTP_SERVER'])
            s.ehlo()
            s.starttls(context=context)
            s.ehlo()
            s.login(app.config['EMAIL_FROM'], app.config['SMTP_PASSWORD'])
            for email in emails:
                logger.warning(f"Sending message from {app.config['EMAIL_FROM']} to {email['email']} subject {email['subject']}")
                msg = EmailMessage()
                msg.set_content(email['body'])

                msg['Subject'] = email['subject']
                msg['From'] = app.config['EMAIL_FROM']
                msg['To'] = email['email']

                s.send_message(msg)
                cur.execute("UPDATE emails SET sent=current_timestamp WHERE id=%s", (email['id'], ))
                conn.commit()
            s.quit()

if __name__ == "__main__":
    main()
