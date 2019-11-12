from flask import current_app as app
from flask import redirect, render_template, flash, url_for

from itsdangerous import SignatureExpired, BadSignature


import invite0.config as conf
from invite0.forms import SignUpForm, InviteForm
from invite0.mail import send_invite
from invite0.tokens import generate_token, read_token
from invite0.auth0.users import user_exists, create_user
from invite0.auth0.session import (
    login_redirect,
    handle_login_callback,
    logout_redirect,
    requires_auth,
    requires_permission
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
    handle_login_callback()
    return redirect('/admin')


@app.route('/logout')
def logout():
    return logout_redirect()


@app.route('/admin', methods=['GET', 'POST'])
@requires_auth
@requires_permission(conf.INVITE_PERMISSION)
def admin():
    form = InviteForm()
    if form.validate_on_submit():
        email_address = form.email.data
        if user_exists(email_address):
            # TODO: link for password reset?
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
    try:
        email_address = read_token(token)
    # TODO: proper error pages
    except SignatureExpired:
        app.logger.info('recieved expired invitation token')
        return 'Sorry, this link has expired. Please request a new invitation link.'
    except BadSignature:
        app.logger.warning('recieved invalid invitation token')
        return 'ERROR: invalid invitation token'

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
        except Exception:
            flash('An unknown error occured.')

        flash('Account created!')
        # TODO: redirect somewhere nice -- SSO dashboard extension?

    return render_template(
        'signup.html',
        form=form,
        email_address=email_address,
    )
