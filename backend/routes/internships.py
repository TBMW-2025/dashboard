from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, Internship, Student, Company
import pandas as pd

internships_bp = Blueprint('internships', __name__)


@internships_bp.route('', methods=['GET'])
@jwt_required()
def get_internships():
    try:
        internships = Internship.query.order_by(Internship.created_at.desc()).all()
        return jsonify([i.to_dict() for i in internships]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@internships_bp.route('', methods=['POST'])
@jwt_required()
def create_internship():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required = ['enrollment_number'] # reduced requirements
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        if not Student.query.get(data['enrollment_number']):
            return jsonify({'error': 'Student not found'}), 404
        
        company_id = data.get('company_id')
        if company_id and not Company.query.get(company_id):
            return jsonify({'error': 'Company not found'}), 404

        internship = Internship(
            enrollment_number=data['enrollment_number'],
            company_id=company_id,
            year=data.get('year', ''),
            programme=data.get('programme', ''),
            gender=data.get('gender', ''),
            internship_place=data.get('internship_place', ''),
            internship_place_02=data.get('internship_place_02', ''),
            organization_type=data.get('organization_type', ''),
            role=data.get('role', ''),
            duration=data.get('duration', ''),
            start_date=data.get('start_date', ''),
            status=data.get('status', 'Active'),
            stipend=float(data['stipend']) if data.get('stipend') else None
        )
        db.session.add(internship)
        db.session.commit()
        return jsonify(internship.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@internships_bp.route('/<int:internship_id>', methods=['PUT'])
@jwt_required()
def update_internship(internship_id):
    try:
        internship = Internship.query.get(internship_id)
        if not internship:
            return jsonify({'error': 'Internship not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        fields = ['year', 'programme', 'gender', 'internship_place', 
                  'internship_place_02', 'organization_type', 
                  'role', 'duration', 'start_date', 'status', 'stipend', 'company_id']

        for field in fields:
            if field in data:
                val = float(data[field]) if field == 'stipend' and data[field] else data.get(field)
                setattr(internship, field, val)

        db.session.commit()
        return jsonify(internship.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@internships_bp.route('/<int:internship_id>', methods=['DELETE'])
@jwt_required()
def delete_internship(internship_id):
    try:
        internship = Internship.query.get(internship_id)
        if not internship:
            return jsonify({'error': 'Internship not found'}), 404
        db.session.delete(internship)
        db.session.commit()
        return jsonify({'message': 'Internship deleted'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@internships_bp.route('/import', methods=['POST'])
@jwt_required()
def import_internships():
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

        # Headers: Year, Enrolment No., Programme, Name of Student, Gender, Internship Place, Internship Place 02, Type of Organization
        success_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                enrollment = str(row.get(next((c for c in df.columns if c.strip().lower() == 'enrolment no.'), None), '')).strip()
                if not enrollment or enrollment == 'nan':
                    # try 'enrollment number' just in case
                    enrollment = str(row.get(next((c for c in df.columns if 'enrollment' in c.strip().lower()), None), '')).strip()
                
                if not enrollment or enrollment == 'nan':
                    continue

                if not Student.query.get(enrollment):
                    errors.append(f"Row {index + 2}: Student with enrolment {enrollment} not found.")
                    continue

                internship = Internship(
                    enrollment_number=enrollment,
                    year=str(row.get(next((c for c in df.columns if c.strip().lower() == 'year'), ''), '')).strip().replace('nan', ''),
                    programme=str(row.get(next((c for c in df.columns if c.strip().lower() == 'programme'), ''), '')).strip().replace('nan', ''),
                    gender=str(row.get(next((c for c in df.columns if c.strip().lower() == 'gender'), ''), '')).strip().replace('nan', ''),
                    internship_place=str(row.get(next((c for c in df.columns if c.strip().lower() == 'internship place'), ''), '')).strip().replace('nan', ''),
                    internship_place_02=str(row.get(next((c for c in df.columns if c.strip().lower() == 'internship place 02'), ''), '')).strip().replace('nan', ''),
                    organization_type=str(row.get(next((c for c in df.columns if 'organization' in c.strip().lower()), ''), '')).strip().replace('nan', ''),
                    status='Completed'
                )
                db.session.add(internship)
                success_count += 1
            except Exception as row_e:
                errors.append(f"Row {index + 2}: {str(row_e)}")

        db.session.commit()
        return jsonify({
            'message': f'Import completed: {success_count} added.',
            'success_count': success_count,
            'errors': errors
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
