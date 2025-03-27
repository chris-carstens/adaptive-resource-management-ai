import numpy as np
import os
import time
import tensorflow as tf
from tensorflow.keras.metrics import Precision, Recall, BinaryAccuracy
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import AdamW

class IntermediateDataset:
    def __init__(self, data_path):
        self.data_files = sorted([f for f in os.listdir(f'{data_path}') if f.endswith('_data.npy')])
        self.label_files = sorted([f for f in os.listdir(f'{data_path}') if f.endswith('_labels.npy')])
        self.data_path = data_path
        
    def __len__(self):
        return len(self.data_files)
    
    def as_dataset(self):
        def generator():
            for data_file, label_file in zip(self.data_files, self.label_files):
                data = np.load(f'{self.data_path}/{data_file}')
                labels = np.load(f'{self.data_path}/{label_file}')
                yield data, labels
        
        return tf.data.Dataset.from_generator(
            generator,
            output_signature=(
                tf.TensorSpec(shape=(None, None, None, 125), dtype=tf.float32),
                tf.TensorSpec(shape=(None,), dtype=tf.int32)
            )
        )

def train_model_part2(base_dir=None):
    # Enable eager execution
    tf.config.run_functions_eagerly(True)
    
    save_path = os.path.join(base_dir, 'shared_volume') if base_dir else 'shared_volume'
    
    # Load the preprocessed features
    train_features = np.load(f'{save_path}/train/features.npy')
    train_labels = np.load(f'{save_path}/train/labels.npy')
    test_features = np.load(f'{save_path}/test/features.npy')
    test_labels = np.load(f'{save_path}/test/labels.npy')
    
    # Validate dataset sizes
    if len(train_features) == 0 or len(test_features) == 0:
        raise ValueError("Empty dataset detected")
    
    print(f"Dataset sizes - Train: {len(train_features)}, Test: {len(test_features)}")
    
    # Create datasets
    train_dataset = tf.data.Dataset.from_tensor_slices((train_features, train_labels)).batch(32)
    test_dataset = tf.data.Dataset.from_tensor_slices((test_features, test_labels)).batch(32)

    # Second half of the model
    model_part2 = Sequential()
    model_part2.add(Dense(64, activation='relu', input_shape=(256,)))
    model_part2.add(Dense(32, activation='relu'))
    model_part2.add(Dense(1, activation='sigmoid'))

    # Compile model with correct loss
    learning_rate = 0.001
    optimizer = AdamW(learning_rate=learning_rate)
    model_part2.compile(optimizer=optimizer, 
                    loss=tf.keras.losses.BinaryCrossentropy(),
                    metrics=['accuracy'],
                    run_eagerly=True)

    # Validate datasets are not empty
    for x, y in train_dataset.take(1):
        print(f"First batch shapes - Features: {x.shape}, Labels: {y.shape}")

    # Add tensorboard callback
    logdir='logs_part2'
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=logdir)

    # Time the second half training
    start_time = time.time()

    hist = model_part2.fit(
        train_dataset,
        epochs=1,
        validation_data=test_dataset,
        callbacks=[tensorboard_callback]
    )

    training_time = time.time() - start_time
    print(f"Second half training time: {training_time:.2f} seconds")

    # Initialize metrics
    pre = Precision()
    re = Recall()
    acc = BinaryAccuracy()

    # Evaluate metrics on test dataset
    for features, labels in test_dataset:
        predictions = model_part2.predict(features)
        pre.update_state(labels, predictions)
        re.update_state(labels, predictions)
        acc.update_state(labels, predictions)

    print(f"\nModel Metrics:")
    print(f"Precision: {pre.result().numpy():.4f}")
    print(f"Recall: {re.result().numpy():.4f}")
    print(f"Accuracy: {acc.result().numpy():.4f}")

    # Load first part timing and calculate total
    part1_timing = np.load(f'{save_path}/timing_part1.npy', allow_pickle=True).item()
    total_time = part1_timing['training_time'] + part1_timing['processing_time'] + training_time

    print(f"\nTotal timing breakdown:")
    print(f"First half training: {part1_timing['training_time']:.2f} seconds")
    print(f"Feature generation: {part1_timing['processing_time']:.2f} seconds")
    print(f"Second half training: {training_time:.2f} seconds")
    print(f"Total time: {total_time:.2f} seconds")

    # Save the final model
    model_part2.save(f'{save_path}/model_part2.keras')

    return {
        'training_time': training_time,
        'metrics': {
            'precision': pre.result().numpy(),
            'recall': re.result().numpy(),
            'accuracy': acc.result().numpy()
        },
        'history': hist.history
    }
current_dir = os.path.dirname(os.path.abspath(__file__))
result = train_model_part2(current_dir)