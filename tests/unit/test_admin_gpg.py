# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests for the admin GPG key push."""

from unittest import mock

import ops
import pytest
import requests
from ops import testing

import admin_gpg

NUM_TRIES = 3


class PushCharm(ops.CharmBase):
    """Charm that pushes the admin key on config-changed."""

    def __init__(self, framework: ops.Framework):
        """Construct.

        Args:
            framework: The ops framework.
        """
        super().__init__(framework)
        framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_config_changed(self, _: ops.ConfigChangedEvent) -> None:
        """Push the admin key."""
        admin_gpg.AdminGPG(self.model).push_admin_key(num_tries=NUM_TRIES)


@pytest.fixture(name="context")
def context_fixture() -> testing.Context:
    """Create a testing context for the push charm.

    Returns:
        The testing context.
    """
    return testing.Context(PushCharm, meta={"name": "push-charm"})


@pytest.fixture(name="state")
def state_fixture() -> testing.State:
    """Create a state holding the admin secret.

    Returns:
        The state.
    """
    secret = testing.Secret(
        tracked_content={"adminpublickey": "PUBKEY"}, label=admin_gpg.ADMIN_LABEL, owner="app"
    )
    return testing.State(leader=True, secrets=[secret])


@pytest.fixture(name="post", autouse=True)
def post_fixture(monkeypatch: pytest.MonkeyPatch) -> mock.MagicMock:
    """Mock gpg, the HTTP post and the retry sleep.

    Args:
        monkeypatch: The pytest monkeypatch fixture.

    Returns:
        The mocked requests.post.
    """
    post = mock.MagicMock()
    monkeypatch.setattr(admin_gpg.gnupg, "GPG", mock.MagicMock())
    monkeypatch.setattr(admin_gpg.requests, "post", post)
    monkeypatch.setattr(admin_gpg.time, "sleep", mock.MagicMock())
    return post


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


def test_push_admin_key_success(context, state, post):
    """
    arrange: a keyserver that accepts the key.
    act: push the admin key.
    assert: the public key is posted once.
    """
    post.return_value = _response(200)

    context.run(context.on.config_changed(), state)

    post.assert_called_once()
    assert post.call_args.kwargs["data"] == {"keytext": "PUBKEY"}


def test_push_admin_key_retries(context, state, post):
    """
    arrange: a keyserver that fails while starting and then accepts the key.
    act: push the admin key.
    assert: the push is retried until it succeeds.
    """
    post.side_effect = [requests.ConnectionError("refused"), _response(503), _response(200)]

    context.run(context.on.config_changed(), state)

    assert post.call_count == NUM_TRIES


@pytest.mark.parametrize(
    "outcome",
    [requests.ConnectionError("refused"), _response(500)],
    ids=["connection error", "http error"],
)
def test_push_admin_key_fails_after_all_attempts(context, state, post, outcome):
    """
    arrange: a keyserver that never accepts the key.
    act: push the admin key.
    assert: the error is raised after the last attempt, without a final sleep.
    """
    post.side_effect = [outcome] * NUM_TRIES

    with pytest.raises(testing.errors.UncaughtCharmError):
        context.run(context.on.config_changed(), state)

    assert post.call_count == NUM_TRIES
    assert admin_gpg.time.sleep.call_count == NUM_TRIES - 1


def test_push_admin_key_without_secret(context, post):
    """
    arrange: a model without the admin secret.
    act: push the admin key.
    assert: a runtime error is raised and nothing is posted.
    """
    with pytest.raises(testing.errors.UncaughtCharmError, match="Admin GPG key not found"):
        context.run(context.on.config_changed(), testing.State(leader=True))

    post.assert_not_called()
