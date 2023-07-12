# used to get environment variables with config info
import datetime
import os
import sys
from multiprocessing import Process
import logging
import numpy as np
import tensorflow as tf

sys.path.append('../../../real-time-baby-sleep-position-detector')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '4'

from utils.data_utils import (create_consumer, create_producer,
                              preprocess_input, send_data_to_kafka)
from utils.settings import (KAFKA_BOOTSTRAP, NUM_PARTITIONS,
                            PROCESSED_EVENTS_TOPIC, RAW_EVENTS_TOPIC)

print("Using Kafka cluster at %s" % (KAFKA_BOOTSTRAP))
print("Reading sensor events from %s and producing predictions to %s" % (RAW_EVENTS_TOPIC, PROCESSED_EVENTS_TOPIC))


transformed_labels = ['back', 'stand', 'prone', 'side', 'side']


def detect() -> None:
    """
    Run the detection process to classify sensor events.

    """

    loaded_model = tf.keras.models.load_model("model.h5")
    consumer = create_consumer(topic=RAW_EVENTS_TOPIC)
    producer_predicted = create_producer(value_serializer_type='json')

    while True:

        message = consumer.poll(timeout_ms=5000)

        if message is None:
            continue

        try:

            input_model_payload = preprocess_input(message=message, key='value')
            timestamp = preprocess_input(message=message, key='current_time')
            predicted_value = loaded_model.predict(input_model_payload, verbose=1)
            idx_predicted = np.argmax(predicted_value)

            print('**************************************')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(timestamp, transformed_labels[idx_predicted])
            print('**************************************')

            send_data_to_kafka(
                producer=producer_predicted,
                data={'status': transformed_labels[idx_predicted], "timestamp": timestamp},
                topic=PROCESSED_EVENTS_TOPIC
            )

        except Exception as e:
            logging.warning("Error occurred during processing. Error: %s" % str(e))
            continue


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    print("Using Kafka cluster at %s" % (KAFKA_BOOTSTRAP))
    print("Reading sensor events from %s and producing predictions to %s" % (
        RAW_EVENTS_TOPIC, 
        PROCESSED_EVENTS_TOPIC
    ))
    for _ in range(NUM_PARTITIONS):
        p = Process(target=detect)
        p.start()
