import numpy as np
import tensorflow as tf
import os
from matplotlib import pyplot as plt
import cv2
from keras.preprocessing import image
from keras.models import load_model
from tensorflow.keras.metrics import Precision, Recall, BinaryAccuracy
from sklearn.metrics import confusion_matrix
import seaborn as sns
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dense, Flatten
from tensorflow.keras.optimizers import AdamW
import time

def train_model_part1(base_dir=None):
    if base_dir:
        os.makedirs(os.path.join(base_dir, 'shared_volume/train'), exist_ok=True)
        os.makedirs(os.path.join(base_dir, 'shared_volume/test'), exist_ok=True)
    
    # First half of the model
    model_part1 = Sequential()
    model_part1.add(Conv2D(250, (3,3), 1, activation='relu', input_shape=(250,250,3)))
    model_part1.add(MaxPooling2D())
    model_part1.add(Conv2D(125, (3,3), 1, activation='relu'))
    model_part1.add(MaxPooling2D())
    model_part1.add(Flatten())  # Add Flatten to reduce dimensions
    model_part1.add(Dense(125, activation='relu'))  # Add Dense layer for intermediates

    # Compile first model with correct metrics
    model_part1.compile(optimizer='adam', 
                       loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                       metrics=['accuracy'])

    # Load and preprocess data
    Training = tf.keras.utils.image_dataset_from_directory(
        'kaggle/input/forest-fire-dataset/Forest Fire Dataset/Training',
        image_size=(16, 16)
    )
    Training = Training.map(lambda x,y: (x/255, y))

    # Split data
    train_size = int(len(Training)*.8 / 100) # TODO: increase, decreased just for trying
    test_size = int(len(Training)*.2 / 100) # TODO: increase, decreased just for trying
    train = Training.take(train_size)
    test = Training.skip(train_size).take(test_size)

    # Add tensorboard callback
    logdir='logs_part1'
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=logdir)

    # Time the training of first half
    start_time = time.time()

    hist = model_part1.fit(train, 
                          epochs=1, 
                          validation_data=test, 
                          callbacks=[tensorboard_callback])

    training_time = time.time() - start_time
    print(f"First half training time: {training_time:.2f} seconds")

    # Save and process results
    save_path = os.path.join(base_dir, 'shared_volume') if base_dir else 'shared_volume'
    model_part1.save(f'{save_path}/model_part1.keras')

    # Generate and save intermediate outputs
    def save_intermediate_outputs(dataset, output_path):
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        all_features = []
        all_labels = []

        for images, labels in dataset:
            features = model_part1.predict(images)
            all_features.append(features)
            all_labels.append(labels)

        np.save(f'{output_path}/features.npy', np.concatenate(all_features))
        np.save(f'{output_path}/labels.npy', np.concatenate(all_labels))

    # Time the intermediate results generation
    start_time = time.time()
    save_intermediate_outputs(train, f'{save_path}/train')
    save_intermediate_outputs(test, f'{save_path}/test')
    processing_time = time.time() - start_time
    print(f"Feature generation time: {processing_time:.2f} seconds")

    # Save timing information
    timing_info = {
        'training_time': training_time,
        'processing_time': processing_time
    }
    np.save(f'{save_path}/timing_part1.npy', timing_info)
    
    return {
        'training_time': training_time,
        'processing_time': processing_time,
        'history': hist.history
    }

if __name__ == '__main__':
    train_model_part1()
