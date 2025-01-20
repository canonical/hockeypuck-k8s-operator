# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for hockeypuck-k8s tests."""

import pytest


def pytest_addoption(parser: pytest.Parser):
    """Parse additional pytest options.

    Args:
        parser: Pytest parser.
    """
    # The prebuilt charm file.
    parser.addoption("--charm-file", action="store", default="")
    # The Hockeypuck image name:tag.
    parser.addoption("--hockeypuck-image", action="store", default="")
    # The path to kubernetes config.
