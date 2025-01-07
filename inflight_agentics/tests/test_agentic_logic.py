"""Unit tests for agentic logic."""
import pytest
from unittest.mock import MagicMock, patch
from inflight_agentics.agentic_logic import AgenticController

@pytest.fixture
def mock_llm_client():
    """Fixture to create a mock LLM client."""
    mock = MagicMock()
    mock.stream_text.return_value = (
        "Based on the situation, I recommend rebooking the passengers. "
        "This is a definite case where immediate action is required."
    )
    return mock

@pytest.fixture
def test_event():
    """Fixture providing a sample test event."""
    return {
        "flight_id": "AC1234",
        "status": "DELAYED",
        "timestamp": "2025-01-07T10:00:00Z",
        "delay_minutes": 45,
        "reason": "Weather conditions"
    }

def test_controller_initialization():
    """Test controller initialization."""
    with patch('inflight_agentics.agentic_logic.RealtimeLLMClient') as mock_client:
        controller = AgenticController()
        assert controller.llm_client is not None
        mock_client.assert_called_once()

def test_controller_with_provided_client(mock_llm_client):
    """Test controller initialization with provided LLM client."""
    controller = AgenticController(llm_client=mock_llm_client)
    assert controller.llm_client == mock_llm_client

def test_process_event_success(mock_llm_client, test_event):
    """Test successful event processing."""
    controller = AgenticController(llm_client=mock_llm_client)
    result = controller.process_event(test_event)
    
    assert result["action_type"] == "REBOOK"
    assert result["confidence"] > 0.8  # High confidence due to "definite" in response
    assert isinstance(result["details"], dict)
    assert isinstance(result["reasoning"], str)
    
    # Verify prompt generation and LLM call
    mock_llm_client.stream_text.assert_called_once()
    prompt = mock_llm_client.stream_text.call_args.args[0]
    assert test_event["flight_id"] in prompt
    assert test_event["status"] in prompt
    assert str(test_event["delay_minutes"]) in prompt

def test_process_event_missing_fields():
    """Test handling of events with missing required fields."""
    controller = AgenticController()
    invalid_event = {
        "flight_id": "AC1234"  # Missing status and timestamp
    }
    
    result = controller.process_event(invalid_event)
    
    assert result["action_type"] == "ERROR"
    assert "Missing required fields" in result["details"]["error"]
    assert result["confidence"] == 0.0

def test_process_event_llm_error(mock_llm_client, test_event):
    """Test handling of LLM errors during processing."""
    mock_llm_client.stream_text.side_effect = Exception("LLM API error")
    controller = AgenticController(llm_client=mock_llm_client)
    
    result = controller.process_event(test_event)
    
    assert result["action_type"] == "ERROR"
    assert "LLM API error" in result["details"]["error"]
    assert result["confidence"] == 0.0

def test_prompt_generation(mock_llm_client):
    """Test prompt generation with different event data."""
    controller = AgenticController(llm_client=mock_llm_client)
    
    # Test with minimal event
    minimal_event = {
        "flight_id": "AC1234",
        "status": "ON_TIME",
        "timestamp": "2025-01-07T10:00:00Z"
    }
    controller.process_event(minimal_event)
    minimal_prompt = mock_llm_client.stream_text.call_args.args[0]
    assert "AC1234" in minimal_prompt
    assert "ON_TIME" in minimal_prompt
    
    # Test with detailed event
    detailed_event = {
        "flight_id": "AC5678",
        "status": "CANCELLED",
        "timestamp": "2025-01-07T11:00:00Z",
        "reason": "Technical issue",
        "delay_minutes": 120
    }
    controller.process_event(detailed_event)
    detailed_prompt = mock_llm_client.stream_text.call_args.args[0]
    assert "Technical issue" in detailed_prompt
    assert "120 minutes" in detailed_prompt

def test_response_parsing_variations(mock_llm_client, test_event):
    """Test parsing of different LLM response patterns."""
    controller = AgenticController(llm_client=mock_llm_client)
    
    # Test "definitely rebook" response
    mock_llm_client.stream_text.return_value = "We should definitely rebook these passengers."
    result = controller.process_event(test_event)
    assert result["action_type"] == "REBOOK"
    assert result["confidence"] > 0.8
    
    # Test "might need to notify" response
    mock_llm_client.stream_text.return_value = "We might need to notify passengers of the delay."
    result = controller.process_event(test_event)
    assert result["action_type"] == "NOTIFY"
    assert result["confidence"] < 0.8
    
    # Test "monitor situation" response
    mock_llm_client.stream_text.return_value = "Continue to monitor the situation."
    result = controller.process_event(test_event)
    assert result["action_type"] == "MONITOR"
    assert result["confidence"] == 0.7  # Default confidence

def test_controller_str_representation(mock_llm_client):
    """Test string representation of controller."""
    controller = AgenticController(llm_client=mock_llm_client)
    repr_str = repr(controller)
    assert "AgenticController" in repr_str
    assert "llm_client" in repr_str

def test_process_event_with_retries(mock_llm_client, test_event):
    """Test event processing with LLM retries."""
    # Configure LLM to fail once then succeed
    mock_llm_client.stream_text.side_effect = [
        Exception("Temporary error"),
        "Definitely rebook the passengers."
    ]
    
    controller = AgenticController(llm_client=mock_llm_client)
    result = controller.process_event(test_event)
    
    assert result["action_type"] == "REBOOK"
    assert mock_llm_client.stream_text.call_count == 2

def test_confidence_levels_in_responses(mock_llm_client, test_event):
    """Test confidence level assignment based on language patterns."""
    controller = AgenticController(llm_client=mock_llm_client)
    
    confidence_tests = [
        ("Certainly need to rebook", 0.9),
        ("Might need to monitor", 0.5),
        ("Should probably notify", 0.7),
        ("Definitely cancel", 0.9),
        ("Consider monitoring", 0.5)
    ]
    
    for response, expected_confidence in confidence_tests:
        mock_llm_client.stream_text.return_value = response
        result = controller.process_event(test_event)
        assert abs(result["confidence"] - expected_confidence) < 0.1
