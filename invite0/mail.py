import time
from threading import Thread

from flask import render_template, url_for, current_app as app
from flask_mail import Mail, Message

from email_validator import validate_email, EmailNotValidError

from invite0 import config as conf
from invite0.auth0.admin import user_exists
from invite0.tokens import generate_token


_mail = Mail(app)


def send_invite(email_address, link, _conn=_mail):
    if conf.MAIL_SENDER_NAME:
        sender = (conf.MAIL_SENDER_NAME, conf.MAIL_SENDER_ADDRESS)
    else:
        sender = conf.MAIL_SENDER_ADDRESS

    _conn.send(Message(
        subject=conf.INVITE_SUBJECT,
        sender=sender,
        recipients=[email_address],
        html=render_template('invitation.html', invite_link=link)
    ))
    app.logger.info(f'Invitation sent to {email_address}')


def verify_addresses(email_addresses):
    """
    Validate multiple email addresses (for bulk invites)

    :return: first invalid email address or None if all are valid
    """
    for email_address in email_addresses:
        try:
            # mimic wtforms.validators.Email
            # https://github.com/wtforms/wtforms/blob/master/src/wtforms/validators.py#L384-L389
            validate_email(
                email_address,
                check_deliverability=False,
                allow_smtputf8=True,
                allow_empty_local=False,
            )
        except EmailNotValidError:
            return email_address
    return None


def _send_bulk_invite(email_addresses):
    """Send invites to multiple email addresses"""
    skip_cnt = 0
    send_cnt = 0
    with _mail.connect() as conn:
        for email_address in email_addresses:
            if user_exists(email_address):
                skip_cnt += 1
            else:
                send_cnt += 1
                token = generate_token(email_address)
                link = url_for('signup', token=token, _external=True)
                send_invite(email_address, link, conn)

            # Auth0 free tier rate limits the Management API to 2 requests/second.
            # This avoids that with plenty of wiggle room.
            time.sleep(1)  # seconds
    return skip_cnt, send_cnt


def _send_bulk_invite_wrapper(email_addresses, inviter_email, app_obj):
    """Wraps `_send_bulk_invite`, adding error handling/reporting and the app context"""
    # necessary in order for `app.logger` to work because we're in a background thread
    with app_obj.app_context():
        try:
            # yes, could just inline `_send_bulk_invite` but the indentation gets out of hand
            skip_cnt, send_cnt = _send_bulk_invite(email_addresses)
        except:
            app.logger.exception('Error during bulk invite operation')
            _mail.send(Message(
                subject=f'{conf.ORG_NAME} | Oops! Your bulk invite job failed',
                sender=conf.MAIL_SENDER_ADDRESS,
                recipients=[inviter_email],
                html=f'Sorry about that! Please ask your system administrator to check the logs.'
            ))
        else:
            app.logger.info('Bulk invite job completed successfully')
            _mail.send(Message(
                subject=f'{conf.ORG_NAME} | Your bulk invite job is complete',
                sender=conf.MAIL_SENDER_ADDRESS,
                recipients=[inviter_email],
                html=f'invites sent: {send_cnt}, skipped (existing users): {skip_cnt}',
            ))

def spawn_bulk_invite_job(email_addresses, inviter_email):
    Thread(
        target=_send_bulk_invite_wrapper,
        args=[email_addresses, inviter_email, app._get_current_object()]
    ).start()
