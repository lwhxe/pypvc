User
import cv2
import os
import numpy as np
import multiprocessing
import pickle

def save_coefficients(filename, red_coeffs, green_coeffs, blue_coeffs):
    # Create a dictionary to hold the coefficients
    coefficients_dict = {
        'red': red_coeffs,
        'green': green_coeffs,
        'blue': blue_coeffs
    }

    # Save the dictionary to a file with the .pypvc extension
    output_file = filename.replace('.webm', '.pypvc')
    with open(output_file, 'wb') as f:
        # Encode coefficients to ASCII before pickling
        coefficients_dict_encoded = {
            key: [coeff.tobytes().decode('latin1') for coeff in value] for key, value in coefficients_dict.items()
        }
        pickle.dump(coefficients_dict_encoded, f)

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
    video_directory = 'F:/pypvc/videos'
    for filename in os.listdir(video_directory):
        if filename.endswith('.webm'):  # Ensure processing only video files
            video_path = os.path.join(video_directory, filename)
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
                
            save_coefficients(filename, r, g, b)
            
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
