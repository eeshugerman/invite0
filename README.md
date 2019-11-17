# Overview
## What is it?
Invite0 is a small web app which augments the popular [Auth0](https://auth0.com) service, providing code-free support for "invite only" tenants.

## The problem
By default, your Auth0 tenant is open for signup to anyone on the web. This may or may not be what you want; let's suppose it's not. Fortunately, signups can be easily disabled in the UI. Cool! But now... how do you add users? You might hope that invitation links could be sent to email addresses from the UI, but unfortunately Auth0 does not support this out-of-the-box. Rather, your options are:

  1. create users manually in the UI and by some means send credentials to new users (yuck!)
  2. handle user creation in your application code via the Management API

(1) poses glaring problems for security and scalability. (2) may be a fine option _if you're developing an application_ -- but what if you are simply integrating software that you do not develop? This is where Invite0 comes in to play.

## The solution
Invite0 is two web pages:
- `/admin`: From this page, Auth0 users with a certain permission can send invitations to email addresses.
- `/signup/<token>`: This is where the recipients land when they click the invitation link. It's a basic form: password and password confirmation. (Support is planned for additional fields, eg `name` and `picture`.)

`token` is a JSON Web Token (JWT) which encodes the user's email address and the current time in a signed, url-safe string. When the admin clicks `Send`, the user's invite link, `https://<domain>/signup/<token>`, is emailed to them. When the user follows the link, the `/signup` endpoint checks the token. Since the token is signed, we can verify that it was encoded with our `SECRET_KEY` (or in other words, that it has not been tampered with). From the token, we decode the email address and creation time, and check that it has not expired per `INVITE_EXPIRATION_DAYS`. Finally, when the user submits the password form, their account is created in Auth0 with the Mangement API.

This approach enables us to send single-use, temporary invite links, and verifies email address as part of the process, all without touching a database! Token encoding and decoding is handled by [`itsdangerous`](https://github.com/pallets/itsdangerous).

# Installation

### 1. Setup the API and Application in the Auth0 UI
#### 1. API
  1. `APIs` -> `Create API`
  2. Provide a name and identifier, click `Create`
  3. On the `Permissions` tab, add a `send:invitation` permission

#### 2. Application
  1. Click `Applications` -> `<API name from step 1.2> (Test Application)`
  2. _Optional_: remove `(Test Application)` from the application name, or rename as you see fit
  3. Add the allowed callback and logout URLs
    - allowed callback URL: `https://<your Invite0 domain>/login_callback`
    - allowed logout URL: `https://<your Invite0 domain>/logout`
    - for local testing, `<your Invite0 domain>` is `http://localhost:8000`
    - don't forget to click `Save Changes` at the bottom of the page!
  4. On the `APIs` tab, grant access to the Management API for the `read:users` and `create:users` permisssions

#### 3. Grant your user the `send:invitation` permission
  1. `Users & Roles` -> `Users` -> `<your email address>` -> `Permissions` -> `Assign Permissions`
  2. Select the `send:invitation` permission

#### 2. Create your `docker-compose.yml`
Here's an example of a minimal setup with Docker Compose:
```yaml
version: "3"

services:
  invite0:
    image: eeshugerman/invite0
    ports:
      - 8000:8000   # host:container
    environment:
      INVITE0_DOMAIN: <your Invite0 domain>    # localhost:8000 for local testing
      ORG_NAME: Your Organization
      SECRET_KEY: <long random string>

      # mail settings are passed directly to Flask-Mail -- see: https://pythonhosted.org/Flask-Mail
      MAIL_SERVER: smtp.gmail.com
      MAIL_PORT: 587
      MAIL_USE_TLS: 1
      MAIL_USERNAME: foo@gmail.com
      MAIL_PASSWORD: passw0rd
      MAIL_SENDER_ADDRESS: foo@gmail.com

      # you'll find these values in the settings page for the Application and API created in steps 1 and 2
      AUTH0_CLIENT_ID: <client ID>
      AUTH0_CLIENT_SECRET: <client secret>
      AUTH0_DOMAIN: <tenant>.auth0.com
      AUTH0_AUDIENCE: <audience>
```
#### 3. Run `docker-compose up`

### 4. Log in at `localhost:8000/admin`
# Configuration
## Environment variables
See available variables and their defaults in [config.py](invite0/config.py).

## Overriding default HTML and CSS
You can override the default HTML and CSS with bind-mounts:
```
services:
  invite0:
    volumes:
      - ./signup.html:/invite0/invite0/templates/signup.html    # just the signup page, or
      - ./templates/:/invite0/invite0/templates/                # all HTML including invite email
      - ./styles.css:/invite0/invite0/static/css/styles.css
```
Refer to the default HTML [here](invite0/templates).
