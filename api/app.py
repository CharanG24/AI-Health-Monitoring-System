from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from ai_model import AnomalyDetector
import os

app = Flask(__name__)
CORS(app)

anomaly_detector = AnomalyDetector()

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///health_monitoring.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    vitals = db.relationship('VitalSigns', backref='patient', lazy=True, cascade='all, delete-orphan')

class VitalSigns(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    heart_rate = db.Column(db.Float, nullable=False)
    blood_pressure_systolic = db.Column(db.Float, nullable=False)
    blood_pressure_diastolic = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    oxygen_saturation = db.Column(db.Float, nullable=False)

def init_db():
    with app.app_context():
        db_dir = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/patients', methods=['GET'])
def get_all_patients():
    patients = Patient.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'age': p.age,
        'gender': p.gender,
        'created_at': p.created_at.isoformat(),
        'vitals': [{
            'timestamp': v.timestamp.isoformat(),
            'heart_rate': v.heart_rate,
            'blood_pressure_systolic': v.blood_pressure_systolic,
            'blood_pressure_diastolic': v.blood_pressure_diastolic,
            'temperature': v.temperature,
            'oxygen_saturation': v.oxygen_saturation
        } for v in p.vitals]
    } for p in patients])

@app.route('/api/patients', methods=['POST'])
def create_patient():
    try:
        data = request.get_json()

        if not data.get('name') or not data.get('age') or not data.get('gender'):
            return jsonify({'error': 'Missing required fields'}), 400
            
        if data['age'] < 0:
            return jsonify({'error': 'Age cannot be negative'}), 400
            
        if data['gender'] not in ['M', 'F', 'O']:
            return jsonify({'error': 'Invalid gender value'}), 400
            
        new_patient = Patient(
            name=data['name'],
            age=data['age'],
            gender=data['gender']
        )
        db.session.add(new_patient)
        db.session.commit()
        return jsonify({'message': 'Patient created successfully', 'id': new_patient.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    try:
        patient = Patient.query.get_or_404(patient_id)
        db.session.delete(patient)
        db.session.commit()
        return jsonify({'message': 'Patient deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients/<int:patient_id>/vitals', methods=['POST'])
def add_vitals(patient_id):
    try:
        data = request.get_json()
        
        required_fields = ['heart_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic', 
                         'temperature', 'oxygen_saturation']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
            if data[field] < 0:
                return jsonify({'error': f'{field} cannot be negative'}), 400
        
        new_vitals = VitalSigns(
            patient_id=patient_id,
            heart_rate=data['heart_rate'],
            blood_pressure_systolic=data['blood_pressure_systolic'],
            blood_pressure_diastolic=data['blood_pressure_diastolic'],
            temperature=data['temperature'],
            oxygen_saturation=data['oxygen_saturation']
        )
        
        anomaly_score, is_anomaly = anomaly_detector.predict_anomaly(data)
        analysis, _ = anomaly_detector.analyze_vitals(data)  # Get only the analysis list
        
        db.session.add(new_vitals)
        db.session.commit()

        all_vitals = VitalSigns.query.all()
        vitals_data = [({
            'heart_rate': v.heart_rate,
            'blood_pressure_systolic': v.blood_pressure_systolic,
            'blood_pressure_diastolic': v.blood_pressure_diastolic,
            'temperature': v.temperature,
            'oxygen_saturation': v.oxygen_saturation
        }) for v in all_vitals]
        
        anomaly_detector.train(vitals_data)
        
        return jsonify({
            'message': 'Vitals recorded successfully',
            'anomaly_detected': is_anomaly,
            'anomaly_score': anomaly_score,
            'analysis': analysis
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients/<int:patient_id>/vitals', methods=['GET'])
def get_patient_vitals(patient_id):
    vitals = VitalSigns.query.filter_by(patient_id=patient_id).order_by(VitalSigns.timestamp.desc()).all()
    return jsonify([{
        'timestamp': v.timestamp.isoformat(),
        'heart_rate': v.heart_rate,
        'blood_pressure_systolic': v.blood_pressure_systolic,
        'blood_pressure_diastolic': v.blood_pressure_diastolic,
        'temperature': v.temperature,
        'oxygen_saturation': v.oxygen_saturation,
        'anomaly_score': anomaly_detector.predict_anomaly({
            'heart_rate': v.heart_rate,
            'blood_pressure_systolic': v.blood_pressure_systolic,
            'blood_pressure_diastolic': v.blood_pressure_diastolic,
            'temperature': v.temperature,
            'oxygen_saturation': v.oxygen_saturation
        })[0],
        'analysis': anomaly_detector.analyze_vitals({
            'heart_rate': v.heart_rate,
            'blood_pressure_systolic': v.blood_pressure_systolic,
            'blood_pressure_diastolic': v.blood_pressure_diastolic,
            'temperature': v.temperature,
            'oxygen_saturation': v.oxygen_saturation
        })[0]
    } for v in vitals])

@app.route('/api/patients/<int:patient_id>/analysis', methods=['GET'])
def get_patient_analysis(patient_id):
    latest_vitals = VitalSigns.query.filter_by(patient_id=patient_id).order_by(VitalSigns.timestamp.desc()).first()
    
    if not latest_vitals:
        return jsonify({'message': 'No vitals found for this patient'}), 404
        
    vitals_data = {
        'heart_rate': latest_vitals.heart_rate,
        'blood_pressure_systolic': latest_vitals.blood_pressure_systolic,
        'blood_pressure_diastolic': latest_vitals.blood_pressure_diastolic,
        'temperature': latest_vitals.temperature,
        'oxygen_saturation': latest_vitals.oxygen_saturation
    }
    
    anomaly_score, is_anomaly = anomaly_detector.predict_anomaly(vitals_data)
    analysis, _ = anomaly_detector.analyze_vitals(vitals_data)  # Get only the analysis list
    
    return jsonify({
        'timestamp': latest_vitals.timestamp.isoformat(),
        'vitals': vitals_data,
        'anomaly_detected': is_anomaly,
        'anomaly_score': anomaly_score,
        'analysis': analysis
    })

# The following line allows the app to work with Vercel's serverless function
from vercel_wsgi import make_lambda_handler
handler = make_lambda_handler(app)

# Ensuring the app only runs locally during development
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
