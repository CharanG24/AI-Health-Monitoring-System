# Health Monitoring System

A Flask-based web application for monitoring patient vital signs and detecting anomalies using AI.

## Features

- Patient management (add, delete)
- Vital signs recording
- AI-powered anomaly detection
- Real-time analysis of vital signs
- User-friendly web interface

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. Initialize the database:
```bash
python app.py
```

2. The application will be available at `http://localhost:5000`

## Project Structure

- `app.py`: Main Flask application
- `ai_model.py`: AI model for anomaly detection
- `templates/`: HTML templates
- `static/`: CSS and JavaScript files
- `requirements.txt`: Python dependencies

## API Endpoints

- `GET /api/patients`: Get all patients
- `POST /api/patients`: Add a new patient
- `DELETE /api/patients/<id>`: Delete a patient
- `POST /api/patients/<id>/vitals`: Add vital signs for a patient
- `GET /api/patients/<id>/vitals`: Get vital signs for a patient
- `GET /api/patients/<id>/analysis`: Get AI analysis for a patient

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 