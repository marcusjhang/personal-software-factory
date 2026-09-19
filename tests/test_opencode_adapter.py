from psf.adapters import common


def test_last_json():
    assert common.last_json('noise\n{"a": 1}') == {"a": 1}
    assert common.last_json("nothing") is None


def test_build_prompt_uses_factory_prompt():
    p = common.build_prompt({"role": "verify", "goal": "g",
                             "context": {"prompt": "CUSTOM VERIFY POLICY", "spec": {"title": "t"}}})
    assert "CUSTOM VERIFY POLICY" in p and "passed" in p and "Goal: g" in p


def test_implement_prompt_asks_for_summary():
    p = common.build_prompt({"role": "implement", "goal": "g", "context": {}})
    assert "SUMMARY:" in p and "IMPLEMENT" in p


def test_command_claude_and_opencode():
    c = common.command("claude", "do x", "/ws", "sonnet")
    assert c[0] == "claude" and "-p" in c and "acceptEdits" in c and c[-2:] == ["--model", "sonnet"]
    o = common.command("opencode", "do x", "/ws", "deepseek/deepseek-v4-pro")
    assert o[:3] == ["opencode", "run", "--dir"] and "deepseek/deepseek-v4-pro" in o and "--auto" in o


def test_unknown_harness_rejected():
    try:
        common.command("nope", "x", "/ws", None)
        assert False
    except ValueError:
        pass


def test_adapter_modules_import():
    from psf.adapters import claude, opencode  # noqa: F401
    assert hasattr(claude, "main_cli") and hasattr(opencode, "main_cli")
