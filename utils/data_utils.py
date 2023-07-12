import json
import logging
import os
import socket
import sys

import numpy as np
import requests
from kafka3 import KafkaConsumer, KafkaProducer
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

sys.path.append('../../../real-time-baby-sleep-position-detector')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '4'
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# tf.get_logger().setLevel('ERROR')
from utils.settings import (KAFKA_BOOTSTRAP, SLACK_API_TOKEN, SLACK_CHANNEL,
                            WINDOW_SIZE, SLACK_ALERT)


def create_producer(value_serializer_type: str) -> KafkaProducer:
    """
    Create a Kafka producer with the specified value serializer type.

    Args:
        value_serializer_type: The type of value serializer to use.

    Returns:
        The created Kafka producer.

    """

    if value_serializer_type == 'json':
        value_serializer = lambda v: json.dumps(v).encode('utf-8')
    if value_serializer_type == 'string':
        value_serializer = str.encode

    try:
        producer = KafkaProducer(
            client_id=socket.gethostname(),
            bootstrap_servers=[KAFKA_BOOTSTRAP],
            value_serializer=value_serializer,
            batch_size=64000,
            retries=3
        )
    except Exception as e:
        logging.exception(f"Couldn't create the producer due to error {e}")
        producer = None
    return producer


def create_consumer(topic: str, group_id: str = None) -> KafkaConsumer:
    """
    Create a Kafka consumer for the specified topic and group ID.

    Args:
        topic: The topic to consume messages from.
        group_id: The group ID for the consumer.

    Returns:
        The created Kafka consumer.

    """
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            client_id=socket.gethostname(),
            group_id=group_id)

        consumer.subscribe([topic])

    except Exception as e:
        logging.exception(f"Couldn't create the consumer due to error {e}")
        consumer = None
    return consumer


def configure_session() -> requests.Session:
    """
    Configure and return a requests session with retry functionality.

    Returns:
        The configured requests session.

    """
    session = requests.Session()
    retry = Retry(connect=5, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def send_data_to_kafka(producer: KafkaProducer, topic: str, data) -> None:
    """
    Send data to a Kafka topic using the specified producer.

    Args:
        producer: The Kafka producer to use.
        topic: The topic to send data to.
        data: The data to send.

    """
    try:
        producer.send(topic=topic, value=data)
    except Exception as e:
        logging.warning("Failed to send data to Kafka. Error: %s" % str(e))


def extract_payload_value(item, key: str):
    """
    Extract a value from a Kafka message payload using the specified key.

    Args:
        item: The Kafka message item.
        key: The key to extract the value from the payload.

    Returns:
        The extracted value from the payload.

    """
    try:
        payload = json.loads(item.value.decode('utf-8'))
        return payload.get(key)
    except (ValueError, KeyError):
        return None


def preprocess_input(message, key: str = 'value') -> np.ndarray:
    """
    Preprocess the input data from a Kafka message.

    Args:
        message: The Kafka message.
        key: The key to extract the input data from the message.

    Returns:
        The preprocessed input data as a NumPy array.

    """
    try:
        payload_items = list(message.items())[0][1]
        array_payload = [extract_payload_value(item, key) for item in payload_items]
        input_payload = np.array(array_payload)
        if len(input_payload) == WINDOW_SIZE:
            tmp_payload = np.reshape(input_payload, (1, WINDOW_SIZE, 6))
        elif len(input_payload) == 1:
            tmp_payload = input_payload
        else:
            raise ValueError('Method must be 40 or 1.')

        return tmp_payload
    except (IndexError, TypeError):
        return None


client = WebClient(token=SLACK_API_TOKEN)


def slack_alert(last_status):

    try:
        # Send message to slack channel
        client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text=last_status
        )
    except SlackApiError as e:
        print(e.response["error"])