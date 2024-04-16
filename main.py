import cv2
import os
import numpy as np
import multiprocessing
import json
import sys
import gzip
import shutil

def gzip_compress(filename):
    with open(filename, 'rb') as f_in:
        with gzip.open(f'{filename}.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(filename)

def save_coefficients(filename, red_coeffs, green_coeffs, blue_coeffs):
    # Create a dictionary to hold the coefficients
    coefficients_dict = {
        'red': [coeff.tolist() for coeff in red_coeffs],
        'green': [coeff.tolist() for coeff in green_coeffs],
        'blue': [coeff.tolist() for coeff in blue_coeffs]
    }

    # Save the dictionary to a file with the .pypvc extension
    if len(sys.argv) > 2:
        input_file = sys.argv[2]
        # Extract the file extension
        _, replacable = os.path.splitext(input_file)
    
        # Now you can use `replacable` in your replacement logic
        # Example usage
        output_file = filename.replace(replacable, '.pypvc')
        print(output_file)  # This will print 'example.pypvc' if filename was 'example.webm'
    else:
        print("Insufficient arguments provided.")
    with open(output_file, 'w') as f:  # Note the 'w' mode for writing text
        json.dump(coefficients_dict, f, indent=4)  # Pretty print the JSON
    gzip_compress(output_file)

def process_video_frames(video_path):
    # Lists to hold RGB values of all frames except the last one
    red_values, green_values, blue_values = [], [], []

    # Capture the video from the file
    cap = cv2.VideoCapture(video_path)

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Read frames in a loop
    for i in range(frame_count - 1):  # Skip the last frame
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame from BGR to RGB (OpenCV uses BGR by default)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Extract RGB channels
        red, green, blue = frame_rgb[:,:,0], frame_rgb[:,:,1], frame_rgb[:,:,2]
        
        # Append current frame's RGB values to lists
        red_values.append(red.flatten())
        green_values.append(green.flatten())
        blue_values.append(blue.flatten())

    # Release the video capture object
    cap.release()
    return red_values, green_values, blue_values

def main():
    video_directory = f"{sys.argv[1]}"
    filename_list = []
    for filename in os.listdir(video_directory):
        filename_list.append(filename)
    print(f"You have selected {len(filename_list)}, selecting file at position 0: {filename_list[0]}")
    video_path = os.path.join(video_directory, filename_list[0])
    if filename.endswith(f"{sys.argv[2]}"):
        r, g, b = process_video_frames(video_path)
        print(f"Processing {filename}:")
        queue_r = multiprocessing.Queue()
        queue_g = multiprocessing.Queue()
        queue_b = multiprocessing.Queue()
        processes = [multiprocessing.Process(target=polymatch, args=[r, "red", queue_r]), 
                    multiprocessing.Process(target=polymatch, args=[g, "green", queue_g]), 
                    multiprocessing.Process(target=polymatch, args=[b, "blue", queue_b])]
        for process in processes:
            process.start()
        polynomial_coefficients_r = queue_r.get()
        polynomial_coefficients_g = queue_g.get()
        polynomial_coefficients_b = queue_b.get()
        for process in processes:
            process.join()
            
        # Save the polynomial coefficients instead of RGB arrays
        save_coefficients(filename, polynomial_coefficients_r, polynomial_coefficients_g, polynomial_coefficients_b)

            
def polymatch(color, colorname, queue):
    length = len(color)
    if length == 0:
        print(f"No data to process for {colorname}.")
        return
    polynomial_coefficients = []
    for i in range(length):
        color_list = np.array(color[i], dtype=np.uint8)
        x = np.arange(len(color_list))
        coefficients = np.polyfit(x, color_list, 2)
        polynomial_coefficients.append(coefficients)
        
        # Calculate progress
        progress = ((i + 1) / length) * 100  # Adjusted to reflect completion of the current frame
        progress_bar = '-' * int(progress // 2) + ' ' * (50 - int(progress // 2))  # Shorter bar for compact display
        
        # Display progress update on the same line
        print(f"\r{progress:.2f}% [{progress_bar}] Fitted {colorname} - Frame {i+1}/{length}         ", end="")
    
    # Put polynomial_coefficients into the queue
    queue.put(polynomial_coefficients)
    
    # Newline for clean separation after processing is complete
    print(f"\nFinished fitting for {colorname}.")  

if __name__ == "__main__":
    main()
