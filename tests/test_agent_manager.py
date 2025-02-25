import pytest
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.append(PARENT_DIR + "/code_base")

from agent_manager import AgentManager
import requests


@pytest.fixture
def agent_mgr():
    """Create a real AgentManager instance for live API calls."""
    return AgentManager()

def test_send_task_success(agent_mgr):
    """
    Test sending a basic prompt to the default agent and verifying
    we get a non-empty string. This requires LM Studio to be running.
    """
    response = agent_mgr.send_task("engineer", "Hello, can you summarize your capabilities?")
    assert isinstance(response, str), "Response should be a string"
    assert len(response.strip()) > 0, "Response should not be empty"

def test_send_task_timeout(agent_mgr):
    """
    We'll pass an extremely short timeout to see if we get a timeout error message.
    If the model is slow, we might see a '❌ Timeout: ...' in the result.
    """
    response = agent_mgr.send_task("architect", "This prompt might take a while", timeout=0.001)
    assert "Timeout:" in response or "❌" in response, "We expect a timeout error text if it doesn't respond fast enough"

def test_delegate_task_strict_format(agent_mgr):
    """
    Tests the 'delegate_task' that tries a stricter formatting approach if the first attempt fails.
    We'll mock the first attempt to be blank, second attempt to succeed, or we can do a real approach if the model is quick.
    """
    original_send_task = agent_mgr.send_task

    # We'll define a mock that returns an empty string first, then returns a code block second
    call_count = {"count": 0}
    def mock_send_task(agent, prompt, timeout=180):
        if call_count["count"] == 0:
            call_count["count"] += 1
            return ""  # blank => triggers second attempt
        else:
            return "```python\ndef example_function():\n    pass\n```"

    agent_mgr.send_task = mock_send_task
    response = agent_mgr.delegate_task("architect", "Write a function to do something.")
    assert "def example_function" in response, "Should get the second attempt code"

    # restore
    agent_mgr.send_task = original_send_task


def test_preprocessor(agent_mgr):
    """
    Testing the 'preprocess_ai_response' method. We'll pass some text and see if it re-formats it into code.
    Real or mock approach. If real, we see how the 'preprocessor' agent transforms it.
    """
    # If you want to do a real approach, ensure you have a 'preprocessor' agent in agent_manager
    # For now, let's do a quick test. If there's no real 'preprocessor' agent or it doesn't exist, we might see an API error.
    text = "Make a simple python function to greet"
    result = agent_mgr.preprocess_ai_response(text)
    # We can't be sure what the model returns, but let's do a minimal check
    assert "def" in result.lower() or "function" in result.lower(), "Should mention a function in code block"
