KAFKA_BOOTSTRAP = 'localhost:9092'
RAW_EVENTS_TOPIC = 'RAW_SENSORS'
PROCESSED_EVENTS_TOPIC = 'BODY_ACTIVITY'
WINDOW_SIZE = 40
WINDOW_STEP = 15
BATCH_SIZE = 64
SLACK_API_TOKEN = ""
SLACK_CHANNEL = ""
SLACK_ALERT = False

PP_ADDRESS = 'http://192.168.42.129:8541'
NUM_PARTITIONS = 1
COLUMNS_SENSORS = [
    # accelerometer data
    "accel_x",
    "accel_y",
    "accel_z",
    # gyroscope data
    "gyro_x",
    "gyro_y",
    "gyro_z"
]

NUM_COLUMNS = len(COLUMNS_SENSORS)
RAW_SENSOR_CONSUMER_GROUP = "raw_sensor"
PROCESSED_CONSUMER_GROUP = "body_activity"
