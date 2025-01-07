"""Unit tests for Kafka producer."""
import pytest
from unittest.mock import MagicMock, patch
from kafka.errors import KafkaError
from inflight_agentics.kafka_producer import FlightEventProducer

@pytest.fixture
def mock_kafka_producer():
    """Fixture to mock KafkaProducer."""
    with patch('inflight_agentics.kafka_producer.KafkaProducer') as mock:
        # Create a mock instance that will be returned by KafkaProducer()
        producer_instance = MagicMock()
        mock.return_value = producer_instance
        
        # Mock the send method to return a future
        future = MagicMock()
        future.get.return_value = MagicMock(
            topic='test-topic',
            partition=0,
            offset=1
        )
        producer_instance.send.return_value = future
        
        yield producer_instance

@pytest.fixture
def test_event():
    """Fixture providing a sample test event."""
    return {
        "flight_id": "AC1234",
        "status": "DELAYED",
        "timestamp": "2025-01-07T10:00:00Z",
        "delay_minutes": 45
    }

def test_producer_initialization():
    """Test producer initialization with default settings."""
    with patch('inflight_agentics.kafka_producer.KafkaProducer') as mock_kafka:
        producer = FlightEventProducer()
        
        # Verify KafkaProducer was initialized with correct parameters
        mock_kafka.assert_called_once()
        call_kwargs = mock_kafka.call_args.kwargs
        assert 'bootstrap_servers' in call_kwargs
        assert 'value_serializer' in call_kwargs
        assert 'retries' in call_kwargs

def test_successful_event_publish(mock_kafka_producer, test_event):
    """Test successful event publication."""
    producer = FlightEventProducer()
    
    # Publish event
    result = producer.publish_event(test_event, key="AC1234")
    
    # Verify the event was sent correctly
    assert result is True
    mock_kafka_producer.send.assert_called_once()
    mock_kafka_producer.flush.assert_called_once()
    
    # Verify the message was sent to the correct topic with correct data
    call_args = mock_kafka_producer.send.call_args
    assert call_args.args[0] == producer.topic  # First arg is topic
    assert call_args.kwargs['value'] == test_event
    assert call_args.kwargs['key'] == b"AC1234"  # Key should be encoded

def test_publish_without_key(mock_kafka_producer, test_event):
    """Test event publication without a key."""
    producer = FlightEventProducer()
    
    result = producer.publish_event(test_event)
    
    assert result is True
    call_kwargs = mock_kafka_producer.send.call_args.kwargs
    assert 'key' in call_kwargs
    assert call_kwargs['key'] is None

def test_failed_event_publish(mock_kafka_producer, test_event):
    """Test handling of failed event publication."""
    # Configure the future to raise an exception
    future = MagicMock()
    future.get.side_effect = KafkaError("Failed to send message")
    mock_kafka_producer.send.return_value = future
    
    producer = FlightEventProducer()
    
    # Attempt to publish event
    result = producer.publish_event(test_event)
    
    # Verify the result and error handling
    assert result is False
    mock_kafka_producer.flush.assert_called_once()

def test_producer_close(mock_kafka_producer):
    """Test proper closure of producer."""
    producer = FlightEventProducer()
    producer.close()
    
    mock_kafka_producer.close.assert_called_once()

def test_context_manager(mock_kafka_producer):
    """Test producer usage as context manager."""
    with FlightEventProducer() as producer:
        producer.publish_event({"test": "data"})
    
    # Verify producer was properly closed
    mock_kafka_producer.close.assert_called_once()

def test_producer_flush_on_publish(mock_kafka_producer, test_event):
    """Test that producer flushes after publishing."""
    producer = FlightEventProducer()
    producer.publish_event(test_event)
    
    mock_kafka_producer.flush.assert_called_once()

def test_producer_handles_send_timeout(mock_kafka_producer, test_event):
    """Test handling of timeout during send operation."""
    # Configure the future to raise a timeout
    future = MagicMock()
    future.get.side_effect = KafkaError("Operation timed out")
    mock_kafka_producer.send.return_value = future
    
    producer = FlightEventProducer()
    result = producer.publish_event(test_event)
    
    assert result is False

def test_producer_str_representation():
    """Test string representation of producer."""
    with patch('inflight_agentics.kafka_producer.KafkaProducer'):
        producer = FlightEventProducer(broker_url="test:9092", topic="test-topic")
        repr_str = repr(producer)
        
        assert "test:9092" in repr_str
        assert "test-topic" in repr_str

def test_producer_handles_close_error(mock_kafka_producer):
    """Test handling of errors during producer closure."""
    mock_kafka_producer.close.side_effect = Exception("Close failed")
    
    producer = FlightEventProducer()
    # Should not raise exception
    producer.close()
    
    mock_kafka_producer.close.assert_called_once()
