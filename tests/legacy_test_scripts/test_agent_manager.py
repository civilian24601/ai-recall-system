import pytest
import requests
from unittest.mock import patch, MagicMock

from code_base.agent_manager import AgentManager

@pytest.fixture
def agent_mgr():
    """Creates an AgentManager for test usage."""
    return AgentManager()

@patch("requests.post")
def test_send_task_success(mock_post, agent_mgr):
    """
    Scenario: normal success, 200 response with valid JSON content.
    """
    # Mock a standard completion response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": "Hello from AI!"}}
        ]
    }
    mock_post.return_value = mock_response

    result = agent_mgr.send_task("architect", "Test Prompt", timeout=30)
    assert result == "Hello from AI!", f"Expected 'Hello from AI!', got {result}"

@patch("requests.post", side_effect=requests.exceptions.Timeout)
def test_send_task_timeout(mock_post, agent_mgr):
    """
    Scenario: The request times out.
    """
    result = agent_mgr.send_task("engineer", "Timeout Prompt", timeout=10)
    assert "Timeout: engineer did not respond in 10 seconds" in result, \
        f"Expected timeout message, got {result}"

@patch("requests.post")
def test_send_task_http_error(mock_post, agent_mgr):
    """
    Scenario: The API returns a non-2xx status or fails with a RequestException.
    """
    mock_response = MagicMock()
    # Simulate an HTTP 500
    mock_response.raise_for_status.side_effect = requests.exceptions.RequestException("500 Internal Server Error")
    mock_post.return_value = mock_response

    result = agent_mgr.send_task("qa", "Error Prompt", timeout=20)
    assert "❌ API Error:" in result, f"Expected API Error message, got {result}"

@patch.object(AgentManager, "send_task")
def test_delegate_task_empty_response(mock_send_task, agent_mgr):
    """
    Scenario: delegate_task calls send_task, but we get an empty or blank string
    => We do a retry with a 'STRICT MODE:' prefix.
    """
    # First call returns an empty string, second call returns a minimal code block
    mock_send_task.side_effect = [
        "  ",  # empty response
        "```python\ndef placeholder_function():\n    pass\n```"
    ]

    final_result = agent_mgr.delegate_task("engineer", "Please fix code", timeout=30)
    # The first time is empty => triggers a retry with stricter prompt
    # The second time returns the code block
    assert mock_send_task.call_count == 2, "Expected two calls to send_task"
    assert "placeholder_function" in final_result, "Expected the fallback code block."

@patch.object(AgentManager, "send_task")
def test_delegate_task_fallback(mock_send_task, agent_mgr):
    """
    If both calls to send_task yield blank strings,
    we expect the final fallback '```python\ndef placeholder_function()...' block.
    """
    mock_send_task.side_effect = ["   ", ""]

    final_result = agent_mgr.delegate_task("oversight", "Please do a fix", timeout=45)
    assert mock_send_task.call_count == 2, "Expected two calls to send_task for fallback logic"
    assert "placeholder_function" in final_result, "Expected the fallback function definition."
