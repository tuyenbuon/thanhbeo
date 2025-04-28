from app import db, app
from models import Job

with app.app_context():
    print(Job.__table__.columns.keys())  # Xem danh sách cột trong bảng job
