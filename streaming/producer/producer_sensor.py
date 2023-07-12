#!/usr/bin/env python3
import time
from datetime import datetime
import sys
import numpy as np

sys.path.append('../../../real-time-baby-sleep-position-detector')
from utils.settings import KAFKA_BOOTSTRAP, PP_ADDRESS, RAW_EVENTS_TOPIC, WINDOW_SIZE
from utils.data_utils import configure_session, create_producer, send_data_to_kafka

print("Using Kafka cluster at %s" % (KAFKA_BOOTSTRAP))


def get_sensor_values(session) -> np.ndarray:

    """
    Get sensor values from the specified session.

    Args:
        session: The session for making HTTP requests.

    Returns:
        A NumPy array of sensor values.

    """

    response_accX = session.get(url=f'{PP_ADDRESS}/get?accX').json()['buffer']['accX']['buffer'][0]
    response_accY = session.get(url=f'{PP_ADDRESS}/get?accY').json()['buffer']['accY']['buffer'][0]
    response_accZ = session.get(url=f'{PP_ADDRESS}/get?accZ').json()['buffer']['accZ']['buffer'][0]
    response_gyrX = session.get(url=f'{PP_ADDRESS}/get?gyrX').json()['buffer']['gyrX']['buffer'][0]
    response_gyrY = session.get(url=f'{PP_ADDRESS}/get?gyrY').json()['buffer']['gyrY']['buffer'][0]
    response_gyrZ = session.get(url=f'{PP_ADDRESS}/get?gyrZ').json()['buffer']['gyrZ']['buffer'][0]

    values = np.array([response_accX, response_accY, response_accZ, response_gyrX, response_gyrY, response_gyrZ])
    return values


def run_sensor_collection() -> None:

    """
    Run the sensor collection process continuously.

    """
    session = configure_session()
    producer = create_producer(value_serializer_type='json')
    counter = 0
    load_value = []

    while True:
        values = get_sensor_values(session)
        load_value.append(values)
        current_time = datetime.utcnow().isoformat()

        if counter % WINDOW_SIZE == 0:
            message_value = {'value': np.array(load_value).tolist(), "current_time": current_time}

            # Send the message to Kafka
            send_data_to_kafka(producer, RAW_EVENTS_TOPIC, message_value)
            load_value = []
            print(message_value)

        counter += 1


if __name__ == "__main__":
    sys.exit(run_sensor_collection())
