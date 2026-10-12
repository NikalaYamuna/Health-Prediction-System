from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

@app.route('/report')
def generate_report():
    # Example user data
    user_data = {
        'name': 'G.Madhavi',
        'age': 19,
        'height': '155 cm',
        'weight': '42 kg',
        'email': 'gumpumadhu@email.com',
        'health_conditions': {
            'mental': 'Anxiety Disorders',
            'metabolic': 'Diabetes',
            'respiratory': 'Asthma',
            'reproductive': 'Endometriosis',
            'lifestyle': 'Non-Vegetarian, Moderate Activity',
            'family_history': 'Breast Cancer, Diabetes'
        },
        'ai_risk_prediction': {
            'moderate_risk_cardio': True,
            'regular_diabetes_screening': True,
            'respiratory_checkup_needed': True
        },
        'recommendations': [
            'Book a consultation with a gynecologist for Endometriosis symptoms.',
            'Schedule regular blood sugar and cholesterol checks.',
            'Follow a personalized workout and stress management plan.',
            'Increase fiber-rich and anti-inflammatory foods in your diet.'
        ]
    }

    # Pass data to the frontend template
    return render_template('health_report.html', user=user_data)

if __name__ == '__main__':
    app.run(debug=True)
