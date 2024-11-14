from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Enum, desc
import pytz

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lpg_monitor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

IST = pytz.timezone('Asia/Kolkata')


class Alerts(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(Enum('low level', 'gas leak', 'gas leak and low level', name='alert_type_enum'), nullable=False)
    concentration = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime, default=lambda: datetime.now(IST))

    def __repr__(self):
        return f"<Alert {self.id} - Type: {self.alert_type} - Concentration: {self.concentration} - Weight: {self.weight} - Time: {self.time}>"


class LPG_data(db.Model):
    __tablename__ = 'lpg_data'

    id = db.Column(db.Integer, primary_key=True)
    concentration = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<LPG Data - Concentration: {self.concentration} - Weight: {self.weight}>"

@app.route('/api/lpg-data', methods=['POST'])
def receive_data():
    data = request.get_json()
    concentration = data.get('concentration')
    weight = data.get('weight')

    if concentration and weight:
        lpg_data = LPG_data(concentration=concentration, weight=weight)
        db.session.add(lpg_data)
        db.session.commit()

        print(f"Received concentration: {concentration} ppm, weight: {weight} kg")

        return jsonify({"status": "success", "concentration": concentration, "weight": weight}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid or missing data"}), 400


@app.route('/')
def home():
    latest_data = LPG_data.query.order_by(desc(LPG_data.id)).first()

    if latest_data:
        concentration = latest_data.concentration
        level = latest_data.weight
    else:
        concentration = level = 0
    alert_type = None

    if concentration > 250 and level < 10:
        alert_type = 'gas leak and low level'
    elif concentration > 250:
        alert_type = 'gas leak'
    elif level < 10:
        alert_type = 'low level'

    if alert_type:
        alert = Alerts(alert_type=alert_type, concentration=concentration, weight=level)
        db.session.add(alert)
        db.session.commit()

    return render_template('index.html', concentration=concentration, level=level)


@app.route('/alerts')
def alerts():
    alerts = Alerts.query.order_by(desc(Alerts.time)).all()
    return render_template('alerts.html', alerts=alerts)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
