from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename
from models import db, Student, User, Placement
import os
import pandas as pd
import io
from datetime import datetime

students_bp = Blueprint('students', __name__)


@students_bp.route('/<string:enrollment_number>/reset-password', methods=['POST'])
@jwt_required()
def reset_student_password(enrollment_number):
    try:
        from models import User
        student = Student.query.get(enrollment_number)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        data = request.get_json() or {}
        new_password = data.get('new_password')
        if not new_password:
            return jsonify({'error': 'New password is required'}), 400

        user = User.query.filter_by(email=student.student_email_id).first()
        if not user:
            user = User(
                username=student.enrollment_number,
                email=student.student_email_id,
                mobile=student.mobile_number,
                role='student'
            )
            db.session.add(user)

        user.set_password(new_password)
        db.session.commit()

        print("\n" + "="*60)
        print(f"🔐 [ADMIN RESET] Password reset for {user.username} (Student: {student.student_name})")
        print(f"   🔑 New Password: {new_password}")
        print("="*60 + "\n")

        return jsonify({'message': f'Password reset successfully for {student.student_name}.'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@students_bp.route('', methods=['GET'])
@jwt_required()
def get_students():
    try:
        students = Student.query.order_by(Student.enrollment_number.asc()).all()
        return jsonify([s.to_dict() for s in students]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@students_bp.route('', methods=['POST'])
@jwt_required()
def create_student():
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required = ['student_name', 'enrollment_number', 'student_email_id']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        if Student.query.filter_by(enrollment_number=data['enrollment_number']).first():
            return jsonify({'error': 'Enrollment number already exists'}), 409

        student = Student(
            student_name=data['student_name'],
            enrollment_number=data['enrollment_number'],
            student_email_id=data.get('student_email_id', ''),
            mobile_number=data.get('mobile_number', ''),
            programme=data.get('programme', ''),
            higher_education_plan=data.get('higher_education_plan', 'No'),
            placement_status=data.get('placement_status', 'Not Placed')
        )
        db.session.add(student)
        db.session.commit()
        return jsonify(student.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@students_bp.route('/<string:enrollment_number>', methods=['PUT'])
@jwt_required()
def update_student(enrollment_number):
    try:
        student = Student.query.get(enrollment_number)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        fields = ['student_name', 'enrollment_number', 'student_email_id', 'mobile_number',
                  'programme', 'higher_education_plan', 'placement_status']

        for field in fields:
            if field in data:
                setattr(student, field, data[field])

        db.session.commit()
        return jsonify(student.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@students_bp.route('/<string:enrollment_number>', methods=['DELETE'])
@jwt_required()
def delete_student(enrollment_number):
    try:
        student = Student.query.get(enrollment_number)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        db.session.delete(student)
        db.session.commit()
        return jsonify({'message': 'Student deleted'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@students_bp.route('/import', methods=['POST'])
@jwt_required()
def import_students():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Invalid file format. Please upload an Excel file (.xlsx or .xls)'}), 400

        try:
            df = pd.read_excel(file)
        except Exception as e:
            return jsonify({'error': f'Failed to read Excel file: {str(e)}'}), 400

        # Helper to find columns with variations
        def get_col(candidates):
            for cand in candidates:
                match = next((c for c in df.columns if str(c).strip().lower() == cand.strip().lower()), None)
                if match: return match
            return None

        col_enroll = get_col(['Enrollment Number', 'Enrolment No', 'Enrolment No.', 'Enrollment', 'Enrollment No.'])
        col_name = get_col(['Student Name', 'Name', 'Name of Student'])
        col_email = get_col(['Email ID', 'Email', 'Student Email'])
        col_mobile = get_col(['Mobile Number', 'Contact', 'Phone', 'Mobile No.'])
        col_programme = get_col(['Programme', 'Department & Course', 'Department', 'Course'])
        col_higher = get_col(['Higher Education Plan', 'Planning for Higher Education?', 'Higher Education'])
        col_placed = get_col(['Placement Status', 'Placed or Not'])
        col_company = get_col(['Company', 'Placed Company', 'Organization'])
        col_role = get_col(['Role', 'Designation', 'Job Role'])
        col_salary = get_col(['Salary', 'LPA', 'CTC', 'Package'])
        col_date = get_col(['Placement Date', 'Date of Placement', 'Date'])

        if not col_enroll or not col_name:
            return jsonify({'error': 'Required columns (Enrollment/Name) not found in the Excel file.'}), 400

        success_count = 0
        updated_count = 0
        row_errors = []

        for index, row in df.iterrows():
            try:
                enrollment = str(row.get(col_enroll, '')).strip()
                name = str(row.get(col_name, '')).strip()
                
                if not enrollment or enrollment.lower() == 'nan' or not name or name.lower() == 'nan':
                    continue

                student = Student.query.get(enrollment)
                is_new = False
                if not student:
                    student = Student(enrollment_number=enrollment)
                    db.session.add(student)
                    is_new = True
                
                # Update core fields
                student.student_name = name
                if col_email: student.student_email_id = str(row.get(col_email, '')).strip().replace('nan', '')
                if col_mobile: student.mobile_number = str(row.get(col_mobile, '')).strip().replace('nan', '')
                if col_programme: student.programme = str(row.get(col_programme, '')).strip().replace('nan', '')
                if col_higher: student.higher_education_plan = str(row.get(col_higher, 'No')).strip().replace('nan', 'No')
                
                # Update placement status (Yes / No)
                p_status = str(row.get(col_placed, 'No')).strip().replace('nan', 'No')
                if p_status.lower() in ['yes', 'placed']:
                    student.placement_status = 'Yes'
                else:
                    student.placement_status = 'No'

                # Sync User creation/update
                if student.student_email_id:
                    u = User.query.filter_by(username=student.enrollment_number).first()
                    if not u:
                        u = User(username=student.enrollment_number, email=student.student_email_id, mobile=student.mobile_number, role='student')
                        u.set_password('Student@123')
                        db.session.add(u)
                    else:
                        u.email = student.student_email_id
                        u.mobile = student.mobile_number

                # Sync Placement Table for "Yes" students
                if student.placement_status == 'Yes':
                    p_rec = Placement.query.get(student.enrollment_number)
                    if not p_rec:
                        p_rec = Placement(enrollment_number=student.enrollment_number)
                        db.session.add(p_rec)
                    
                    p_rec.student_name = student.student_name
                    # Only update if columns exist in the Excel
                    if col_company: p_rec.company = str(row.get(col_company, 'Unknown')).strip().replace('nan', 'Unknown')
                    if col_role: p_rec.role = str(row.get(col_role, 'Unknown')).strip().replace('nan', 'Unknown')
                    
                    if col_salary:
                        try:
                            s_val = str(row.get(col_salary, '0')).strip().lower().replace('nan', '0').split(' ')[0]
                            p_rec.salary_lpa = float(s_val) if s_val else 0.0
                        except:
                            p_rec.salary_lpa = 0.0
                    
                    if col_date:
                        p_date = str(row.get(col_date, '')).strip().replace('nan', '')
                        if p_date: p_rec.placement_date = p_date
                    
                    if not p_rec.placement_date:
                        p_rec.placement_date = datetime.now().strftime('%Y-%m-%d')
                    
                    p_rec.status = 'Placed'
                else:
                    # If status is "No", remove from placement table if exists
                    p_rec = Placement.query.get(student.enrollment_number)
                    if p_rec:
                        db.session.delete(p_rec)

                if is_new: success_count += 1
                else: updated_count += 1
                
                db.session.commit()
            except Exception as row_e:
                db.session.rollback()
                row_errors.append(f"Row {index + 2}: {str(row_e)}")

        return jsonify({
            'message': f'Import completed: {success_count} added, {updated_count} updated.',
            'success_count': success_count,
            'updated_count': updated_count,
            'errors': row_errors
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
