# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests for the Hockeypuck charm."""

import typing
from unittest import mock

import ops
import paas_charm.go
import pytest
import requests
from ops import testing

import charm

ADMIN_FINGERPRINT = "A" * 40


def _set_status(status: ops.StatusBase) -> typing.Callable[..., None]:
    """Create a replacement for the framework reconcile that sets a status.

    Args:
        status: The status to set.

    Returns:
        The replacement reconcile.
    """

    def reconcile(self: ops.CharmBase, *_args: typing.Any, **_kwargs: typing.Any) -> None:
        """Set the status."""
        self.unit.status = status

    return reconcile


@pytest.fixture(name="admin_gpg")
def admin_gpg_fixture():
    """Mock AdminGPG.

    Yields:
        The mocked AdminGPG class.
    """
    with mock.patch("charm.AdminGPG") as admin_gpg_cls:
        admin_gpg_cls.return_value.admin_fingerprint.return_value = ADMIN_FINGERPRINT
        yield admin_gpg_cls


@pytest.fixture(name="state")
def state_fixture() -> testing.State:
    """Create a leader state with a connectable workload container.

    Returns:
        The state.
    """
    return testing.State(leader=True, containers=[testing.Container("app", can_connect=True)])


def test_admin_key_pushed_after_reconcile(context, state, admin_gpg, monkeypatch):
    """
    arrange: a charm whose framework reconcile leaves the unit active.
    act: run the config-changed event.
    assert: the admin key is pushed and the unit is active.
    """
    monkeypatch.setattr(paas_charm.go.Charm, "_reconcile", _set_status(ops.ActiveStatus()))

    state_out = context.run(context.on.config_changed(), state)

    admin_gpg.return_value.push_admin_key.assert_called_once_with()
    assert state_out.unit_status == testing.ActiveStatus()


@pytest.mark.parametrize(
    "status",
    [
        testing.BlockedStatus("blocked"),
        testing.WaitingStatus("waiting"),
        testing.MaintenanceStatus("busy"),
    ],
)
def test_admin_key_not_pushed_when_not_active(context, state, admin_gpg, monkeypatch, status):
    """
    arrange: a charm whose framework reconcile leaves the unit in a non-active status.
    act: run the config-changed event.
    assert: the admin key is not pushed and the status is kept.
    """
    monkeypatch.setattr(paas_charm.go.Charm, "_reconcile", _set_status(status))

    state_out = context.run(context.on.config_changed(), state)

    admin_gpg.return_value.push_admin_key.assert_not_called()
    assert state_out.unit_status == status


def test_admin_key_push_failure_is_raised(context, state, admin_gpg, monkeypatch, caplog):
    """
    arrange: a charm for which pushing the admin key fails.
    act: run the config-changed event.
    assert: the error is logged and the hook fails.
    """
    monkeypatch.setattr(paas_charm.go.Charm, "_reconcile", _set_status(ops.ActiveStatus()))
    admin_gpg.return_value.push_admin_key.side_effect = requests.ConnectionError("refused")

    with pytest.raises(testing.errors.UncaughtCharmError, match="ConnectionError"):
        context.run(context.on.config_changed(), state)

    assert "Unable to push admin key to Hockeypuck" in caplog.text


@pytest.mark.parametrize(
    "user_keys, expected",
    [
        pytest.param(None, ADMIN_FINGERPRINT, id="no user keys"),
        pytest.param("BBBB,CCCC", f"BBBB,CCCC,{ADMIN_FINGERPRINT}", id="user keys"),
        pytest.param("BBBB,", f"BBBB,{ADMIN_FINGERPRINT}", id="trailing comma"),
    ],
)
def test_admin_keys_include_admin_fingerprint(context, admin_gpg, user_keys, expected):
    """
    arrange: a charm with or without user defined admin keys.
    act: create the charm state.
    assert: the admin fingerprint is appended to the admin keys.
    """
    del admin_gpg
    config = {} if user_keys is None else {"admin-keys": user_keys}
    state = testing.State(
        leader=True,
        config=config,
        containers=[testing.Container("app", can_connect=True)],
    )

    with context(context.on.config_changed(), state) as manager:
        charm_state = manager.charm._create_charm_state()  # pylint: disable=protected-access

    assert charm_state.user_defined_config["admin_keys"] == expected


def test_multi_unit_deployment_is_blocked(context):
    """
    arrange: a charm planned with two units.
    act: run the config-changed event.
    assert: the unit is blocked.
    """
    state = testing.State(
        leader=True,
        planned_units=2,
        containers=[testing.Container("app", can_connect=True)],
    )

    state_out = context.run(context.on.config_changed(), state)

    assert state_out.unit_status == testing.BlockedStatus(
        "Hockeypuck does not support multi-unit deployments"
    )


def test_lookup_key_returns_key(context, state, monkeypatch):
    """
    arrange: a ready charm and a keyserver that knows the key.
    act: run the lookup-key action, which requires the actions observer to be alive.
    assert: the key is returned.
    """
    monkeypatch.setattr(charm.HockeypuckK8SCharm, "is_ready", lambda _: True)
    response = requests.Response()
    response.status_code = 200
    response._content = b"PUBLIC KEY"  # pylint: disable=protected-access
    get = mock.MagicMock(return_value=response)
    monkeypatch.setattr(requests, "get", get)

    context.run(context.on.action("lookup-key", params={"keyword": "alice"}), state)

    get.assert_called_once_with(
        "http://127.0.0.1:11371/pks/lookup?op=get&search=alice", timeout=20
    )
    assert context.action_results == {"result": "PUBLIC KEY"}
