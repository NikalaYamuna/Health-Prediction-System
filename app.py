import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid
import logging

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database and upload configuration

db_user = os.getenv("DB_USER", "root")
db_password = quote_plus(os.getenv("DB_PASSWORD", ""))
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "3307")
db_name = os.getenv("DB_NAME", "health_db")

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{db_user}:{db_password}@"
    f"{db_host}:{db_port}/{db_name}"
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Dummy users dictionary
users = {
    'Yamuna': '123456',
    'madhavi': '789012',
    'manisha': '78345',
    'sahithi': '23567',
    'maibu': '56743',
}

# Database models
class HealthInput(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    height = db.Column(db.Float, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    contact = db.Column(db.String(100), nullable=True)
    dietary = db.Column(db.String(50), nullable=True)
    activity = db.Column(db.String(50), nullable=True)
    smoking = db.Column(db.String(10), nullable=True)
    alcohol = db.Column(db.String(10), nullable=True)
    sleep = db.Column(db.Integer, nullable=True)
    stress = db.Column(db.String(50), nullable=True)
    consent = db.Column(db.Boolean)
    file_path = db.Column(db.String(255), nullable=True)
    mental_health = db.Column(db.String(300), nullable=True)
    metabolic_health = db.Column(db.String(300), nullable=True)
    respiratory_health = db.Column(db.String(300), nullable=True)
    urinary_health = db.Column(db.String(300), nullable=True)
    digestive_health = db.Column(db.String(300), nullable=True)
    skin_hair_health = db.Column(db.String(300), nullable=True)
    bone_joint_health = db.Column(db.String(300), nullable=True)
    cardiovascular_health = db.Column(db.String(300), nullable=True)
    breast_health = db.Column(db.String(300), nullable=True)
    reproductive_health = db.Column(db.String(300), nullable=True)
    family_history = db.Column(db.String(300), nullable=True)

class ConsultationRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    specialist = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    preferred_date = db.Column(db.Date, nullable=False)
    preferred_time = db.Column(db.Time, nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Mock hospital data
hospitals = [
    {"name": "Apollo Hospital", "address": "Jubilee Hills, Hyderabad, Telangana", "phone": "+91-40-23607777", "city": "Hyderabad", "specialists": ["gynecologist", "endocrinologist", "general"]},
    {"name": "Fortis Hospital", "address": "Bannerghatta Road, Bangalore, Karnataka", "phone": "+91-80-66214444", "city": "Bangalore", "specialists": ["gynecologist", "mental-health", "pulmonologist"]},
    {"name": "Care Hospital", "address": "Banjara Hills, Hyderabad, Telangana", "phone": "+91-40-30418888", "city": "Hyderabad", "specialists": ["endocrinologist", "general", "pulmonologist"]},
    {"name": "Manipal Hospital", "address": "Old Airport Road, Bangalore, Karnataka", "phone": "+91-80-25024444", "city": "Bangalore", "specialists": ["gynecologist", "mental-health", "general"]}
]

# Helper functions
def to_yes_no(value):
    if not value:
        return 'no'
    val = str(value).lower()
    return 'yes' if val in ['yes', 'true', 'on', '1'] else 'no'

def split_condition(cond_str):
    if cond_str:
        return [item.strip() for item in cond_str.split(',') if item.strip()]
    return []

def filter_health_conditions(conditions):
    if not conditions:
        return []
    if 'None' in conditions and len(conditions) > 1:
        return [c for c in conditions if c != 'None']
    return conditions

@app.route('/')
def login():
    logger.info("Rendering login page")
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    userid = request.form.get('userid')
    password = request.form.get('password')
    logger.info(f"Login attempt: userid={userid}")
    if userid in users and users[userid] == password:
        session['userid'] = userid
        flash(f"Welcome {userid}!", "success")
        logger.info(f"Login successful for user: {userid}")
        return redirect(url_for('home'))
    flash("Invalid credentials. Please try again.", "danger")
    logger.warning(f"Login failed for userid={userid}")
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'userid' not in session:
        flash("Please login first.", "warning")
        logger.warning("Redirecting to login: session['userid'] missing")
        return redirect(url_for('login'))
    logger.info(f"Rendering home page for user: {session['userid']}")
    return render_template('home.html', userid=session['userid'])

@app.route('/input', methods=['GET', 'POST'])
def input_page():
    if 'userid' not in session:
        flash("Please login first.", "warning")
        logger.warning("Redirecting to login: session['userid'] missing")
        return redirect(url_for('login'))
    logger.info(f"Accessing /input for user: {session['userid']}")
    if request.method == 'POST':
        try:
            logger.info("Form data received: %s", request.form)
            logger.info("Files received: %s", request.files)
            required_fields = ['full_name', 'age', 'height', 'weight', 'contact']
            for field in required_fields:
                if not request.form.get(field):
                    raise ValueError(f"Missing required field: {field}")
            file = request.files.get('lab_reports')
            file_path = ''
            if file and file.filename:
                unique_name = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
                saved_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                file.save(saved_path)
                file_path = saved_path.replace('\\', '/')
                logger.info(f"File saved at: {file_path}")
            age = int(request.form.get('age'))
            height = float(request.form.get('height'))
            weight = float(request.form.get('weight'))
            sleep = int(request.form.get('sleep_hours')) if request.form.get('sleep_hours') else None
            logger.info(f"Converted values: age={age}, height={height}, weight={weight}, sleep={sleep}")
            health_fields = [
                'mental_health', 'metabolic_health', 'respiratory_health', 'urinary_health',
                'digestive_health', 'skin_hair_health', 'bone_joint_health', 'cardiovascular_health',
                'breast_health', 'reproductive_health', 'family_history'
            ]
            health_conditions = {field: filter_health_conditions(request.form.getlist(field)) for field in health_fields}
            logger.info("Health conditions: %s", health_conditions)
            new_entry = HealthInput(
                full_name=request.form.get('full_name'),
                age=age,
                height=height,
                weight=weight,
                contact=request.form.get('contact'),
                dietary=request.form.get('diet') or None,
                activity=request.form.get('physical_activity') or None,
                smoking=to_yes_no(request.form.get('smoking')),
                alcohol=to_yes_no(request.form.get('alcohol')),
                sleep=sleep,
                stress=request.form.get('stress_level') or None,
                consent=request.form.get('consent') == 'on',
                file_path=file_path,
                mental_health=', '.join(health_conditions['mental_health']),
                metabolic_health=', '.join(health_conditions['metabolic_health']),
                respiratory_health=', '.join(health_conditions['respiratory_health']),
                urinary_health=', '.join(health_conditions['urinary_health']),
                digestive_health=', '.join(health_conditions['digestive_health']),
                skin_hair_health=', '.join(health_conditions['skin_hair_health']),
                bone_joint_health=', '.join(health_conditions['bone_joint_health']),
                cardiovascular_health=', '.join(health_conditions['cardiovascular_health']),
                breast_health=', '.join(health_conditions['breast_health']),
                reproductive_health=', '.join(health_conditions['reproductive_health']),
                family_history=', '.join(health_conditions['family_history']),
            )
            db.session.add(new_entry)
            db.session.commit()
            logger.info("Database entry committed successfully")
            session['last_id'] = new_entry.id
            logger.info(f"Set session['last_id'] = {new_entry.id}")
            flash("Form submitted successfully!", "success")
            return redirect(url_for('report_page'))
        except ValueError as ve:
            flash(f"Validation error: {str(ve)}", "danger")
            logger.error(f"Validation error: {str(ve)}")
            return redirect(url_for('input_page'))
        except Exception as e:
            flash(f"Error processing the form: {type(e).__name__}: {str(e)}", "danger")
            logger.error(f"Form processing error: {type(e).__name__}: {str(e)}")
            return redirect(url_for('input_page'))
    return render_template('input.html', userid=session['userid'])

@app.route('/report')
def report_page():
    if 'userid' not in session:
        flash("Please login first.", "warning")
        logger.warning("Redirecting to login: session['userid'] missing")
        return redirect(url_for('login'))
    logger.info(f"Accessing /report for user: {session['userid']}")
    latest_id = session.get('last_id')
    logger.info(f"Retrieved session['last_id'] = {latest_id}")
    if not latest_id:
        flash("No recent report found.", "info")
        return redirect(url_for('input_page'))
    latest = HealthInput.query.get(latest_id)
    if not latest:
        flash("Data not found for the report.", "warning")
        logger.warning(f"No HealthInput found for ID {latest_id}")
        return redirect(url_for('input_page'))
    session.pop('last_id', None)
    ai_risks = {
        'moderate_cardio_risk': 'High Blood Pressure' in split_condition(latest.cardiovascular_health) or latest.smoking == 'yes',
        'diabetes_screening_needed': 'Diabetes' in split_condition(latest.metabolic_health),
        'respiratory_checkup_needed': 'Asthma' in split_condition(latest.respiratory_health),
        'cancer_screening_recommended': bool(latest.breast_health) or bool(latest.family_history),
        'bone_health_monitoring': bool(latest.bone_joint_health),
        'reproductive_health_checkup': bool(latest.reproductive_health),
        'urinary_health_monitoring': bool(latest.urinary_health),
        'digestive_health_monitoring': bool(latest.digestive_health),
        'skin_hair_health_monitoring': bool(latest.skin_hair_health),
    }
    recommendations = []
    if latest.sleep and latest.sleep < 6:
        recommendations.append("Increase sleep to at least 7-8 hours.")
    if latest.stress and latest.stress.lower() in ['high']:
        recommendations.append("Practice stress-reducing activities.")
    if latest.smoking == 'yes':
        recommendations.append("Consider quitting smoking.")
    if latest.alcohol == 'yes':
        recommendations.append("Limit alcohol intake.")
    if not recommendations:
        recommendations.append("Maintain a healthy and active lifestyle.")
    report_data = {
        'name': latest.full_name,
        'age': latest.age,
        'height': latest.height,
        'weight': latest.weight,
        'email': latest.contact,
        'file_path': latest.file_path,
        'consent': latest.consent,
        'lifestyle': {
            'diet': latest.dietary or 'None',
            'activity': latest.activity or 'None',
            'smoking': latest.smoking or 'No',
            'alcohol': latest.alcohol or 'No',
            'sleep': latest.sleep,
            'stress': latest.stress or 'None'
        },
        'health_conditions': {
            'mental_health': split_condition(latest.mental_health),
            'metabolic_health': split_condition(latest.metabolic_health),
            'respiratory_health': split_condition(latest.respiratory_health),
            'urinary_health': split_condition(latest.urinary_health),
            'digestive_health': split_condition(latest.digestive_health),
            'skin_hair_health': split_condition(latest.skin_hair_health),
            'bone_joint_health': split_condition(latest.bone_joint_health),
            'cardiovascular_health': split_condition(latest.cardiovascular_health),
            'breast_health': split_condition(latest.breast_health),
            'reproductive_health': split_condition(latest.reproductive_health),
            'family_history': split_condition(latest.family_history),
        },
        'ai_risk_prediction': ai_risks,
        'recommendations': recommendations
    }
    session['report_data'] = report_data
    logger.info("Report data prepared: %s", report_data)
    try:
        return render_template('report.html', user=report_data)
    except Exception as e:
        flash(f"Error rendering report page: {type(e).__name__}: {str(e)}", "danger")
        logger.error(f"Template rendering error: {type(e).__name__}: {str(e)}")
        return redirect(url_for('input_page'))

@app.route('/recom')
def recom_page():
    if 'userid' not in session:
        flash("Please login first.", "warning")
        logger.warning("Redirecting to login: session['userid'] missing")
        return redirect(url_for('login'))
    logger.info(f"Accessing /recom for user: {session['userid']}")
    data = session.get('report_data')
    if not data:
        flash("No data found for recommendations.", "info")
        return redirect(url_for('input_page'))
    return render_template('recom.html', user=data)

@app.route('/consultation')
def consultation():
    if 'userid' not in session:
        flash("Please login first.", "warning")
        logger.warning("Redirecting to login from /consultation: session['userid'] missing")
        return redirect(url_for('login'))
    logger.info(f"Attempting to render consult.html for user: {session['userid']}")
    try:
        template_path = os.path.join(app.template_folder, 'consult.html')
        if not os.path.exists(template_path):
            logger.error(f"Template consult.html not found at: {template_path}")
            flash("Consultation page not found.", "danger")
            return redirect(url_for('home'))
        logger.info(f"Rendering consult.html from: {template_path}")
        return render_template('consult.html', userid=session['userid'])
    except Exception as e:
        flash(f"Error rendering consultation page: {type(e).__name__}: {str(e)}", "danger")
        logger.error(f"Template rendering error: {type(e).__name__}: {str(e)}")
        return redirect(url_for('home'))

@app.route('/book_consultation', methods=['POST'])
def book_consultation():
    if 'userid' not in session:
        flash("Please login first.", "warning")
        logger.warning("Redirecting to login from /book_consultation: session['userid'] missing")
        return redirect(url_for('login'))
    try:
        logger.info("Form data received: %s", request.form)
        name = request.form.get('name')
        email = request.form.get('email')
        specialist = request.form.get('specialist')
        location = request.form.get('location')
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        message = request.form.get('message')
        if not all([name, email, specialist, location, date_str, time_str, message]):
            raise ValueError("All fields are required.")
        preferred_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        preferred_time = datetime.strptime(time_str, '%H:%M').time()
        new_request = ConsultationRequest(
            user_id=session['userid'],
            name=name,
            email=email,
            specialist=specialist,
            location=location,
            preferred_date=preferred_date,
            preferred_time=preferred_time,
            message=message
        )
        db.session.add(new_request)
        db.session.commit()
        logger.info("Consultation request saved successfully")
        flash("Consultation request submitted successfully!", "success")
        return redirect(url_for('consultation'))
    except ValueError as ve:
        flash(f"Error: {str(ve)}", "danger")
        logger.error(f"Validation error: {str(ve)}")
        return redirect(url_for('consultation'))
    except Exception as e:
        flash(f"Error processing request: {type(e).__name__}: {str(e)}", "danger")
        logger.error(f"Form processing error: {type(e).__name__}: {str(e)}")
        return redirect(url_for('consultation'))

@app.route('/get_hospitals')
def get_hospitals():
    specialist = request.args.get('specialist')
    location = request.args.get('location', '').lower()
    logger.info(f"Fetching hospitals for specialist={specialist}, location={location}")
    if not specialist or not location:
        return jsonify([])
    filtered_hospitals = [
        hospital for hospital in hospitals
        if location in hospital['city'].lower() and specialist in hospital['specialists']
    ]
    logger.info(f"Returning {len(filtered_hospitals)} hospitals")
    return jsonify(filtered_hospitals)

@app.route('/about')
def about():
    if 'userid' not in session:
        flash("Please login first.", "warning")
        logger.warning("Redirecting to login from /about: session['userid'] missing")
        return redirect(url_for('login'))
    logger.info(f"Accessing /about for user: {session['userid']}")
    return render_template('about.html', userid=session['userid'])

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    logger.info("User logged out")
    return redirect(url_for('login'))

@app.route('/test_db')
def test_db():
    try:
        db.session.execute('SELECT 1')
        logger.info("Database connection test successful")
        return "Database connection successful!"
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return f"Database error: {str(e)}"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)