import time
from threading import Thread

from flask import current_app as app
from flask import redirect, render_template, flash, url_for

from itsdangerous import SignatureExpired, BadSignature
from email_validator import validate_email, EmailNotValidError


import invite0.config as conf
from invite0 import data
from invite0.forms import SignUpForm, InviteForm, BulkInviteForm, ProfileForm
from invite0.tokens import generate_token, read_token
from invite0.auth0.admin import user_exists, create_user
from invite0.auth0.session import (
    current_user,
    login_redirect, handle_login_callback, logout_redirect,
    requires_login, requires_permission,
)
from invite0.auth0.exceptions import (
    PasswordStrengthError,
    PasswordNoUserInfoError,
    UserAlreadyExistsError,
)
from invite0.mail import (
    send_invite,
    send_invite_bulk,
    notify_bulk_invite_success,
    notify_bulk_invite_failure
)


@app.route('/login')
def login():
    return login_redirect()


@app.route('/login_callback')
def login_callback():
    login_destination = handle_login_callback() or '/my-account'
    return redirect(login_destination)


@app.route('/logout')
def logout():
    return logout_redirect()


@app.route('/my-account')
@requires_login
def my_account():
    labels = {
        field: attrs['label']
        for field, attrs in data.ALL_USER_FIELDS.items()
    }
    return render_template(
        'my-account.html',
        profile=current_user.profile,
        labels=labels,
    )


@app.route('/my-account/edit', methods=['GET', 'POST'])
@requires_login
def my_account_edit():
    # TODO: handle 400's from Auth0 gracefully
    form = ProfileForm(data=current_user.profile)
    if form.validate_on_submit():
        profile = {field: form.data[field] for field in conf.USER_FIELDS}
        current_user.update_profile(profile)
        return redirect('/my-account')
    return render_template('my-account-edit.html', form=form)


@app.route('/password-reset')
@requires_login
def password_reset():
    current_user.send_password_reset_email()
    email_address = current_user.profile['email']
    flash(f'Password reset link sent to {email_address}.', 'is-info')
    return redirect('/my-account')


def _check_bulk_addresses(email_addresses):
    """
    Validate multiple email addresses (helper for /admin)

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


def _do_bulk_invite(email_addresses, inviter_email, app_obj):
    """ Send invites to multiple email addresses (helper for /admin) """
    with app_obj.app_context():
        try:
            skipped_cnt = 0
            recipients = []
            for email_address in email_addresses:
                if user_exists(email_address):
                    skipped_cnt += 1
                else:
                    recipients.append(email_address)
                # Auth0 free tier rate limits the Management API to 2 requests/second.
                # This avoids that with some wiggle room.
                time.sleep(1)  # seconds

            tasks = []
            for email_address in recipients:
                token = generate_token(email_address)
                link = url_for('signup', token=token, _external=True)
                tasks.append((email_address, link))
            send_invite_bulk(tasks)
        except:
            app.logger.exception('Error during bulk invite operation')
            notify_bulk_invite_failure(inviter_email)
        else:
            notify_bulk_invite_success(inviter_email, len(recipients), skipped_cnt)
            app.logger.info('Bulk invite job completed successfully')


@app.route('/admin', methods=['GET', 'POST'])
@requires_login
@requires_permission(conf.INVITE_PERMISSION)
def admin():

    single_form = InviteForm()
    if single_form.submit_single.data and single_form.validate_on_submit():
        email_address = single_form.email.data
        if user_exists(email_address):
            flash('An account already exists for this email address.', 'is-danger')
        else:
            token = generate_token(email_address)
            link = url_for('signup', token=token, _external=True)
            send_invite(email_address, link)
            flash(f'Invitation sent to {email_address}!', 'is-success')

    bulk_form = BulkInviteForm()
    if bulk_form.submit_bulk.data and bulk_form.validate_on_submit():
        email_addresses = bulk_form.emails.data.replace(',', ' ').split()
        bad_address = _check_bulk_addresses(email_addresses)
        if bad_address is None:
            thread = Thread(target=_do_bulk_invite, args=[
                email_addresses,
                current_user.profile['email'], 
                app._get_current_object()
            ])
            thread.start()
            flash('Bulk invite job initiated. You will recieve an email at '
                  f'{current_user.profile["email"]} when it is complete.', 'is-success')
        else:
            flash(f'{bad_address} is not a valid email address. '
                   'Please correct or remove this value and try again.', 'is-danger')

    return render_template('admin.html', single_form=single_form, bulk_form=bulk_form)


@app.route('/signup/<token>', methods=['GET', 'POST'])
def signup(token):
    def error_page(message):
        return render_template('error.html', message=message)
    try:
        email_address = read_token(token)
    except SignatureExpired:
        app.logger.info('Recieved expired invitation token')
        return error_page('This link has expired. Please request a new invitation link.')
    except BadSignature:
        app.logger.warning('Recieved invalid invitation token')
        return error_page('invalid signup link')

    form = SignUpForm()
    if form.validate_on_submit():
        try:
            create_user(email_address, password=form.password.data)
        except PasswordStrengthError:
            flash('Password too weak!', 'is-danger')
        except PasswordNoUserInfoError:
            flash('Password must not contain user information (eg email/username).', 'is-danger')
        except UserAlreadyExistsError:
            flash('An account already exists for your email address.', 'is-danger')
            # TODO: password reset link
        except Exception as e:
            flash('An unknown error occured.', 'is-danger')

        app.logger.info(f'Created account for {email_address}')
        flash('Account created!', 'is-success')

        if conf.WELCOME_URL:
            return redirect(conf.WELCOME_URL)
        else:
            return redirect('/my-account')

    return render_template(
        'signup.html',
        form=form,
        show_logout_button=False,
    )
