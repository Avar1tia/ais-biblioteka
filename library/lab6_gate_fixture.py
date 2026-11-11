"""Isolated CI fixture for the static gate."""

import flask


def ruff_fixture():
    return lab6_intentionally_undefined


def bandit_fixture():
    flask.Flask.run(debug=True)
