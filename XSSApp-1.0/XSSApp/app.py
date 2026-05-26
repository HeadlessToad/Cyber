from http import HTTPStatus

import flask
import hashlib
import base64
import os
import jinja2
import logging

from . import validation_utilities
from .validation_utilities import generate_regex_validator

from flask import Flask
app = Flask(__name__, template_folder="templates", static_folder="static")


def generate_random_key():
    RANDOM_SIZE = 16
    return base64.b64encode(os.urandom(RANDOM_SIZE))


messages = []

# Top secret value! Nobody knows this value and shall never know!
VERY_SECRET_PASSWORD = "55ce7573ece627be0140648f5e403121"


VALIDATORS = {
    "name": generate_regex_validator(validation_utilities.NAME_REGEX, "name"),
    "phone_number": generate_regex_validator(validation_utilities.PHONE_REGEX, "phone number"),
    "email": generate_regex_validator(validation_utilities.MAIL_REGEX, "mail address"),
    "message": validation_utilities.validate_message,
}


IS_ADMIN_KEY = 'is_admin'
CSRF_TOKEN_KEY = 'csrf_token'


def is_administrator_logged_in():
    return IS_ADMIN_KEY in flask.session and flask.session[IS_ADMIN_KEY]


def attempt_admin_login():
    sent_password = flask.request.args.get("password", None)
    if sent_password and test_administrator_password(sent_password):
        app.logger.info("Administrator logged in successfully!")
        flask.session[IS_ADMIN_KEY] = True
        return True
    return False


def get_or_set_csrf_token():
    if CSRF_TOKEN_KEY not in flask.session:
        csrf_value = generate_random_key().decode()
        flask.session[CSRF_TOKEN_KEY] = csrf_value
    else:
        csrf_value = flask.session[CSRF_TOKEN_KEY]
    return csrf_value


def add_message(args: dict):
    required_args = ["name", "phone_number", "email", "subject", "message"]
    result = {name: args.get(name) for name in required_args}
    for validator_name, validator in VALIDATORS.items():
        if validator_name in result:
            validator(result[validator_name])
    result["message"] = jinja2.Markup(result["message"])
    if is_administrator_logged_in():
        result["name"] = result["name"] + " (Administrator)"

    messages.append(result)


def test_administrator_password(password: str):
    password = password.encode("utf-8")
    hasher = hashlib.sha256(password)
    return base64.b64encode(hasher.digest()) == b"0zhVv4LkMDBMht0Qh3OPEDah7xVllG7j1Z1DPCQK7qk="


@ app.route('/')
def index():
    is_admin = is_administrator_logged_in()
    resp = flask.Response()
    resp.set_data(flask.render_template(
        "index.html", messages=messages, csrf_value=get_or_set_csrf_token(), is_admin=is_admin))
    resp.calculate_content_length()
    return resp


@app.route("/login", methods=["GET"])
def login():
    attempt_admin_login()
    return flask.redirect('/')


@app.route("/drop_all_messages")
def drop_all_messages():
    if is_administrator_logged_in():
        messages.clear()
    return flask.redirect('/')


@app.route("/logout")
def logout():
    flask.session[IS_ADMIN_KEY] = False
    return flask.redirect('/')


@app.route('/request', methods=['POST'])
def handle_request():
    sent_token = flask.request.form.get(CSRF_TOKEN_KEY)
    actual_token = flask.session.get(CSRF_TOKEN_KEY, None)
    if sent_token != actual_token:
        app.logger.error(
            "Bad request - invalid csrf token (%s != %s)", sent_token, actual_token)
        return flask.Response(
            response="Invalid token", status=HTTPStatus.UNAUTHORIZED)
    try:
        add_message(flask.request.form)
    except ValueError as e:
        app.logger.error(
            "Bad request - invalid content (%s)", e.args[0])
        return flask.Response(
            response=e.args[0], status=HTTPStatus.BAD_REQUEST)

    return flask.redirect('/')


@app.route('/favicon.ico')
def get_icon():
    return app.send_static_file('favicon.ico')


def start_app():
    secret_key = generate_random_key()
    app.logger.setLevel(logging.INFO)
    app.logger.info("App secret key: %s", base64.b64encode(secret_key))
    app.secret_key = secret_key
    app.config["SESSION_COOKIE_HTTPONLY"] = False

    app.run(host="0.0.0.0")


if __name__ == "__main__":
    start_app()
