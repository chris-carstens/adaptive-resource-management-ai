import os
import subprocess


import kagglehub

# Download latest version
path = kagglehub.dataset_download("alik05/forest-fire-dataset")

print("Path to dataset files:", path)

# Get current directory and construct absolute paths
current_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(current_dir, 'hello.py')
        
        # Create working directory if it doesn't exist
os.makedirs(os.path.join(current_dir, 'shared_volume'), exist_ok=True)
os.makedirs(os.path.join(current_dir, 'shared_volume/train'), exist_ok=True)
os.makedirs(os.path.join(current_dir, 'shared_volume/test'), exist_ok=True)
        
        # Run the training script from the correct directory
result = subprocess.run(['python', script_path], 
        capture_output=True, 
        text=True,
        cwd=current_dir)  # Set working directory
        