"""Unit tests for OpenAI Realtime integration."""
import pytest
from unittest.mock import MagicMock, patch
from inflight_agentics.openai_realtime_integration import RealtimeLLMClient

@pytest.fixture
def mock_openai():
    """Fixture to mock OpenAI's API."""
    with patch('inflight_agentics.openai_realtime_integration.openai') as mock:
        yield mock

@pytest.fixture
def mock_session():
    """Fixture to create a mock session."""
    session = MagicMock()
    
    # Create mock events
    event1 = MagicMock()
    event1.type = "response.text.delta"
    event1.text = "This is a "
    
    event2 = MagicMock()
    event2.type = "response.text.delta"
    event2.text = "test response."
    
    # Configure session to return events
    session.send_message.return_value = [event1, event2]
    return session

def test_init_sets_api_key(mock_openai):
    """Test that initialization sets the API key."""
    client = RealtimeLLMClient()
    assert mock_openai.api_key is not None

def test_stream_text_success(mock_openai, mock_session):
    """Test successful text streaming."""
    # Configure mock
    mock_openai.ChatCompletion.create_session.return_value = mock_session
    
    # Create client and test
    client = RealtimeLLMClient()
    response = client.stream_text("Test prompt")
    
    # Verify results
    assert response == "This is a test response."
    mock_session.send_message.assert_called_once_with("Test prompt")

def test_stream_text_handles_non_delta_events(mock_openai):
    """Test handling of non-delta events."""
    # Create mock session with non-delta event
    session = MagicMock()
    event = MagicMock()
    event.type = "response.text.complete"
    event.text = "Complete text"
    session.send_message.return_value = [event]
    
    mock_openai.ChatCompletion.create_session.return_value = session
    
    client = RealtimeLLMClient()
    response = client.stream_text("Test prompt")
    
    # Should ignore non-delta events
    assert response == ""

def test_stream_text_retries_on_error(mock_openai, mock_session):
    """Test retry behavior on streaming errors."""
    # Configure session to fail twice then succeed
    failing_session = MagicMock()
    failing_session.send_message.side_effect = [
        Exception("First failure"),
        Exception("Second failure"),
        [
            MagicMock(type="response.text.delta", text="Success after retries")
        ]
    ]
    
    mock_openai.ChatCompletion.create_session.return_value = failing_session
    
    client = RealtimeLLMClient()
    response = client.stream_text("Test prompt", retries=3)
    
    assert response == "Success after retries"
    assert failing_session.send_message.call_count == 3

def test_stream_text_max_retries_exceeded(mock_openai):
    """Test behavior when max retries are exceeded."""
    # Configure session to always fail
    failing_session = MagicMock()
    failing_session.send_message.side_effect = Exception("Persistent failure")
    
    mock_openai.ChatCompletion.create_session.return_value = failing_session
    
    client = RealtimeLLMClient()
    
    with pytest.raises(Exception) as exc_info:
        client.stream_text("Test prompt", retries=2)
    
    assert "Failed to stream text after 2 attempts" in str(exc_info.value)
    assert failing_session.send_message.call_count == 3  # Initial try + 2 retries

def test_stream_text_session_creation_error(mock_openai):
    """Test handling of session creation errors."""
    mock_openai.ChatCompletion.create_session.side_effect = Exception("Session creation failed")
    
    client = RealtimeLLMClient()
    
    with pytest.raises(Exception) as exc_info:
        client.stream_text("Test prompt")
    
    assert "Failed to stream text after" in str(exc_info.value)

def test_repr_format():
    """Test the string representation of the client."""
    client = RealtimeLLMClient()
    repr_str = repr(client)
    assert "RealtimeLLMClient" in repr_str
    assert "********" in repr_str  # API key should be masked
