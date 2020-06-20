from flask import current_app as app
from flask import redirect, render_template, flash, url_for

from itsdangerous import SignatureExpired, BadSignature

import invite0.config as conf
from invite0 import data
from invite0.forms import SignUpForm, InviteForm, BulkInviteForm, ProfileForm
from invite0.tokens import generate_token, read_token
from invite0.auth0.admin import user_exists, create_user
from invite0.mail import send_invite, spawn_bulk_invite_job, verify_addresses
from invite0.auth0 import session
from invite0.auth0.session import current_user, requires_login, requires_permission
from invite0.auth0 import exceptions

@app.route('/')
def index():
    return redirect('/my-account')


@app.route('/login')
def login():
    return session.login_redirect()


@app.route('/login_callback')
def login_callback():
    login_destination = session.handle_login_callback()
    if not login_destination:
        # TODO: Use Flask error handling
        # https://flask.palletsprojects.com/en/1.1.x/errorhandling/#error-handlers
        return render_template('error.html', message="Sorry, I don't know where to direct you.")
    return redirect(login_destination)


@app.route('/logout')
def logout():
    return session.logout_redirect()


@app.route('/my-account')
@requires_login
def my_account():
    labels = {field: attrs['label'] for field, attrs in data.ALL_USER_FIELDS.items()}
    return render_template('my-account.html', profile=current_user.profile, labels=labels)


@app.route('/my-account/edit', methods=['GET', 'POST'])
@requires_login
def my_account_edit():
    # TODO: handle 400s from Auth0 gracefully
    form = ProfileForm(data=current_user.profile)
    if form.validate_on_submit():
        profile = {field: form.data[field] for field in conf.USER_FIELDS}
        try:
            current_user.profile = profile
        except exceptions.CanNotUnsetFieldError:
            flash("Sorry, this field can't be unset.", 'is-danger')
        else:
            return redirect('/my-account')
    return render_template('my-account-edit.html', form=form)


@app.route('/password-reset')
@requires_login
def password_reset():
    current_user.send_password_reset_email()
    email_address = current_user.profile['email']
    flash(f'Password reset link sent to {email_address}.', 'is-info')
    return redirect('/my-account')


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
            return redirect('/admin')

    bulk_form = BulkInviteForm()
    if bulk_form.submit_bulk.data and bulk_form.validate_on_submit():
        email_addresses = bulk_form.emails.data.replace(',', ' ').split()
        bad_address = verify_addresses(email_addresses)
        if bad_address:
            flash(f'{bad_address} is not a valid email address. '
                   'Please correct or remove this value and try again.', 'is-danger')
        else:
            inviter_email = current_user.profile['email']
            spawn_bulk_invite_job(email_addresses, inviter_email)

            flash(f'Bulk invite job initiated. You will recieve an email at {inviter_email} '
                   'when it is complete.', 'is-success')
            return redirect('/admin')

    return render_template('admin.html', single_form=single_form, bulk_form=bulk_form)


@app.route('/signup/<token>', methods=['GET', 'POST'])
def signup(token):
    def error_page(message):
        # TODO: Use Flask error handling
        # https://flask.palletsprojects.com/en/1.1.x/errorhandling/#error-handlers
        return render_template('error.html', message=message, hide_logout_button=True)
    try:
        email_address = read_token(token)
    except SignatureExpired:
        app.logger.info('Recieved expired invitation token')
        return error_page('This link has expired. Please request a new invitation link.')
    except BadSignature:
        app.logger.warning('Recieved invalid invitation token')
        return error_page("There's something wrong with this invitation link. Are you lost?")

    form = SignUpForm()
    if form.validate_on_submit():
        extras = {field: getattr(form, field).data for field in conf.REQUIRED_USER_FIELDS}
        try:
            create_user(email_address, password=form.password.data, **extras)
        except exceptions.PasswordStrengthError:
            flash('Password too weak!', 'is-danger')
        except exceptions.PasswordNoUserInfoError:
            flash('Password must not contain user information (eg email/username).', 'is-danger')
        except exceptions.UserAlreadyExistsError:
            flash('An account already exists for your email address.', 'is-danger')
            # TODO: password reset link
        except Exception as e:
            flash('An unknown error occured.', 'is-danger')
        else:
            flash('Account created!', 'is-success')
            if conf.WELCOME_URL:
                return redirect(conf.WELCOME_URL)
            else:
                return redirect('/my-account')

    return render_template(
        'signup.html',
        form=form,
        hide_logout_button=False,
    )
