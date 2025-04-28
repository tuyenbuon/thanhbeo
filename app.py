
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db  # Import db từ extensions.py
from models import User, Job, Application
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask import Flask
import os



app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)  # ✅ Đảm bảo gọi init_app(app) đúng cách

# Cấu hình Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # ✅ Trả về user từ database

@app.context_processor
def inject_user():
    return dict(user=current_user)

@app.route('/')
def main_page():
    jobs = Job.query.order_by(Job.date_posted.desc()).limit(10).all()
    featured_jobs = Job.query.filter_by(is_featured=True).limit(5).all()
    return render_template('main.html', jobs=jobs, featured_jobs=featured_jobs)


# Trang chủ hiển thị danh sách công việc
@app.route('/home')
def home():
    query = request.args.get('query', '').strip()
    location = request.args.get('location', '').strip()
    job_type = request.args.get('job_type', '')
    salary_min = request.args.get('salary_min', type=int)
    salary_max = request.args.get('salary_max', type=int)
    experience = request.args.get('experience', '')

    jobs = Job.query

    if query:
        jobs = jobs.filter(Job.title.ilike(f"%{query}%"))
    if location:
        jobs = jobs.filter(Job.location.ilike(f"%{location}%"))
    if job_type:
        jobs = jobs.filter_by(job_type=job_type)
    if salary_min is not None:
        jobs = jobs.filter(Job.salary >= salary_min)
    if salary_max is not None:
        jobs = jobs.filter(Job.salary <= salary_max)
    if experience:
        jobs = jobs.filter(Job.experience.ilike(f"%{experience}%"))

    jobs = jobs.all()

    return render_template('index.html', jobs=jobs, user=current_user)

# Đăng ký tài khoản
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role') or 'user'  # hoặc 'admin' tùy

        if not username or not email or not password:
            flash('Vui lòng nhập đầy đủ thông tin.')
            return render_template('register.html')

        # Hash mật khẩu
        hashed_password = generate_password_hash(password)

        # Tạo người dùng mới
        new_user = User(username=username, email=email, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Đăng ký thành công!')
        return redirect(url_for('login'))

    return render_template('register.html')


# Đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Sai email hoặc mật khẩu!', 'danger')

    return render_template('login.html')


# Đăng xuất
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đăng xuất thành công!', 'success')
    return redirect(url_for('home'))

# Đăng tin tuyển dụng
@app.route('/add_job', methods=['GET', 'POST'])
@login_required
def add_job():
    if current_user.role != 'recruiter':  # ✅ Kiểm tra quyền
        flash('Chỉ nhà tuyển dụng mới có thể đăng tin!', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        location = request.form['location']
        salary = request.form['salary']
        experience = request.form['experience']
        description = request.form['description']

        logo_file = request.files.get('logo')
        logo_filename = None

        if logo_file and allowed_file(logo_file.filename):
            filename = secure_filename(logo_file.filename)
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            logo_file.save(logo_path)
            logo_filename = filename

        new_job = Job(
            title=title,
            company=company,
            location=location,
            salary=salary,
            experience=experience,
            description=description,
            logo_filename=logo_filename  # Thêm logo vào đây
        )

        db.session.add(new_job)
        db.session.commit()

        flash('Tin tuyển dụng đã được đăng!', 'success')
        return redirect(url_for('home'))

    return render_template('post_job.html')  # ❗ Luôn có return khi GET


@app.route('/edit_job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    if request.method == 'POST':
        job.title = request.form['title']
        job.description = request.form['description']
        job.experience = request.form['experience']
        job.salary = request.form['salary']
        job.location = request.form['location']
        db.session.commit()
        return redirect(url_for('job_list'))
    return render_template('edit_job.html', job=job)



# Xóa tin tuyển dụng
@app.route('/delete_job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    if current_user.role != 'recruiter':  # ✅ Kiểm tra quyền
        flash('Chỉ nhà tuyển dụng mới có thể đăng tin!', 'danger')
        return redirect(url_for('home'))

    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash('Công việc đã bị xóa!', 'danger')
    return redirect(url_for('home'))

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('job_detail.html', job=job)

# Ứng tuyển công việc
@app.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    job = Job.query.get_or_404(job_id)
    phone_number = request.form['phone_number']  # ✅ Lấy số điện thoại từ form
    cover_letter = request.form['cover_letter']

    new_application = Application(
        user_id=current_user.id,
        job_id=job_id,
        phone_number=phone_number,  # ✅ Lưu số điện thoại
        cover_letter=cover_letter,
        applied_date=datetime.utcnow()  # ✅ Lưu ngày ứng tuyển
    )

    db.session.add(new_application)
    db.session.commit()

    flash('Ứng tuyển thành công!', 'success')
    return redirect(url_for('job_detail', job_id=job_id))


# Xem danh sách ứng viên đã ứng tuyển vào công việc
@app.route('/job/<int:job_id>/applications')
@login_required
def view_applications(job_id):
    job = Job.query.get_or_404(job_id)
    applications = Application.query.filter_by(job_id=job_id).all()
    return render_template('applications.html', job=job, applications=applications)

@app.route('/job_list')
def job_list():
    jobs = Job.query.all()
    return render_template('job_list.html', jobs=jobs)


@app.route('/create_job')
def create_job():
    return render_template("create_job.html")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # ✅ Chỉ gọi một lần duy nhất
    app.run(debug=True)
