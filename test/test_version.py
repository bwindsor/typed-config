import re
from typedconfig import __version__


def test_version_tuple():
    assert type(__version__.VERSION) is tuple
    assert len(__version__.VERSION) == 3
    for version_part in __version__.VERSION:
        assert type(version_part) is int
        assert version_part >= 0


def test_version_string():
    assert re.match(r"[0-9]+\.[0-9]+\.[0-9]+", __version__.__version__)
