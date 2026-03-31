from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import generate_password_hash
from datetime import datetime

db = SQLAlchemy()

class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    two_factor_enabled = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'two_factor_enabled': self.two_factor_enabled
        }

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        try:
            from flask_bcrypt import check_password_hash
            return check_password_hash(self.password_hash, password)
        except ValueError:
            from werkzeug.security import check_password_hash as werkzeug_check
            return werkzeug_check(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'mobile': self.mobile,
            'role': self.role
        }

class Otp(db.Model):
    __tablename__ = 'otps'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email_otp = db.Column(db.String(10), nullable=False)
    mobile_otp = db.Column(db.String(10), nullable=False)
    expiry_time = db.Column(db.Float, nullable=False)

    user = db.relationship('User', backref=db.backref('otps', lazy=True, cascade='all, delete-orphan'))


class Student(db.Model):
    __tablename__ = 'students'
    enrollment_number = db.Column(db.String(50), primary_key=True)
    student_name = db.Column(db.String(120), nullable=False)
    student_email_id = db.Column(db.String(120))
    mobile_number = db.Column(db.String(20))
    programme = db.Column(db.String(150))
    higher_education_plan = db.Column(db.String(10))
    placement_status = db.Column(db.String(10), default='Not Placed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships mapped for compatibility with old structure if needed
    internships = db.relationship('Internship', backref='student', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'enrollment_number': self.enrollment_number,
            'student_name': self.student_name,
            'student_email_id': self.student_email_id,
            'mobile_number': self.mobile_number,
            'programme': self.programme,
            'higher_education_plan': self.higher_education_plan,
            'placement_status': self.placement_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Company(db.Model):
    __tablename__ = 'companies'
    company_id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120))
    contact_person = db.Column(db.String(120))
    contact = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'company_id': self.company_id,
            'company_name': self.company_name,
            'role': self.role,
            'contact_person': self.contact_person,
            'contact': self.contact,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Placement(db.Model):
    __tablename__ = 'placed_students'
    enrollment_number = db.Column(db.String(50), db.ForeignKey('students.enrollment_number'), primary_key=True)
    student_name = db.Column(db.String(120))
    company = db.Column(db.String(120))
    role = db.Column(db.String(120))
    placement_date = db.Column(db.String(50))
    salary_lpa = db.Column(db.Float)
    status = db.Column(db.String(50), default='Placed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='placement_record', uselist=False)

    def to_dict(self):
        return {
            'enrollment_number': self.enrollment_number,
            'student_name': self.student_name,
            'programme': self.student.programme if self.student else None,
            'company': self.company,
            'role': self.role,
            'placement_date': self.placement_date,
            'salary_lpa': self.salary_lpa,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Internship(db.Model):
    __tablename__ = 'internships'
    id = db.Column(db.Integer, primary_key=True)
    enrollment_number = db.Column(db.String(50), db.ForeignKey('students.enrollment_number'), nullable=False)
    year = db.Column(db.String(10))
    programme = db.Column(db.String(100))
    gender = db.Column(db.String(20))
    internship_place = db.Column(db.String(255))
    internship_place_02 = db.Column(db.String(255))
    organization_type = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'enrollment_number': self.enrollment_number,
            'student_name': self.student.student_name if self.student else None,
            'year': self.year,
            'programme': self.programme,
            'gender': self.gender,
            'internship_place': self.internship_place,
            'internship_place_02': self.internship_place_02,
            'organization_type': self.organization_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
