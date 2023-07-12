from flask import Flask, Response
from collections import Counter
import math
import os
import sys
import json
from typing import Generator, Any, Dict, Tuple, Union, List
sys.path.append('../../../real-time-baby-sleep-position-detector')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '4'
# tf.get_logger().setLevel('ERROR')
from utils.settings import PROCESSED_EVENTS_TOPIC, SLACK_ALERT
from utils.data_utils import create_consumer, slack_alert

app = Flask(__name__, template_folder='templates')
app.config['SERVER_NAME'] = '127.0.0.1:5000'


def stream_template(template_name: str, **context: Any) -> Response:
    """
    Enable streaming back results to the Flask app.

    Args:
        template_name: The name of the template to be streamed.
        **context: Additional context variables to be passed to the template.

    Returns:
        A Flask Response object for streaming the template.

    """
    app.update_template_context(context)
    template = app.jinja_env.get_template(template_name)
    streaming = template.stream(context)
    return streaming


def extract_status(message: Response) -> Dict[str, Any]:
    """
    Extract the status value from a Kafka ConsumerRecord.

    Args:
        message: The Kafka ConsumerRecord containing the message.

    Returns:
        A dictionary representing the extracted status value.

    """
    value = json.loads(list(message.items())[0][1][0].value.decode('utf-8'))
    return value


def trim_activity(baby_activity: List[str]) -> List[str]:
    """
    Trim the baby_activity list to a specific size.

    Args:
        baby_activity: The list of baby activity statuses.

    Returns:
        The trimmed baby_activity list.

    """
    level_ceil = 20
    level_status = 10

    if len(baby_activity) > level_ceil:
        baby_activity = baby_activity[level_status:]

    return baby_activity


def calculate_entropy(baby_activity: List[str]) -> float:
    """
    Calculate the entropy of the baby_activity list.

    Args:
        baby_activity: The list of baby activity statuses.

    Returns:
        The calculated entropy value.

    """
    level_status = 10

    if len(baby_activity) > level_status:
        status_counts = Counter(baby_activity[-level_status:])
        total_count = len(baby_activity[-level_status:])

        entropy = 0.0
        for count in status_counts.values():
            probability = count / total_count
            entropy -= probability * math.log2(probability)

        return entropy

    return 0.0


def update_last_status(last_status: Union[str, None], status: str) -> str:
    """
    Update the last_status based on the current status.

    Args:
        last_status: The previous status value.
        status: The current status value.

    Returns:
        The updated last_status.

    """
    if last_status is None:
        last_status = status
    elif last_status != status:
        last_status = status

    return last_status


@app.route('/')
def consume() -> Response:
    """
    Consume messages from the Kafka topic and stream the processed data to the Flask app.

    Returns:
        A Flask Response object for streaming the processed data.

    """

    consumer = create_consumer(topic=PROCESSED_EVENTS_TOPIC)

    def consume_msg():
        status = None
        last_status = None
        baby_activity = []

        while True:
            message = consumer.poll(timeout_ms=50000)
            if message is None:
                continue
            if message == {}:
                continue

            payload = extract_status(message)

            for k in payload.keys():
                if k == 'status':
                    status = payload['status']
                    baby_activity.append(status)
                    baby_activity = trim_activity(baby_activity)
                    entropy = calculate_entropy(baby_activity)
                    last_status = update_last_status(last_status, status)
                elif k == 'timestamp':
                    timestamp = payload['timestamp']

            if SLACK_ALERT:
                if last_status in ['side', 'prone']:
                    slack_alert(last_status=last_status)
            yield [last_status, entropy, timestamp]

            print(last_status, entropy, timestamp)

    return Response(stream_template('index.html', data=consume_msg()))


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)
