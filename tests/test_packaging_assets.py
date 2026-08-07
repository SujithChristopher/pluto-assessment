"""Standalone checks that the packaged build can find what it needs at runtime.

The mechanism artwork is the one non-Python file the guided GUI loads. It is
resolved differently in a PyInstaller build (unpacked under sys._MEIPASS) than
in a `uv run` launch (the source tree), and a wrong answer fails silently — the
ready screen just shows no picture. The spec's data entry and the resolver have
to agree on one location.

Run: uv run python tests/test_packaging_assets.py  ->  prints OK."""
import ast
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import plutofullassessdef as pfadef
from newgui.shell import MECH_IMAGES, assets_dir

_SPEC = (_ROOT / "plutoguidedassessment.spec").read_text(encoding="utf-8")


def test_the_spec_exists_and_builds_the_guided_entry_point():
    assert "newgui/main.py" in _SPEC, _SPEC[:400]
    assert "name='plutoguidedassessment'" in _SPEC, _SPEC[:400]


def test_the_spec_bundles_the_assets_where_the_resolver_looks():
    """assets_dir() returns <_MEIPASS>/assets, so the spec must place them in
    an 'assets' subdirectory, not at the bundle root."""
    assert "datas += [('assets', 'assets')]" in _SPEC, _SPEC


def test_every_mechanism_has_artwork_on_disk():
    """A missing PNG renders nothing and says nothing, so it would only be
    noticed by an operator mid-session."""
    for _mech in pfadef.MECHANISMS:
        assert _mech in MECH_IMAGES, _mech
        _img = _ROOT / "assets" / MECH_IMAGES[_mech]
        assert _img.exists(), _img
        assert _img.stat().st_size > 0, _img


def test_assets_resolve_to_the_source_tree_when_not_frozen():
    assert assets_dir() == _ROOT / "assets", assets_dir()
    for _name in set(MECH_IMAGES.values()):
        assert (assets_dir() / _name).exists(), _name


def test_assets_follow_meipass_in_a_frozen_build():
    """PyInstaller sets sys._MEIPASS to the extract dir; __file__ is not a
    reliable way back to the bundled data, so _MEIPASS must win."""
    _had = hasattr(sys, "_MEIPASS")
    _old = getattr(sys, "_MEIPASS", None)
    sys._MEIPASS = r"C:\frozen\extract"
    try:
        assert assets_dir() == pathlib.Path(r"C:\frozen\extract") / "assets", (
            assets_dir()
        )
    finally:
        if _had:
            sys._MEIPASS = _old
        else:
            del sys._MEIPASS
    # Back to the source tree once the flag is gone.
    assert assets_dir() == _ROOT / "assets", assets_dir()


def test_the_release_guard_blocks_on_debug_only():
    """DEBUG is baked into the archive and invisible from the exe, so the spec
    refuses to build with it on. MECHANISM_ORDER must NOT block a build on its
    own — newgui.sequencer ignores it unless DEBUG is on, so a leftover order
    cannot reach the shipped exe and blocking on it is pure friction."""
    assert 'getattr(_dbg, "DEBUG", False) and not _os.environ.get(' in _SPEC, _SPEC
    assert "PLUTO_ALLOW_DEBUG_BUILD" in _SPEC, _SPEC


def test_a_leftover_mechanism_order_cannot_reach_a_release_build():
    """The claim the guard relies on: with DEBUG off the override is inert."""
    import debugconfig
    from newgui.sequencer import ASSESSMENT_MECHANISMS, debug_mechanism_order, \
        mechanisms_for_mode

    _old = (debugconfig.DEBUG, debugconfig.MECHANISM_ORDER)
    debugconfig.DEBUG, debugconfig.MECHANISM_ORDER = False, ["HOC"]
    try:
        assert debug_mechanism_order() is None
        assert mechanisms_for_mode("assessment") == ASSESSMENT_MECHANISMS
    finally:
        debugconfig.DEBUG, debugconfig.MECHANISM_ORDER = _old


def test_the_spec_is_valid_python():
    """A syntax error only surfaces when someone tries to ship a build."""
    ast.parse(_SPEC)


if __name__ == "__main__":
    for _name, _fn in sorted(list(globals().items())):
        if _name.startswith("test_") and callable(_fn):
            _fn()
            print(f"  {_name} ok")
    print("OK")
