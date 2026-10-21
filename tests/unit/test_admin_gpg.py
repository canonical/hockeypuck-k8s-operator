# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# pylint: disable=protected-access,redefined-outer-name

"""Unit tests for the admin GPG key push."""

from unittest import mock

import ops
import pytest
import requests

import admin_gpg


@pytest.fixture(name="gpg")
def gpg_fixture(monkeypatch: pytest.MonkeyPatch):
    """Create an AdminGPG with a stored admin secret and no sleeping.

    Args:
        monkeypatch: pytest monkeypatch fixture.

    Returns:
        The AdminGPG instance.
    """
    model = mock.MagicMock()
    model.get_secret.return_value.get_content.return_value = {"adminpublickey": "PUBKEY"}
    monkeypatch.setattr(admin_gpg.time, "sleep", mock.MagicMock())
    return admin_gpg.AdminGPG.__new__(admin_gpg.AdminGPG), model


def _response(status_code: int) -> requests.Response:
    """Build a response.

    Args:
        status_code: HTTP status code.

    Returns:
        The response.
    """
    response = requests.Response()
    response.status_code = status_code
    return response


def _push(gpg, **kwargs):
    """Push the admin key.

    Args:
        gpg: Fixture value.
        kwargs: Extra arguments for push_admin_key.
    """
    instance, model = gpg
    instance.model = model
    instance.push_admin_key(**kwargs)


def test_push_admin_key_success(gpg, monkeypatch):
    """
    arrange: a keyserver that accepts the key.
    act: push the admin key.
    assert: the public key is posted once.
    """
    post = mock.MagicMock(return_value=_response(200))
    monkeypatch.setattr(requests, "post", post)

    _push(gpg)

    post.assert_called_once()
    assert post.call_args.kwargs["data"] == {"keytext": "PUBKEY"}


def test_push_admin_key_retries_connection_errors(gpg, monkeypatch):
    """
    arrange: a keyserver that refuses connections while starting and then accepts the key.
    act: push the admin key.
    assert: the push is retried until it succeeds.
    """
    post = mock.MagicMock(
        side_effect=[requests.ConnectionError("refused"), _response(503), _response(200)]
    )
    monkeypatch.setattr(requests, "post", post)

    _push(gpg)

    assert post.call_count == 3


@pytest.mark.parametrize(
    "outcome",
    [requests.ConnectionError("refused"), _response(500)],
    ids=["connection error", "http error"],
)
def test_push_admin_key_raises_after_all_attempts(gpg, monkeypatch, outcome):
    """
    arrange: a keyserver that never accepts the key.
    act: push the admin key.
    assert: a request exception is raised after the last attempt, without a final sleep.
    """
    post = mock.MagicMock(side_effect=[outcome] * 3)
    monkeypatch.setattr(requests, "post", post)

    with pytest.raises(requests.RequestException):
        _push(gpg, num_tries=3)

    assert post.call_count == 3
    assert admin_gpg.time.sleep.call_count == 2


def test_push_admin_key_without_secret(gpg):
    """
    arrange: a model without the admin secret.
    act: push the admin key.
    assert: a runtime error is raised.
    """
    _, model = gpg
    model.get_secret.side_effect = ops.SecretNotFoundError("missing")

    with pytest.raises(RuntimeError):
        _push(gpg)
