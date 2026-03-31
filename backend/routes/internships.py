from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, Internship, Student, Company
import pandas as pd
from sqlalchemy import or_

internships_bp = Blueprint('internships', __name__)


@internships_bp.route('', methods=['GET'])
@jwt_required()
def get_internships():
    try:
        prog = request.args.get('programme')
        query = Internship.query.order_by(Internship.created_at.desc())
        
        if prog:
            if prog == 'BCPA':
                query = query.join(Student, Internship.enrollment_number == Student.enrollment_number).filter(
                    or_(
                        Student.programme.like("%BCPA%"),
                        Student.programme.like("%BCPS%"),
                        Student.programme.like("%BACPA%")
                    )
                )
            else:
                query = query.join(Student, Internship.enrollment_number == Student.enrollment_number).filter(Student.programme.like(f"%{prog}%"))
            
        internships = query.all()
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
            year=data.get('year', ''),
            programme=data.get('programme', ''),
            gender=data.get('gender', ''),
            internship_place=data.get('internship_place', ''),
            internship_place_02=data.get('internship_place_02', ''),
            organization_type=data.get('organization_type', '')
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
                  'internship_place_02', 'organization_type']

        for field in fields:
            if field in data:
                setattr(internship, field, data.get(field))

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

        def get_col(candidates):
            for cand in candidates:
                match = next((c for c in df.columns if str(c).strip().lower() == cand.strip().lower()), None)
                if match: return match
            return None

        col_enroll = get_col(['Enrolment No.', 'Enrolment No', 'Enrollment Number', 'Enrollment', 'Student Enrollment'])
        col_year = get_col(['Year'])
        col_prog = get_col(['Programme', 'Program', 'Course'])
        col_gender = get_col(['Gender'])
        col_place1 = get_col(['Internship Place', 'Place', 'Organization'])
        col_place2 = get_col(['Internship Place 02', 'Secondary Place'])
        col_org_type = get_col(['Type of Organization', 'Org Type', 'Organization Type'])

        if not col_enroll:
            return jsonify({'error': 'Required column (Enrolment No.) not found in the Excel file.'}), 400

        success_count = 0
        updated_count = 0
        row_errors = []

        for index, row in df.iterrows():
            try:
                enrollment = str(row.get(col_enroll, '')).strip()
                if not enrollment or enrollment.lower() == 'nan':
                    continue

                if not Student.query.get(enrollment):
                    row_errors.append(f"Row {index + 2}: Student {enrollment} not found.")
                    continue

                year = str(row.get(col_year, '')).strip().replace('nan', '') if col_year else ''
                
                # Try to find existing record for this student and year
                internship = Internship.query.filter_by(enrollment_number=enrollment, year=year).first()
                is_new = False
                if not internship:
                    internship = Internship(enrollment_number=enrollment, year=year)
                    db.session.add(internship)
                    is_new = True
                
                if col_prog: internship.programme = str(row.get(col_prog, '')).strip().replace('nan', '')
                if col_gender: internship.gender = str(row.get(col_gender, '')).strip().replace('nan', '')
                if col_place1: internship.internship_place = str(row.get(col_place1, '')).strip().replace('nan', '')
                if col_place2: internship.internship_place_02 = str(row.get(col_place2, '')).strip().replace('nan', '')
                if col_org_type: internship.organization_type = str(row.get(col_org_type, '')).strip().replace('nan', '')

                db.session.commit()
                if is_new: success_count += 1
                else: updated_count += 1
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
