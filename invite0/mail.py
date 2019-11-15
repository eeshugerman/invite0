from flask import render_template, current_app as app
from flask_mail import Mail, Message

from invite0 import config as conf


_mail = Mail(app)


def send_invite(email_address, link):
    if conf.MAIL_SENDER_NAME:
        sender = (conf.MAIL_SENDER_NAME, conf.MAIL_SENDER_ADDRESS)
    else:
        sender = conf.MAIL_SENDER_ADDRESS

    message = Message(
        subject=f'{conf.ORG_NAME} - Sign Up',
        sender=sender,
        recipients=[email_address],
        html=render_template('invitation.html', invite_link=link)
    )
    _mail.send(message)
    app.logger.info(f'Sent invitation to {email_address}!')
