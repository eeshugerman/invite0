from flask import render_template, current_app as app
from flask_mail import Mail, Message

from invite0 import config as conf


_mail = Mail(app)


def send_invite(email_address, link, _conn=_mail):
    if conf.MAIL_SENDER_NAME:
        sender = (conf.MAIL_SENDER_NAME, conf.MAIL_SENDER_ADDRESS)
    else:
        sender = conf.MAIL_SENDER_ADDRESS

    message = Message(
        subject=conf.INVITE_SUBJECT,
        sender=sender,
        recipients=[email_address],
        html=render_template('invitation.html', invite_link=link)
    )
    _conn.send(message)
    app.logger.info(f'Invitation sent to {email_address}')


def send_invite_bulk(tasks):
    with _mail.connect() as conn:
        for email_address, link in tasks:
            send_invite(email_address, link, conn)


def notify_bulk_invite_success(inviter_email, invites_cnt, skipped_cnt):
    message = Message(
        subject=f'{conf.ORG_NAME} | Your bulk invite job is complete',
        sender=conf.MAIL_SENDER_ADDRESS,
        recipients=[inviter_email],
        html=f'invites sent: {invites_cnt}, skipped (existing users): {skipped_cnt}',
    )
    _mail.send(message)


def notify_bulk_invite_failure(inviter_email):
    message = Message(
        subject=f'{conf.ORG_NAME} | Oops! Your bulk invite job failed',
        sender=conf.MAIL_SENDER_ADDRESS,
        recipients=[inviter_email],
        html=f'Sorry about that! Please ask your system administrator to check the logs.'
    )
    _mail.send(message)
