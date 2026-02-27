"""
Pytest suite for Kafka streaming components.

Tests cover producer initialization, message serialization,
and consumer functionality for grid state streaming.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from infrastructure.digital_twin.state_builder import GridState
from infrastructure.digital_twin.config import (
    N_BUSES,
    N_GENERATORS,
    N_LINES,
    NOMINAL_FREQUENCY,
)
from infrastructure.streaming.kafka_producer import GridKafkaProducer
from infrastructure.streaming.kafka_consumer_debug import GridStateConsumerDebug
from shared.topic_names import GRID_STATE_TOPIC

# mqtt is optional
try:
    from infrastructure.streaming.mqtt_producer import MqttGridProducer
except ImportError:  # type: ignore
    MqttGridProducer = None


class TestGridKafkaProducer:
    """Tests for GridKafkaProducer component."""

    @patch("infrastructure.streaming.kafka_producer.KafkaProducer")
    def test_producer_initialization(self, mock_kafka):
        """Test producer initialization with default parameters."""
        producer = GridKafkaProducer()

        assert producer.bootstrap_servers == "localhost:9092"
        assert producer.messages_sent == 0
        assert producer.messages_failed == 0
        mock_kafka.assert_called_once()

    @patch("infrastructure.streaming.kafka_producer.KafkaProducer")
    def test_producer_initialization_custom_servers(self, mock_kafka):
        """Test producer initialization with custom bootstrap servers."""
        producer = GridKafkaProducer(bootstrap_servers="broker1:9092,broker2:9092")

        assert producer.bootstrap_servers == "broker1:9092,broker2:9092"

    @patch("infrastructure.streaming.kafka_producer.KafkaProducer")
    def test_producer_initialization_custom_config(self, mock_kafka):
        """Test producer initialization with custom configuration."""
        producer = GridKafkaProducer(
            bootstrap_servers="localhost:9092",
            acks="1",
            retries=5,
            compression_type="snappy",
        )

        assert producer.messages_sent == 0
        # Verify KafkaProducer was called with correct parameters
        call_kwargs = mock_kafka.call_args[1]
        assert call_kwargs["acks"] == "1"
        assert call_kwargs["retries"] == 5
        assert call_kwargs["compression_type"] == "snappy"

    @patch("infrastructure.streaming.kafka_producer.KafkaProducer")
    def test_serialize_state(self, mock_kafka):
        """Test state serialization to JSON bytes."""
        producer = GridKafkaProducer()

        state_dict = {
            "timestamp": 1.0,
            "voltages": [1.0] * N_BUSES,
            "voltage_angles": [0.0] * N_BUSES,
            "loads": [100.0] * N_BUSES,
            "generator_outputs": [120.0] * N_GENERATORS,
            "line_flows": [50.0] * N_LINES,
            "frequency": NOMINAL_FREQUENCY,
        }

        serialized = producer._serialize_state(state_dict)

        assert isinstance(serialized, bytes)
        deserialized = json.loads(serialized.decode("utf-8"))
        assert deserialized["timestamp"] == 1.0
        assert deserialized["frequency"] == NOMINAL_FREQUENCY

    @patch("infrastructure.streaming.kafka_producer.KafkaProducer")
    def test_serialize_state_invalid(self, mock_kafka):
        """Test that serialization fails for non-serializable objects."""
        producer = GridKafkaProducer()

        # Create a non-serializable object
        class NonSerializable:
            pass

        invalid_dict = {"key": NonSerializable()}

        with pytest.raises(TypeError):
            producer._serialize_state(invalid_dict)

    @patch("infrastructure.streaming.kafka_producer.KafkaProducer")
    def test_delivery_callback_success(self, mock_kafka):
        """Test successful delivery callback."""
        producer = GridKafkaProducer()

        mock_metadata = Mock()
        # RecordMetadata exposes topic/partition/offset as attributes, not methods.
        mock_metadata.topic = GRID_STATE_TOPIC
        mock_metadata.partition = 0
        mock_metadata.offset = 42

        producer._delivery_callback(mock_metadata, exception=None)

        assert producer.messages_sent == 1
        assert producer.messages_failed == 0

    @patch("infrastructure.streaming.kafka_producer.KafkaProducer")
    def test_delivery_callback_failure(self, mock_kafka):
        """Test failed delivery callback."""
        producer = GridKafkaProducer()

        mock_metadata = Mock()
        exception = Exception("Broker unavailable")

        producer._delivery_callback(mock_metadata, exception=exception)

        assert producer.messages_sent == 0
        assert producer.messages_failed == 1

    @patch("infrastructure.streaming.kafka_producer.KafkaProducer")
    def test_publish_state_success(self, mock_kafka):
        """Test publishing a grid state."""
        mock_producer_instance = MagicMock()
        mock_kafka.return_value = mock_producer_instance

        producer = GridKafkaProducer()

        state_dict = {
            "timestamp": 1.0,
            "voltages": [1.0] * N_BUSES,
            "voltage_angles": [0.0] * N_BUSES,
            "loads": [100.0] * N_BUSES,
            "generator_outputs": [120.0] * N_GENERATORS,
            "line_flows": [50.0] * N_LINES,
            "frequency": NOMINAL_FREQUENCY,
        }

        # Mock the send future
        mock_future = MagicMock()
        mock_producer_instance.send.return_value = mock_future

        producer.publish_state(state_dict)

        # Verify send was called
        mock_producer_instance.send.assert_called_once()

    @patch("infrastructure.streaming.kafka_producer.KafkaProducer")
    def test_publish_state_invalid(self, mock_kafka):
        """Test that publishing None state raises ValueError."""
        producer = GridKafkaProducer()

        with pytest.raises(ValueError):
            producer.publish_state(None)

    @patch("infrastructure.streaming.kafka_producer.KafkaProducer")
    def test_publish_state_custom_topic(self, mock_kafka):
        """Test publishing to custom topic."""
        mock_producer_instance = MagicMock()
        mock_kafka.return_value = mock_producer_instance

        producer = GridKafkaProducer()

        mock_future = MagicMock()
        mock_producer_instance.send.return_value = mock_future

        state_dict = {
            "timestamp": 1.0,
            "voltages": [1.0] * N_BUSES,
            "voltage_angles": [0.0] * N_BUSES,
            "loads": [100.0] * N_BUSES,
            "generator_outputs": [120.0] * N_GENERATORS,
            "line_flows": [50.0] * N_LINES,
            "frequency": NOMINAL_FREQUENCY,
        }

        custom_topic = "custom.topic"
        producer.publish_state(state_dict, topic=custom_topic)

        # Verify send was called with correct topic
        call_args = mock_producer_instance.send.call_args
        assert call_args[0][0] == custom_topic

    @patch("infrastructure.streaming.kafka_producer.KafkaProducer")
    def test_get_metrics(self, mock_kafka):
        """Test metrics reporting."""
        producer = GridKafkaProducer()

        producer.messages_sent = 10
        producer.messages_failed = 2

        metrics = producer.get_metrics()

        assert metrics["messages_sent"] == 10
        assert metrics["messages_failed"] == 2
        assert metrics["total_messages"] == 12
        assert metrics["success_rate_percent"] == pytest.approx(83.33, rel=0.01)

    @patch("infrastructure.streaming.kafka_producer.KafkaProducer")
    def test_close(self, mock_kafka):
        """Test producer close."""
        mock_producer_instance = MagicMock()
        mock_kafka.return_value = mock_producer_instance

        producer = GridKafkaProducer()
        producer.close()

        mock_producer_instance.close.assert_called_once()

    def test_mqtt_producer_optional(self):
        """Ensure mqtt module imports or is skipped gracefully."""
        if MqttGridProducer is None:
            pytest.skip("paho-mqtt not installed")
        else:
            # instantiate with invalid broker to see error handling
            with pytest.raises(Exception):
                MqttGridProducer(broker="invalid_host")


class TestGridStateConsumerDebug:
    """Tests for GridStateConsumerDebug component."""

    @patch("infrastructure.streaming.kafka_consumer_debug.KafkaConsumer")
    def test_consumer_initialization(self, mock_kafka):
        """Test consumer initialization."""
        consumer = GridStateConsumerDebug()

        assert consumer.topic == GRID_STATE_TOPIC
        assert consumer.messages_received == 0
        assert consumer.messages_invalid == 0

    @patch("infrastructure.streaming.kafka_consumer_debug.KafkaConsumer")
    def test_consumer_custom_topic(self, mock_kafka):
        """Test consumer with custom topic."""
        custom_topic = "custom.grid.topic"
        consumer = GridStateConsumerDebug(topic=custom_topic)

        assert consumer.topic == custom_topic

    def test_validate_message_valid(self):
        """Test validation of valid grid state message."""
        with patch("infrastructure.streaming.kafka_consumer_debug.KafkaConsumer"):
            consumer = GridStateConsumerDebug()

        message = {
            "timestamp": 1.0,
            "voltages": [1.0] * N_BUSES,
            "voltage_angles": [0.0] * N_BUSES,
            "loads": [100.0] * N_BUSES,
            "generator_outputs": [120.0] * N_GENERATORS,
            "line_flows": [50.0] * N_LINES,
            "frequency": 50.0,
        }

        assert consumer.validate_message(message)

    def test_validate_message_missing_field(self):
        """Test validation fails for missing required field."""
        with patch("infrastructure.streaming.kafka_consumer_debug.KafkaConsumer"):
            consumer = GridStateConsumerDebug()

        message = {
            "timestamp": 1.0,
            "voltages": [1.0] * N_BUSES,
            # Missing other required fields
        }

        assert not consumer.validate_message(message)

    def test_validate_message_wrong_type(self):
        """Test validation fails for wrong field type."""
        with patch("infrastructure.streaming.kafka_consumer_debug.KafkaConsumer"):
            consumer = GridStateConsumerDebug()

        message = {
            "timestamp": "not_a_number",  # Should be numeric
            "voltages": [1.0] * N_BUSES,
            "voltage_angles": [0.0] * N_BUSES,
            "loads": [100.0] * N_BUSES,
            "generator_outputs": [120.0] * N_GENERATORS,
            "line_flows": [50.0] * N_LINES,
            "frequency": 50.0,
        }

        assert not consumer.validate_message(message)

    def test_validate_message_wrong_array_length(self):
        """Test validation fails for wrong array lengths."""
        with patch("infrastructure.streaming.kafka_consumer_debug.KafkaConsumer"):
            consumer = GridStateConsumerDebug()

        message = {
            "timestamp": 1.0,
            "voltages": [1.0] * (N_BUSES - 1),  # Wrong length
            "voltage_angles": [0.0] * N_BUSES,
            "loads": [100.0] * N_BUSES,
            "generator_outputs": [120.0] * N_GENERATORS,
            "line_flows": [50.0] * N_LINES,
            "frequency": 50.0,
        }

        assert not consumer.validate_message(message)

    def test_format_message(self):
        """Test message formatting for display."""
        with patch("infrastructure.streaming.kafka_consumer_debug.KafkaConsumer"):
            consumer = GridStateConsumerDebug()

        message = {
            "timestamp": 1.0,
            "voltages": [1.0] * N_BUSES,
            "voltage_angles": [0.0] * N_BUSES,
            "loads": [100.0] * N_BUSES,
            "generator_outputs": [120.0] * N_GENERATORS,
            "line_flows": [50.0] * N_LINES,
            "frequency": 50.0,
            "is_faulted": False,
        }

        formatted = consumer.format_message(message)

        assert isinstance(formatted, str)
        assert "GRID STATE SNAPSHOT" in formatted
        assert "FREQUENCY" in formatted
        assert "50.000" in formatted

    def test_format_message_with_fault(self):
        """Test message formatting when faulted."""
        with patch("infrastructure.streaming.kafka_consumer_debug.KafkaConsumer"):
            consumer = GridStateConsumerDebug()

        message = {
            "timestamp": 1.0,
            "voltages": [1.0] * N_BUSES,
            "voltage_angles": [0.0] * N_BUSES,
            "loads": [100.0] * N_BUSES,
            "generator_outputs": [120.0] * N_GENERATORS,
            "line_flows": [50.0] * N_LINES,
            "frequency": 50.0,
            "is_faulted": True,
            "fault_info": {"type": "voltage_sag"},
        }

        formatted = consumer.format_message(message)

        assert "FAULT ACTIVE" in formatted
        assert "voltage_sag" in formatted

    @patch("infrastructure.streaming.kafka_consumer_debug.KafkaConsumer")
    def test_consumer_close(self, mock_kafka):
        """Test consumer close."""
        mock_consumer_instance = MagicMock()
        mock_kafka.return_value = mock_consumer_instance

        consumer = GridStateConsumerDebug()
        consumer.close()

        mock_consumer_instance.close.assert_called_once()


class TestStreamingIntegration:
    """Integration tests for producer and consumer."""

    @patch("infrastructure.streaming.kafka_producer.KafkaProducer")
    @patch("infrastructure.streaming.kafka_consumer_debug.KafkaConsumer")
    def test_producer_consumer_message_flow(self, mock_consumer_class, mock_producer_class):
        """Test message flow from producer to consumer format."""
        # Setup mocks
        mock_producer_instance = MagicMock()
        mock_producer_class.return_value = mock_producer_instance

        mock_consumer_instance = MagicMock()
        mock_consumer_class.return_value = mock_consumer_instance

        # Create producer
        producer = GridKafkaProducer()

        # Create state
        state_dict = {
            "timestamp": 1.0,
            "voltages": [1.0] * N_BUSES,
            "voltage_angles": [0.0] * N_BUSES,
            "loads": [100.0] * N_BUSES,
            "generator_outputs": [120.0] * N_GENERATORS,
            "line_flows": [50.0] * N_LINES,
            "frequency": 50.0,
        }

        # Publish
        mock_future = MagicMock()
        mock_producer_instance.send.return_value = mock_future

        producer.publish_state(state_dict)

        # Verify send was called
        assert mock_producer_instance.send.called

        # Now verify consumer can process this message format
        consumer = GridStateConsumerDebug()
        assert consumer.validate_message(state_dict)
