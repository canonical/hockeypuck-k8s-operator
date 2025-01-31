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
