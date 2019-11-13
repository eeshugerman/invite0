# What is it?
Invite0 is a small web app which augments the popular [Auth0](https://auth0.com) service, providing code-free support for "invite only" networks.

# The problem
By default, your Auth0 tenant is open for signup to anyone on the web. This may or may not be what you want; let's suppose it's not. Fortunately, signups can be easily disabled in the UI. Cool! But now... how do you add users? You might hope that invitation links could be sent to email addresses from the UI, but unfortunately Auth0 does not support this out-of-the-box. Rather, your options are:
1. create users manually in the UI and by some means send credentials to new users :wince:
2. handle user creation in your application code via the Management API 
  - a somewhat curious approach to this is documented [here](https://auth0.com/docs/design/creating-invite-only-applications)

(1) poses glaring problems for security and scalability. (2) may be a fine option _if you're developing an application_ -- but what if you are simply integrating software that you do not develop? This is where Invite0 comes in.

# The solution
Invite0 is basically two web pages:
- `/admin`: From this page, Auth0 users with a certain permission can send invites to email addresses.
- `/signup`: This is where the recipients land when they click the invite link. It is a basic form to create a password.

`token` is a JSON Web Token (JWT) which encodes the user's email address and the current time in a signed, url-safe string, when the admin clicks "Send"". The user's invite link, https://<domain>/signup/<token>, is emailed to them. When the user follows the link, the `/signup` endpoint recieves the token. Since the token is signed, we can verify that it was encoded with our `SECRET_KEY` / that it has not been tampered with. From the token, we decode the email address and creation time, and check that it has not expired (per `INVITE_EXPIRATION_DAYS`). Finally, when the user submits the password form, their account is created via the Mangement API.

This lets us send single-use, temporary invite links, and verifies email address as part of the process, all without touching a database! Token encoding and decoding is handled by [`itsdangerous`](https://github.com/pallets/itsdangerous).

# TODO:
## how to
### installation / docker / docker-compose
### override default html and/or css
