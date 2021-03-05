import flask
import rockset
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from jinja2 import Template
from shortuuid import uuid

def send_mail(address, ver_code):
    sender_email = os.getenv('EMAIL_EMAIL')
    receiver_email = address
    password = os.getenv('EMAIL_PW')

    message = MIMEMultipart('alternative')
    message['Subject'] = 'Harker Hackers Subscription'
    message['From'] = sender_email
    message['To'] = receiver_email

    body = Template(
            open(
                'verification.jinja', 
                'r'
            ).read()
        ).render({
            'code': ver_code,
            'email': address
        })

    message.attach(
        MIMEText(
            body,
            'html'
        )
    )
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )

app = flask.Flask(__name__)
rs = rockset.Client(
    api_key=os.getenv('RS2_TOKEN'), 
    api_server='api.rs2.usw2.rockset.com'
)
collection = rs.Collection.retrieve(
    'emails', 
    workspace='harker_hackers'
)

@app.route('/')
def login():
    return(
        flask.render_template(
            'index.jinja'
        )
    )

@app.route('/authorized')
def after():
    email = flask.request.args.get('email')
    ver_code = uuid()

    res = list(
            rs.sql(
            rockset.Q(
                'harker_hackers.emails'
            ).where(
                rockset.F['_id'] == email
            ).select('*')
        )
    )

    if res == []:
        send_mail(email, ver_code)
        print(
            collection.add_docs([{
                '_id': email,
                'verified': False,
                'code': ver_code
            }])
        )

        return(
            flask.render_template(
                'please_verify.jinja',
                email=email
            )
        )

    else:
        print(res)
        return('Already subbed')

@app.route('/authorized/<ver_code>/<ver_email>')
def verify(ver_code, ver_email):
    res = rs.sql(
        rockset.Q(
            'select _id from harker_hackers.emails where code={} and _id=\'{}\''.format(
                ver_code,
                ver_email
            )
        )
    )
    email = res[0]['_id']

    if res != []:
        collection.add_docs([{
            '_id': email,
            'verified': True,
        }])
        return(
            flask.render_template(
                'verified.jinja',
                email=email
            )
        )
    else:
        return('Email not found')

if __name__ == '__main__':
    app.run()