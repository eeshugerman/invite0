from flask import current_app as app
from flask import redirect, render_template, flash, url_for

from itsdangerous import SignatureExpired, BadSignature

import invite0.config as conf
from invite0 import data
from invite0.forms import SignUpForm, InviteForm, ProfileForm
from invite0.mail import send_invite
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


@app.route('/login')
def login():
    return login_redirect()


@app.route('/login_callback')
def login_callback():
    login_dest = handle_login_callback() or '/my-account'
    return redirect(login_dest)


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
        labels=labels
    )


@app.route('/my-account/edit', methods=['GET', 'POST'])
@requires_login
def my_account_edit():
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
    flash(f'Password reset link sent to {email_address}.')
    return redirect('/my-account')


@app.route('/admin', methods=['GET', 'POST'])
@requires_login
@requires_permission(conf.INVITE_PERMISSION)
def admin():
    form = InviteForm()
    if form.validate_on_submit():
        email_address = form.email.data
        if user_exists(email_address):
            flash('An account already exists for this email address.')
        else:
            token = generate_token(email_address)
            link = url_for('signup', token=token, _external=True)
            send_invite(email_address, link)
            flash(f'Invitation sent to {email_address}!')
            app.logger.info(f'invitation sent to {email_address}')

    return render_template('admin.html', form=form)


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
            flash('Password too weak!')
        except PasswordNoUserInfoError:
            flash('Password must not contain user information (eg email/username).')
        except UserAlreadyExistsError:
            flash('An account already exists for your email address.')
            # TODO: password reset link
        except Exception as e:
            flash('An unknown error occured.')
            app.logger.error(f'Failed to create account for {email_address}:', exc_info=e)

        flash('Account created!')
        app.logger.info(f'Created account for {email_address}')

        if conf.WELCOME_URL:
            return redirect(conf.WELCOME_URL)
        else:
            return redirect('/my-account')

    return render_template(
        'signup.html',
        form=form,
        email_address=email_address,
    )
