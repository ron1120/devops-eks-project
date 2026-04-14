"""If pytest is started with no paths or only a suite directory (unit/integration/e2e), run all suites."""

from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SUITES = frozenset((_ROOT / "unit", _ROOT / "integration", _ROOT / "e2e"))


def pytest_configure(config):
    args = list(config.args)
    if not args or args == ["."]:
        config.args = [str(p) for p in sorted(_SUITES, key=lambda x: x.name)]
        return
    if len(args) != 1:
        return
    path = Path(args[0]).expanduser().resolve()
    if path.is_dir() and path in _SUITES:
        config.args = [str(p) for p in sorted(_SUITES, key=lambda x: x.name)]
