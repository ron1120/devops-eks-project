"""Widen collection to all suites only when appropriate — never for explicit paths like engine/tests-engine/unit/."""

from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SUITES = (_ROOT / "unit", _ROOT / "integration", _ROOT / "e2e")


def _should_keep_single_suite_only(arg: str, resolved: Path) -> bool:
    """True → do not expand (e.g. Jenkins: engine/tests-engine/unit/, or pytest /abs/.../unit from another cwd)."""
    if resolved not in _SUITES or not resolved.is_dir():
        return False
    parts = Path(arg).as_posix().split("/")
    if len(parts) >= 3 and parts[0] == "engine" and parts[1] == "tests-engine":
        return True
    if Path(arg).is_absolute() and Path.cwd().resolve() != resolved:
        return True
    return False


def pytest_configure(config):
    args = list(config.args)
    if len(args) == 1:
        resolved = Path(args[0]).expanduser().resolve()
        if resolved.is_dir() and resolved in _SUITES:
            if not _should_keep_single_suite_only(args[0], resolved):
                config.args = [str(p) for p in sorted(_SUITES, key=lambda x: x.name)]
            return
    if args and args != ["."]:
        return
    cwd = Path.cwd().resolve()
    under_root = cwd == _ROOT or _ROOT in cwd.parents
    if not under_root:
        return
    if cwd == _ROOT or (cwd.name in ("unit", "integration", "e2e") and cwd.parent == _ROOT):
        config.args = [str(p) for p in sorted(_SUITES, key=lambda x: x.name)]
