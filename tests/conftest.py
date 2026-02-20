# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Additional pytest options for tests."""

from pytest import Parser


def pytest_addoption(parser: Parser) -> None:
    """Parse additional pytest options.

    Args:
        parser: Pytest parser.
    """
    parser.addoption(
        "--hockeypuck-image", action="store", help="Hockeypuck app image to be deployed"
    )
    parser.addoption("--charm-file", action="store", help="Charm file to be deployed")
    parser.addoption("--model", action="store", help="Juju model to use for testing")
    parser.addoption(
        "--use-existing",
        action="store_true",
        default=False,
        help="Use existing Juju model without tearing down",
    )
    parser.addoption(
        "--keep-models",
        action="store_true",
        default=False,
        help="Keep Juju models after tests",
    )
