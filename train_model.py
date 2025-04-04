import tensorflow as tf
from tensorflow.keras import layers, Model
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import os

def create_autoencoder(input_dim):
    # Encoder
    input_layer = layers.Input(shape=(input_dim,))
    encoded = layers.Dense(64, activation='relu')(input_layer)
    encoded = layers.Dense(32, activation='relu')(encoded)
    encoded = layers.Dense(16, activation='relu')(encoded)
    
    # Decoder
    decoded = layers.Dense(32, activation='relu')(encoded)
    decoded = layers.Dense(64, activation='relu')(decoded)
    decoded = layers.Dense(input_dim, activation='linear')(decoded)
    
    # Create and compile the model
    autoencoder = Model(input_layer, decoded)
    autoencoder.compile(optimizer='adam', loss='mse')
    
    return autoencoder

def generate_synthetic_data(n_samples=1000):
    # Generate synthetic vital signs data
    np.random.seed(42)
    
    data = {
        'heart_rate': np.random.normal(75, 10, n_samples),
        'blood_pressure_systolic': np.random.normal(120, 10, n_samples),
        'blood_pressure_diastolic': np.random.normal(80, 8, n_samples),
        'temperature': np.random.normal(37, 0.5, n_samples),
        'oxygen_saturation': np.random.normal(98, 1, n_samples)
    }
    
    # Add some anomalies
    anomaly_indices = np.random.choice(n_samples, size=int(n_samples * 0.1), replace=False)
    for idx in anomaly_indices:
        data['heart_rate'][idx] = np.random.normal(120, 15, 1)
        data['blood_pressure_systolic'][idx] = np.random.normal(160, 20, 1)
        data['blood_pressure_diastolic'][idx] = np.random.normal(100, 15, 1)
        data['temperature'][idx] = np.random.normal(39, 1, 1)
        data['oxygen_saturation'][idx] = np.random.normal(90, 5, 1)
    
    return pd.DataFrame(data)

def main():
    # Create models directory if it doesn't exist
    os.makedirs('models', exist_ok=True)
    
    # Generate synthetic data
    data = generate_synthetic_data()
    
    # Scale the data
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data)
    
    # Create and train the model
    input_dim = scaled_data.shape[1]
    model = create_autoencoder(input_dim)
    
    # Train the model
    history = model.fit(
        scaled_data, scaled_data,
        epochs=50,
        batch_size=32,
        shuffle=True,
        validation_split=0.2
    )
    
    # Save the model
    model.save('models/anomaly_detection_model.h5')
    
    # Save the scaler
    import joblib
    joblib.dump(scaler, 'models/scaler.pkl')
    
    print("Model and scaler saved successfully!")

if __name__ == '__main__':
    main() 