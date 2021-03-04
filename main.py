import flask
import flask_login
import rockset
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_mail(address):
    sender_email = os.getenv('EMAIL_EMAIL')
    receiver_email = address
    password = os.getenv('EMAIL_PW')

    message = MIMEMultipart('alternative')
    message['Subject'] = 'Harker Hackers Subscription'
    message['From'] = sender_email
    message['To'] = receiver_email
    message.attach(
        MIMEText(
            open(
                'verification.html', 
                'r'
            ).read(), 
            'html'
        )
    )
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        print(sender_email)
        print(password)
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
def console():
    email = flask.request.args.get('email')
    send_mail(email)

    print(
        collection.add_docs([{
            '_id': email
        }])
    )
    return(
        flask.render_template(
            'authorized.jinja',
            email=email
        )
    )

if __name__ == '__main__':
    app.run()