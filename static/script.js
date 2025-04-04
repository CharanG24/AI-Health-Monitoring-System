document.addEventListener('DOMContentLoaded', function() {
    const addPatientForm = document.getElementById('addPatientForm');
    const vitalsForm = document.getElementById('vitalsForm');
    const patientList = document.getElementById('patientList');
    const patientSelect = document.getElementById('patientSelect');
    const vitalsList = document.getElementById('vitalsList');
    const anomalyScore = document.getElementById('anomalyScore');
    const anomalyStatus = document.getElementById('anomalyStatus');
    const anomalyDetails = document.getElementById('anomalyDetails');
    const addVitalsBtn = document.getElementById('addVitalsBtn');
    let currentPatientId = null;

    function loadPatients() {
        fetch('/api/patients')
            .then(response => response.json())
            .then(patients => {
                patientList.innerHTML = '';
                patientSelect.innerHTML = '<option value="">Select a patient</option>';
                
                patients.forEach(patient => {
                    const option = document.createElement('option');
                    option.value = patient.id;
                    option.textContent = `${patient.name} (${patient.age} years)`;
                    patientSelect.appendChild(option);

                    const li = document.createElement('li');
                    li.className = 'list-group-item d-flex justify-content-between align-items-center';
                    li.innerHTML = `
                        ${patient.name} (${patient.age} years)
                        <div>
                            <button class="btn btn-sm btn-danger" onclick="deletePatient(${patient.id})">Delete</button>
                        </div>
                    `;
                    patientList.appendChild(li);
                });

                if (patients.length > 0) {
                    const firstPatient = patients[0];
                    currentPatientId = firstPatient.id;
                    patientSelect.value = firstPatient.id;
                    addVitalsBtn.disabled = false;
                    loadVitals(firstPatient.id);
                } else {
                    currentPatientId = null;
                    addVitalsBtn.disabled = true;
                    clearVitalsDisplay();
                }
            });
    }

    function clearVitalsDisplay() {
        vitalsList.innerHTML = '<li class="list-group-item">No vital signs recorded yet.</li>';
        anomalyScore.textContent = '0%';
        anomalyStatus.textContent = 'Normal';
        anomalyStatus.className = 'text-success';
        anomalyDetails.innerHTML = 'No anomalies detected';
    }

    function loadVitals(patientId) {
        if (!patientId) {
            clearVitalsDisplay();
            return;
        }

        fetch(`/api/patients/${patientId}/vitals`)
            .then(response => response.json())
            .then(vitals => {
                vitalsList.innerHTML = '';
                if (vitals.length === 0) {
                    vitalsList.innerHTML = '<li class="list-group-item">No vital signs recorded yet.</li>';
                    clearVitalsDisplay();
                    return;
                }

                const latestVital = vitals[0];  // Get the most recent vital signs
                const roundedScore = Math.round((latestVital.anomaly_score || 0) * 100);
                
                anomalyScore.textContent = `${roundedScore}%`;
                anomalyStatus.textContent = (latestVital.anomaly_score || 0) >= 0.5 ? 'Anomaly Detected' : 'Normal';
                anomalyStatus.className = (latestVital.anomaly_score || 0) >= 0.5 ? 'text-danger' : 'text-success';
                anomalyDetails.innerHTML = latestVital.analysis && latestVital.analysis.length > 0 ? 
                    `<ul>${latestVital.analysis.map(item => `<li>${item}</li>`).join('')}</ul>` : 
                    'No anomalies detected';

                vitals.forEach(vital => {
                    const li = document.createElement('li');
                    li.className = 'list-group-item';
                    
                    // Validate and format vital signs
                    const formattedVitals = {
                        heart_rate: vital.heart_rate ? `${vital.heart_rate} bpm` : 'N/A',
                        blood_pressure: vital.blood_pressure_systolic && vital.blood_pressure_diastolic ? 
                            `${vital.blood_pressure_systolic}/${vital.blood_pressure_diastolic} mmHg` : 'N/A',
                        temperature: vital.temperature ? `${vital.temperature}°C` : 'N/A',
                        oxygen_saturation: vital.oxygen_saturation ? `${vital.oxygen_saturation}%` : 'N/A',
                        anomaly_score: vital.anomaly_score ? `${Math.round(vital.anomaly_score * 100)}%` : '0%',
                        status: (vital.anomaly_score || 0) >= 0.5 ? 'Anomaly Detected' : 'Normal'
                    };

                    li.innerHTML = `
                        <div class="d-flex justify-content-between">
                            <div>
                                <strong>Date:</strong> ${new Date(vital.timestamp).toLocaleString()}<br>
                                <strong>Heart Rate:</strong> ${formattedVitals.heart_rate}<br>
                                <strong>Blood Pressure:</strong> ${formattedVitals.blood_pressure}<br>
                                <strong>Temperature:</strong> ${formattedVitals.temperature}<br>
                                <strong>Oxygen Saturation:</strong> ${formattedVitals.oxygen_saturation}
                            </div>
                            <div>
                                <strong>Anomaly Score:</strong> ${formattedVitals.anomaly_score}<br>
                                <strong>Status:</strong> ${formattedVitals.status}
                            </div>
                        </div>
                        ${vital.analysis && vital.analysis.length > 0 ? `
                            <div class="mt-2">
                                <strong>Analysis:</strong>
                                <ul>
                                    ${vital.analysis.map(item => `<li>${item}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    `;
                    vitalsList.appendChild(li);
                });
            })
            .catch(error => {
                console.error('Error loading vitals:', error);
                vitalsList.innerHTML = '<li class="list-group-item text-danger">Error loading vital signs.</li>';
                clearVitalsDisplay();
            });
    }

    window.onPatientSelect = function(patientId) {
        currentPatientId = patientId;
        addVitalsBtn.disabled = !patientId;
        if (patientId) {
            loadVitals(patientId);
        } else {
            clearVitalsDisplay();
        }
    };

    window.showAddVitalsModal = function() {
        if (currentPatientId) {
            document.getElementById('patientId').value = currentPatientId;
            document.getElementById('vitalsModal').style.display = 'block';
        }
    };

    window.deletePatient = function(patientId) {
        if (confirm('Are you sure you want to delete this patient?')) {
            fetch(`/api/patients/${patientId}`, {
                method: 'DELETE'
            })
            .then(response => {
                if (response.ok) {
                    loadPatients();
                }
            });
        }
    };

    addPatientForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        const patientData = {
            name: formData.get('name'),
            age: parseInt(formData.get('age')),
            gender: formData.get('gender')
        };

        fetch('/api/patients', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(patientData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                this.reset();
                loadPatients();
            }
        });
    });

    vitalsForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        
        // Input validation
        const vitalsData = {
            heart_rate: parseFloat(formData.get('heart_rate')),
            blood_pressure_systolic: parseFloat(formData.get('blood_pressure_systolic')),
            blood_pressure_diastolic: parseFloat(formData.get('blood_pressure_diastolic')),
            temperature: parseFloat(formData.get('temperature')),
            oxygen_saturation: parseFloat(formData.get('oxygen_saturation'))
        };

        // Validate ranges
        if (vitalsData.heart_rate < 30 || vitalsData.heart_rate > 200) {
            alert('Heart rate must be between 30 and 200 bpm');
            return;
        }
        if (vitalsData.blood_pressure_systolic < 70 || vitalsData.blood_pressure_systolic > 200) {
            alert('Systolic blood pressure must be between 70 and 200 mmHg');
            return;
        }
        if (vitalsData.blood_pressure_diastolic < 40 || vitalsData.blood_pressure_diastolic > 130) {
            alert('Diastolic blood pressure must be between 40 and 130 mmHg');
            return;
        }
        if (vitalsData.temperature < 30 || vitalsData.temperature > 45) {
            alert('Temperature must be between 30 and 45°C');
            return;
        }
        if (vitalsData.oxygen_saturation < 70 || vitalsData.oxygen_saturation > 100) {
            alert('Oxygen saturation must be between 70 and 100%');
            return;
        }

        const patientId = formData.get('patientId');

        fetch(`/api/patients/${patientId}/vitals`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(vitalsData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                this.reset();
                document.getElementById('vitalsModal').style.display = 'none';
                loadVitals(patientId);
                const roundedScore = Math.round(data.anomaly_score * 100);
                anomalyScore.textContent = `${roundedScore}%`;
                anomalyStatus.textContent = data.anomaly_score >= 0.5 ? 'Anomaly Detected' : 'Normal';
                anomalyStatus.className = data.anomaly_score >= 0.5 ? 'text-danger' : 'text-success';
                anomalyDetails.innerHTML = data.analysis && data.analysis.length > 0 ? 
                    `<ul>${data.analysis.map(item => `<li>${item}</li>`).join('')}</ul>` : 
                    'No anomalies detected';
            }
        })
        .catch(error => {
            console.error('Error submitting vitals:', error);
            alert('Error submitting vital signs. Please try again.');
        });
    });

    document.querySelector('.close').addEventListener('click', function() {
        document.getElementById('vitalsModal').style.display = 'none';
    });

    loadPatients();
}); 