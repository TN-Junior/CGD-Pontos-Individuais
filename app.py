from flask import Flask
from config import Config
from extensions import db, migrate
import pytz
from apscheduler.schedulers.background import BackgroundScheduler

# Configuração do aplicativo Flask
app = Flask(__name__)
app.config.from_object(Config)


db.init_app(app)
migrate.init_app(app, db)


timezone = pytz.timezone('America/Recife')
scheduler = BackgroundScheduler(timezone=timezone)


from routes import *
from models import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(host='0.0.0.0', port=5000, debug=True)
