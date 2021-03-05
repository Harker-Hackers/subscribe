import flask
import rockset
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from jinja2 import Template
from random import randint

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
            'code': ver_code
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
    ver_code = randint(1, 10000)
    send_mail(email, ver_code)

    res = rs.sql(
        rockset.Q(
            'harker_hackers.emails'
        ).where(
            rockset.F['_id'] == email
        ).select(
            '*'
        )
    )

    if res != []:
        return('Already subbed')
    else:
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

@app.route('/authorized/<ver_code>')
def verify(ver_code):
    res = rs.sql(
        rockset.Q(
            'select _id from harker_hackers.emails where code={}'.format(
                ver_code
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