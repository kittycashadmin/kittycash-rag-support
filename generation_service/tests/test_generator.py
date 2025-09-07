import pytest
from generator import format_prompt, SYSTEM_RULES, Generator

def test_format_prompt_structure():
    context_blocks = [
        {"id": 1, "text": "Doc text 1"},
        {"id": 2, "text": "Doc text 2"}
    ]
    user_query = "What is the process timeline?"
    prompt = format_prompt(context_blocks, user_query)

    assert SYSTEM_RULES.strip() in prompt
    assert "[CONTEXT]" in prompt
    for block in context_blocks:
        assert f"[DOC {block['id']}]" in prompt
        assert block["text"] in prompt
    assert "[USER QUESTION]" in prompt
    assert user_query in prompt
    assert "[ASSISTANT RESPONSE]" in prompt

def test_generate_mock(monkeypatch):
    def fake_run(*args, **kwargs):
        class Result:
            returncode = 0
            stdout = b"Mock generated answer"
            stderr = b""
        return Result()

    gen = Generator()
    monkeypatch.setattr("subprocess.run", fake_run)

    prompt = "Sample prompt"
    output = gen.generate(prompt)
    assert output == "Mock generated answer"

def test_generate_raises(monkeypatch):
    def fake_run_error(*args, **kwargs):
        class Result:
            returncode = 1
            stdout = b""
            stderr = b"Error occurred"
        return Result()

    gen = Generator()
    monkeypatch.setattr("subprocess.run", fake_run_error)

    with pytest.raises(RuntimeError) as exc:
        gen.generate("Bad prompt")
    assert "LLM generation failed" in str(exc.value)
