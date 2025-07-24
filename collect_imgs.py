import os
import cv2

# Directory for storing images
DATA_DIR = './data'
os.makedirs(DATA_DIR, exist_ok=True)

# Ask user for the class number to save data in
existing_classes = [d for d in os.listdir(DATA_DIR) if d.isdigit()]
print("Existing classes:", existing_classes)

while True:
    try:
        class_num = int(input("Enter the class number to save data in (or a new class number): "))
        break
    except ValueError:
        print("Please enter a valid class number.")

# Create directory for the chosen class if it doesn't exist
class_dir = os.path.join(DATA_DIR, str(class_num))
os.makedirs(class_dir, exist_ok=True)

print(f'Collecting data for Class {class_num}. Press "Q" to start!')

# Start webcam
cap = cv2.VideoCapture(0)

# Wait for user confirmation before starting
while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Couldn't read frame from webcam.")
        break

    # Show chosen class number on screen
    cv2.putText(frame, f'Class {class_num}: Press "Q" to Start!', (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow('frame', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break  # Start collecting images

# Number of images per class
dataset_size = 100
counter = 0

while counter < dataset_size:
    ret, frame = cap.read()
    if not ret:
        print("Error: Couldn't capture frame.")
        break

    # Resize for consistency (optional)
    frame = cv2.resize(frame, (224, 224))

    # Save image in PNG format in the chosen class folder
    img_path = os.path.join(class_dir, f'{counter}.png')
    cv2.imwrite(img_path, frame)

    counter += 1
    print(f"Saved {img_path} in Class {class_num}")

    # Show frame with progress and class number
    cv2.putText(frame, f'Class {class_num}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    cv2.putText(frame, f'Capturing {counter}/{dataset_size}', (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.imshow('frame', frame)

    # Wait before capturing next image
    cv2.waitKey(50)  # Adjust delay if needed

cap.release()
cv2.destroyAllWindows()
