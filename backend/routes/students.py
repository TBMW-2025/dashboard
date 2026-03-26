from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename
from models import db, Student, User
import os
import pandas as pd
import io

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
            department_course=data.get('department_course', ''),
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
                  'department_course', 'higher_education_plan', 'placement_status']

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

        # Read the file into pandas
        try:
            df = pd.read_excel(file)
        except Exception as e:
            return jsonify({'error': f'Failed to read Excel file: {str(e)}'}), 400

        # Standardize column mapping (case-insensitive and trimmed)
        column_mapping = {
            'Enrollment Number': 'enrollment_number',
            'Student Name': 'student_name',
            'Email ID': 'student_email_id',
            'Mobile Number': 'mobile_number',
            'Department & Course': 'department_course',
            'Higher Education Plan': 'higher_education_plan',
            'Placement Status': 'placement_status'
        }

        # Find actual columns in df that match our mapping
        df_cols = {col.strip(): col for col in df.columns}
        final_mapping = {}
        for friendly_name, model_attr in column_mapping.items():
            # Check for exact match or case-insensitive match
            found = False
            for actual_col in df_cols:
                if actual_col.lower() == friendly_name.lower():
                    final_mapping[actual_col] = model_attr
                    found = True
                    break
            if not found:
                # If required columns are missing, we should probably error or warn
                if model_attr in ['enrollment_number', 'student_name']:
                     return jsonify({'error': f'Missing required column: {friendly_name}'}), 400

        # Process rows
        success_count = 0
        duplicate_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                enrollment = str(row.get(next((c for c in df.columns if c.strip().lower() == 'enrollment number'), None), '')).strip()
                name = str(row.get(next((c for c in df.columns if c.strip().lower() == 'student name'), None), '')).strip()
                
                if not enrollment or enrollment == 'nan' or not name or name == 'nan':
                    continue

                # Check for existing student
                if Student.query.get(enrollment):
                    duplicate_count += 1
                    continue

                student = Student(
                    enrollment_number=enrollment,
                    student_name=name,
                    student_email_id=str(row.get(next((c for c in df.columns if c.strip().lower() == 'email id'), ''), '')).strip().replace('nan', ''),
                    mobile_number=str(row.get(next((c for c in df.columns if c.strip().lower() == 'mobile number'), ''), '')).strip().replace('nan', ''),
                    department_course=str(row.get(next((c for c in df.columns if c.strip().lower() == 'department & course'), ''), '')).strip().replace('nan', ''),
                    higher_education_plan=str(row.get(next((c for c in df.columns if c.strip().lower() == 'higher education plan'), 'No'), 'No')).strip().replace('nan', 'No'),
                    placement_status=str(row.get(next((c for c in df.columns if c.strip().lower() == 'placement status'), 'Not Placed'), 'Not Placed')).strip().replace('nan', 'Not Placed')
                )
                
                db.session.add(student)
                success_count += 1
                
                # Auto-create user account if email exists (similar to reset-password logic)
                if student.student_email_id:
                    existing_user = User.query.filter_by(email=student.student_email_id).first()
                    if not existing_user:
                        user = User(
                            username=student.enrollment_number,
                            email=student.student_email_id,
                            mobile=student.mobile_number,
                            role='student'
                        )
                        user.set_password('Student@123') # Default password
                        db.session.add(user)

            except Exception as row_e:
                errors.append(f"Row {index + 2}: {str(row_e)}")

        db.session.commit()
        
        return jsonify({
            'message': f'Import completed: {success_count} added, {duplicate_count} skipped.',
            'success_count': success_count,
            'duplicate_count': duplicate_count,
            'errors': errors
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
