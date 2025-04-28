from flask_login import UserMixin
from extensions import db
from datetime import datetime

class User(UserMixin, db.Model):  # ✅ Thêm UserMixin để hỗ trợ Flask-Login
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='applicant')  # ✅ Thêm role

    # ✅ Thêm thuộc tính is_active để Flask-Login nhận diện
    @property
    def is_active(self):
        return True  # Người dùng luôn active

    @property
    def is_authenticated(self):
        return True  # Người dùng đã xác thực

    @property
    def is_anonymous(self):
        return False  # Không phải người dùng ẩn danh

    def get_id(self):
        return str(self.id)  # Flask-Login cần hàm này để lấy ID người dùng



class Job(db.Model):
    __tablename__ = 'job'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.String(50), nullable=True)
    experience = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_featured = db.Column(db.Boolean, default=False)

    # ✅ Thêm dòng dưới đây:
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    logo_filename = db.Column(db.String(100))  # <--- thêm dòng này



class Application(db.Model):
    __tablename__ = 'application'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)  # ✅ Đảm bảo có dòng này
    cover_letter = db.Column(db.Text, nullable=False)
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)  # ✅ Đảm bảo có dòng này

    user = db.relationship('User', backref='applications')
    job = db.relationship('Job', backref='applications')
