from flask import Flask

app = Flask(__name__)
app.config.from_pyfile('config.py')

with app.app_context():
    import invite0.views  # noqa
