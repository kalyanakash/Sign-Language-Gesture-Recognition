import os
import pickle
import mediapipe as mp
import cv2

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Increase min_detection_confidence for better hand detection
hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.2)

DATA_DIR = './data'

data = []
labels = []

for dir_ in os.listdir(DATA_DIR):
    for img_path in os.listdir(os.path.join(DATA_DIR, dir_)):
        data_aux = []
        x_ = []
        y_ = []

        # Read and Resize Image
        img = cv2.imread(os.path.join(DATA_DIR, dir_, img_path))
        img = cv2.resize(img, (640, 480))  # Resize to standard size
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Process with MediaPipe
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                for i in range(len(hand_landmarks.landmark)):
                    x = hand_landmarks.landmark[i].x
                    y = hand_landmarks.landmark[i].y
                    x_.append(x)
                    y_.append(y)

                for i in range(len(hand_landmarks.landmark)):
                    x = hand_landmarks.landmark[i].x
                    y = hand_landmarks.landmark[i].y
                    data_aux.append(x - min(x_))
                    data_aux.append(y - min(y_))

            data.append(data_aux)
            labels.append(dir_)
        else:
            print(f"Skipping {img_path}: No hands detected!")
            
            # Show image for debugging
            cv2.imshow("No Hand Detected", img)
            cv2.waitKey(500)  # Show for 500ms
            cv2.destroyAllWindows()

# Save data to pickle
with open('data.pickle', 'wb') as f:
    pickle.dump({'data': data, 'labels': labels}, f)

print("Dataset creation completed successfully!")
