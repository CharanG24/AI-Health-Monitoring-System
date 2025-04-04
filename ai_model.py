import numpy as np
import os
import json

class AnomalyDetector:
    def __init__(self):
        self.stats = None
        if os.path.exists('models/stats.json'):
            with open('models/stats.json', 'r') as f:
                self.stats = json.load(f)

    def train(self, vitals_data):
        if len(vitals_data) < 10:
            return False
        vital_signs = ['heart_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic', 
                      'temperature', 'oxygen_saturation']
        stats = {}
        for vital in vital_signs:
            values = [v[vital] for v in vitals_data]
            stats[vital] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values))
            }
        self.stats = stats
        os.makedirs('models', exist_ok=True)
        with open('models/stats.json', 'w') as f:
            json.dump(stats, f)
        return True

    def get_vital_ranges(self):
        return {
            'heart_rate': (60, 100),
            'blood_pressure_systolic': (90, 120),
            'blood_pressure_diastolic': (60, 80),
            'temperature': (36.1, 37.2),
            'oxygen_saturation': (95, 100)
        }

    def analyze_vitals(self, vitals):
        ranges = self.get_vital_ranges()
        analysis = []
        severity_score = 0
        abnormal_count = 0

        if vitals['heart_rate'] < ranges['heart_rate'][0]:
            analysis.append("Heart rate is below normal range (bradycardia)")
            severity_score += 0.2
            abnormal_count += 1
        elif vitals['heart_rate'] > ranges['heart_rate'][1]:
            analysis.append("Heart rate is above normal range (tachycardia)")
            severity_score += 0.2
            abnormal_count += 1

        if vitals['blood_pressure_systolic'] > ranges['blood_pressure_systolic'][1]:
            analysis.append("High systolic blood pressure (hypertension)")
            severity_score += 0.3
            abnormal_count += 1
        elif vitals['blood_pressure_systolic'] < ranges['blood_pressure_systolic'][0]:
            analysis.append("Low systolic blood pressure (hypotension)")
            severity_score += 0.3
            abnormal_count += 1

        if vitals['blood_pressure_diastolic'] > ranges['blood_pressure_diastolic'][1]:
            analysis.append("High diastolic blood pressure (hypertension)")
            severity_score += 0.3
            abnormal_count += 1
        elif vitals['blood_pressure_diastolic'] < ranges['blood_pressure_diastolic'][0]:
            analysis.append("Low diastolic blood pressure (hypotension)")
            severity_score += 0.3
            abnormal_count += 1

        # Enhanced temperature analysis
        temp_diff = vitals['temperature'] - ranges['temperature'][1]
        if temp_diff > 0:
            if temp_diff > 5:
                analysis.append("Severe fever (critical)")
                severity_score += 0.8
            elif temp_diff > 2:
                analysis.append("High fever")
                severity_score += 0.6
            else:
                analysis.append("Elevated temperature (fever)")
                severity_score += 0.4
            abnormal_count += 1
        elif vitals['temperature'] < ranges['temperature'][0]:
            analysis.append("Low temperature (hypothermia)")
            severity_score += 0.4
            abnormal_count += 1

        if vitals['oxygen_saturation'] < ranges['oxygen_saturation'][0]:
            analysis.append("Low oxygen saturation (hypoxemia)")
            severity_score += 0.4
            abnormal_count += 1

        # Calculate base severity score
        base_severity = severity_score

        # Apply multipliers for multiple conditions
        if abnormal_count > 1:
            severity_score = base_severity * 1.3
        if abnormal_count > 2:
            severity_score *= 1.4

        # Ensure minimum score for critical conditions
        if any("critical" in condition.lower() for condition in analysis):
            severity_score = max(severity_score, 0.8)
        elif any(condition in analysis for condition in ["fever", "hypertension", "hypotension"]):
            severity_score = max(severity_score, 0.6)

        # Ensure the score is properly capped
        return analysis, min(1.0, severity_score)

    def predict_anomaly(self, vitals):
        analysis, severity_score = self.analyze_vitals(vitals)
        
        if self.stats is None:
            return severity_score, severity_score >= 0.5
            
        z_scores = []
        for vital, value in vitals.items():
            if vital in self.stats:
                z_score = abs(value - self.stats[vital]['mean']) / max(self.stats[vital]['std'], 1e-6)
                z_scores.append(z_score)
        
        stat_score = float(np.mean(z_scores)) if z_scores else 0.0
        stat_score = min(1.0, stat_score / 2.0)  # Reduced divisor to increase sensitivity
        
        # Combine severity and statistical scores with more weight on severity
        final_score = max(severity_score, stat_score * 0.5 + severity_score * 0.5)
        
        # Ensure minimum score for critical conditions
        if any("critical" in condition.lower() for condition in analysis):
            final_score = max(final_score, 0.8)
        elif any(condition in analysis for condition in ["fever", "hypertension", "hypotension"]):
            final_score = max(final_score, 0.6)
            
        # Ensure the score is properly capped and returned
        final_score = min(1.0, final_score)
        return final_score, final_score >= 0.5 