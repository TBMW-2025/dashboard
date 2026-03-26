from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, Placement, Student
import pandas as pd

placements_bp = Blueprint('placements', __name__)


@placements_bp.route('', methods=['GET'])
@jwt_required()
def get_placements():
    try:
        placements = Placement.query.order_by(Placement.created_at.desc()).all()
        return jsonify([p.to_dict() for p in placements]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@placements_bp.route('', methods=['POST'])
@jwt_required()
def add_placement():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        enrollment_number = data.get('enrollment_number')
        company = data.get('company')

        if not enrollment_number:
            return jsonify({'error': 'enrollment_number is required'}), 400
        if not company:
            return jsonify({'error': 'company is required'}), 400

        student = Student.query.get(enrollment_number)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # ── Prevent duplicate: if a record already exists, update it instead ──
        existing = Placement.query.get(enrollment_number)
        if existing:
            existing.company = company
            existing.role = data.get('role', existing.role or '')
            existing.placement_date = data.get('placement_date', existing.placement_date or '')
            if data.get('salary_lpa'):
                existing.salary_lpa = data['salary_lpa']
            existing.status = data.get('status', existing.status or 'Placed')

            if existing.status == 'Placed':
                student.placement_status = 'Yes'

            db.session.commit()
            return jsonify(existing.to_dict()), 200

        # ── New placement record ───────────────────────────────────────────────
        placement = Placement(
            enrollment_number=enrollment_number,
            student_name=student.student_name,
            company=company,
            role=data.get('role', ''),
            placement_date=data.get('placement_date', ''),
            salary_lpa=data.get('salary_lpa'),
            status=data.get('status', 'Placed')
        )

        if placement.status == 'Placed':
            student.placement_status = 'Yes'

        db.session.add(placement)
        db.session.commit()
        return jsonify(placement.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@placements_bp.route('/<string:enrollment_number>', methods=['PUT'])
@jwt_required()
def update_placement(enrollment_number):
    try:
        placement = Placement.query.get(enrollment_number)
        if not placement:
            return jsonify({'error': 'Placement not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        for field in ['company', 'role', 'placement_date', 'salary_lpa', 'status']:
            if field in data:
                setattr(placement, field, data[field])

        # Sync student placement_status
        new_status = data.get('status')
        if new_status:
            student = Student.query.get(placement.enrollment_number)
            if student:
                student.placement_status = 'Yes' if new_status == 'Placed' else 'No'

        db.session.commit()
        return jsonify(placement.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@placements_bp.route('/<string:enrollment_number>', methods=['DELETE'])
@jwt_required()
def delete_placement(enrollment_number):
    try:
        placement = Placement.query.get(enrollment_number)
        if not placement:
            return jsonify({'error': 'Placement not found'}), 404

        # Reset the student's placement status
        student = Student.query.get(enrollment_number)
        if student:
            student.placement_status = 'No'

        db.session.delete(placement)
        db.session.commit()
        return jsonify({'message': 'Placement deleted'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@placements_bp.route('/import', methods=['POST'])
@jwt_required()
def import_placements():
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

        success_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                enroll = str(row.get(next((c for c in df.columns if 'enrol' in c.strip().lower()), ''), '')).strip()
                if not enroll or enroll == 'nan':
                    name = str(row.get(next((c for c in df.columns if 'student name' in c.strip().lower()), ''), '')).strip()
                    if name and name != 'nan':
                        student_match = Student.query.filter_by(student_name=name).first()
                        if student_match:
                            enroll = student_match.enrollment_number
                
                if not enroll or enroll == 'nan':
                    continue

                student = Student.query.get(enroll)
                if not student:
                    errors.append(f"Row {index + 2}: Student {enroll} not found.")
                    continue

                company_name = str(row.get(next((c for c in df.columns if 'company' in c.strip().lower()), ''), '')).strip().replace('nan', '')
                if not company_name:
                    continue

                existing = Placement.query.get(enroll)
                if existing:
                    existing.company = company_name
                    existing.role = str(row.get(next((c for c in df.columns if 'role' in c.strip().lower()), ''), '')).strip().replace('nan', '')
                    existing.placement_date = str(row.get(next((c for c in df.columns if 'date' in c.strip().lower()), ''), '')).strip().replace('nan', '')
                    salary = row.get(next((c for c in df.columns if 'salary' in c.strip().lower()), None))
                    if pd.notnull(salary):
                        existing.salary_lpa = float(salary)
                    existing.status = str(row.get(next((c for c in df.columns if 'status' in c.strip().lower()), 'Placed'), 'Placed')).strip().replace('nan', 'Placed')
                    if existing.status == 'Placed':
                        student.placement_status = 'Yes'
                else:
                    new_placement = Placement(
                        enrollment_number=enroll,
                        student_name=student.student_name,
                        company=company_name,
                        role=str(row.get(next((c for c in df.columns if 'role' in c.strip().lower()), ''), '')).strip().replace('nan', ''),
                        placement_date=str(row.get(next((c for c in df.columns if 'date' in c.strip().lower()), ''), '')).strip().replace('nan', ''),
                        status=str(row.get(next((c for c in df.columns if 'status' in c.strip().lower()), 'Placed'), 'Placed')).strip().replace('nan', 'Placed')
                    )
                    salary = row.get(next((c for c in df.columns if 'salary' in c.strip().lower()), None))
                    if pd.notnull(salary):
                        new_placement.salary_lpa = float(salary)
                    
                    if new_placement.status == 'Placed':
                        student.placement_status = 'Yes'
                    db.session.add(new_placement)
                
                success_count += 1
            except Exception as row_e:
                errors.append(f"Row {index + 2}: {str(row_e)}")

        db.session.commit()
        return jsonify({
            'message': f'Import completed: {success_count} records processed.',
            'success_count': success_count,
            'errors': errors
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
