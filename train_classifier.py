import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Load data from the pickle file
data_dict = pickle.load(open('./data.pickle', 'rb'))

# Extract data and labels
data = np.asarray(data_dict['data'])
labels = np.asarray(data_dict['labels'])

# Print sample data shape for debugging
print("Sample data shape:", data.shape)
print("Sample labels:", labels[:10])

# Flatten the data properly
data_flattened = np.array([np.array(d).flatten() for d in data])

# Split data into training and testing sets
x_train, x_test, y_train, y_test = train_test_split(
    data_flattened, labels, test_size=0.2, shuffle=True, stratify=labels
)

# Initialize the RandomForestClassifier with better parameters
model = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)

# Train the model
model.fit(x_train, y_train)

# Make predictions
y_predict = model.predict(x_test)

# Calculate accuracy
score = accuracy_score(y_test, y_predict)

# Print accuracy
print(f"Model Accuracy: {score * 100:.2f}%")

# Save the trained model along with metadata
with open('model.p', 'wb') as f:
    pickle.dump({'model': model, 'accuracy': score}, f)
