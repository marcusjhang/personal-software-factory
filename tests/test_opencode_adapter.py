import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "psf_agent_opencode", Path(__file__).resolve().parents[1] / "scripts" / "psf_agent_opencode.py")
mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mod)


def test_last_json():
    assert mod.last_json('noise\n{"a": 1}') == {"a": 1}
    assert mod.last_json("nothing") is None


def test_build_prompt_uses_factory_prompt():
    p = mod.build_prompt({"role": "verify", "goal": "g",
                          "context": {"prompt": "CUSTOM VERIFY POLICY", "spec": {"title": "t"}}})
    assert "CUSTOM VERIFY POLICY" in p and "passed" in p and "Goal: g" in p


def test_implement_prompt_asks_for_summary():
    p = mod.build_prompt({"role": "implement", "goal": "g", "context": {}})
    assert "SUMMARY:" in p and "IMPLEMENT" in p
