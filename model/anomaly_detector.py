from typing import List, Tuple
import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
import tensorflow as tf
import sys

# Define labels and columns
labels = [
    "back",
    "left_side",
    "right_side",
    "prone",
    "stand"
]

columns = [
    "accel_x",
    "accel_y",
    "accel_z",
    "gyro_x",
    "gyro_y",
    "gyro_z"
]

# Window settings
WINDOW_SIZE = 40
WINDOW_STEP = 15


def load_data(label: str) -> Tuple[List[np.ndarray], List[str]]:
    filename = f"trainingdata/train-{label}.csv"
    df = pd.read_csv(filename, header=None, names=columns)
    inputs = df[columns]
    num_samples = len(inputs)

    input_windows, target_windows = [], []

    for start_idx in range(0, num_samples - WINDOW_SIZE, WINDOW_STEP):
        end_idx = start_idx + WINDOW_SIZE
        input_windows.append(inputs.iloc[start_idx:end_idx].values)
        target_windows.append(label)

    return input_windows, target_windows


def prepare_training_data() -> Tuple[np.ndarray, np.ndarray]:
    training_x, training_y = [], []
    for label in labels:
        print(f"Getting training examples for {label}")
        input_windows, target_windows = load_data(label)
        training_x.extend(input_windows)
        training_y.extend(target_windows)

    training_x = np.array(training_x)
    training_y = np.array(training_y).reshape(-1, 1)

    return training_x, training_y


def prepare_labels(training_y: np.ndarray) -> Tuple[np.ndarray, OneHotEncoder]:
    enc = OneHotEncoder(sparse=False).fit(training_y)
    training_y = enc.transform(training_y)

    return training_y, enc


def create_model(input_shape: Tuple[int, int], num_labels: int) -> tf.keras.Model:
    units = 64

    model = tf.keras.Sequential([
        tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(units, return_sequences=True, input_shape=input_shape)),
        tf.keras.layers.Dropout(rate=0.5),
        tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(units)),
        tf.keras.layers.Dense(units, activation="relu"),
        tf.keras.layers.Dropout(rate=0.5),
        tf.keras.layers.Dense(num_labels, activation="softmax")
    ])

    optimizer = tf.keras.optimizers.Adam(learning_rate=0.01)
    loss = tf.keras.losses.CategoricalCrossentropy()

    model.compile(loss=loss, metrics=["accuracy"], optimizer=optimizer)

    return model


def train_model(model: tf.keras.Model, training_x: np.ndarray, training_y: np.ndarray) -> None:
    print("Training ML model...")
    model.fit(
        training_x,
        training_y,
        epochs=25,
        shuffle=True,
        verbose=1
    )


def save_model(model: tf.keras.Model, filepath: str) -> None:
    model.save(filepath)


def load_saved_model(filepath: str) -> tf.keras.Model:
    loaded_model = tf.keras.models.load_model(filepath=filepath)
    return loaded_model


def run_test(model: tf.keras.Model, enc: OneHotEncoder, test_label: str) -> None:
    filename = f"testdata/test-{test_label}.csv"
    df = pd.read_csv(filename, header=None, names=columns)
    inputs = df[columns]
    x_test = np.array([inputs.iloc[0:WINDOW_SIZE].values])

    prediction = model.predict(x_test)
    print(f"expected   : {test_label}")
    print(f"prediction : {enc.inverse_transform(prediction)[0][0]}")


def main() -> None:
    print("--------------------------------------------------------------")
    print("Preparing training data...")
    print("--------------------------------------------------------------")

    training_x, training_y = prepare_training_data()

    print("Shaping training data...")

    input_shape = (WINDOW_SIZE, len(columns))
    training_y, enc = prepare_labels(training_y)

    print("Creating ML model...")
    model = create_model(input_shape, len(labels))

    train_model(model, training_x, training_y)

    # Save the trained model
    save_model(model, "model.h5")

    # ---------------------------------------------------------------------------

    print("--------------------------------------------------------------")
    print("Test to verify the ML model...")
    print("--------------------------------------------------------------")

    loaded_model = load_saved_model("model.h5")

    run_test(loaded_model, enc, "back")
    run_test(loaded_model, enc, "stand")
    run_test(loaded_model, enc, "right_side")


if __name__ == "__main__":
    sys.exit(main())
