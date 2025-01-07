"""Inflight Agentics - A real-time event processing system for flight operations."""

from inflight_agentics.agentic_logic import AgenticController
from inflight_agentics.kafka_consumer import FlightEventConsumer
from inflight_agentics.kafka_producer import FlightEventProducer
from inflight_agentics.openai_realtime_integration import RealtimeLLMClient

__all__ = [
    'AgenticController',
    'FlightEventConsumer',
    'FlightEventProducer',
    'RealtimeLLMClient',
]

__version__ = '0.1.0'
