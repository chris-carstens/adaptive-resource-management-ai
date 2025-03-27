import numpy as np
import kagglehub
import os
import time

import numpy as np
import tensorflow as tf
import os
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dense, Flatten

def train_model_part1(base_dir=None):
    print('HOLA')
    if base_dir:
        os.makedirs(os.path.join(base_dir, 'shared_volume/train'), exist_ok=True)
        os.makedirs(os.path.join(base_dir, 'shared_volume/test'), exist_ok=True)
    print('HOL2')
    
    # First half of the model
    model_part1 = Sequential()
    model_part1.add(Conv2D(32, (3,3), 1, activation='relu', input_shape=(64,64,3)))
    model_part1.add(MaxPooling2D())
    model_part1.add(Conv2D(64, (3,3), 1, activation='relu'))
    model_part1.add(MaxPooling2D())
    model_part1.add(Conv2D(128, (3,3), 1, activation='relu'))
    model_part1.add(MaxPooling2D())
    model_part1.add(Flatten())
    model_part1.add(Dense(256, activation='relu'))
    print('HOL3')

    # Compile first model with correct metrics
    model_part1.compile(optimizer='adam', 
                       loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                       metrics=['accuracy'])
    print('HOL4')

    try:
        # Download dataset using kagglehub
        print('HOL5')
        
        # Update the training path to point to the downloaded dataset
        training_path = os.path.join(dataset_path, "Forest Fire Dataset", "Training")
        
        if not os.path.exists(training_path):
            error_msg = f"Training data not found at {training_path}"
            raise FileNotFoundError(error_msg)
        print('HOL6')
        print('HOL6.1')

            
        # Load and preprocess data
        Training = tf.keras.utils.image_dataset_from_directory(
            training_path,
            image_size=(64, 64)
        )
        print('HOL7')
        Training = Training.map(lambda x,y: (x/255, y))
        print('HOL7.1')
    except Exception as e:
        error_msg = f"Failed to load dataset: {str(e)}"
        raise Exception(error_msg)

    # Split data
    train_size = int(len(Training)*.8 * 0.2) # TODO: INCREASE
    test_size = int(len(Training)*.2 * 0.2) # TODO: INCREASE
    train = Training.take(train_size)
    test = Training.skip(train_size).take(test_size)

    # Add tensorboard callback
    logdir='logs_part1'
    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=logdir)

    # Time the training of first half
    start_time = time.time()
    print('HOL8')

    hist = model_part1.fit(train, 
                          epochs=1, 
                          validation_data=test, 
                          callbacks=[tensorboard_callback])
    print('HOL9')

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

print('HOLA INICIAL')
global dataset_path
dataset_path = kagglehub.dataset_download("alik05/forest-fire-dataset")

current_dir = os.path.dirname(os.path.abspath(__file__))
train_model_part1(current_dir)
