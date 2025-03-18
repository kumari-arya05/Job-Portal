from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bootstrap import Bootstrap5
from models import db, User, Job, Application
from forms import LoginForm, RegisterForm, JobForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Replace with a secure random string
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
Bootstrap5(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return redirect(url_for('job_list'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:  # Plain text for simplicity; use hashing in production
            login_user(user)
            return redirect(url_for('job_list'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists')
        else:
            user = User(username=form.username.data, password=form.password.data, role=form.role.data)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/jobs', methods=['GET'])
def job_list():
    jobs = Job.query.all()
    return render_template('job_list.html', jobs=jobs)

@app.route('/job/post', methods=['GET', 'POST'])
@login_required
def job_post():
    if current_user.role != 'employer':
        flash('Only employers can post jobs.')
        return redirect(url_for('job_list'))
    form = JobForm()
    if form.validate_on_submit():
        job = Job(
            title=form.title.data,
            description=form.description.data,
            salary=form.salary.data,
            location=form.location.data,
            employer_id=current_user.id
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully!')
        return redirect(url_for('job_list'))
    return render_template('job_post.html', form=form)

@app.route('/job/apply/<int:job_id>', methods=['POST'])
@login_required
def job_apply(job_id):
    if current_user.role != 'job_seeker':
        flash('Only job seekers can apply.')
        return redirect(url_for('job_list'))
    if Application.query.filter_by(job_id=job_id, user_id=current_user.id).first():
        flash('You have already applied for this job.')
    else:
        application = Application(job_id=job_id, user_id=current_user.id)
        db.session.add(application)
        db.session.commit()
        flash('Application submitted successfully!')
    return redirect(url_for('job_list'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
