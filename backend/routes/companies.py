from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, Company
import pandas as pd

companies_bp = Blueprint('companies', __name__)


@companies_bp.route('', methods=['GET'])
@jwt_required()
def get_companies():
    try:
        companies = Company.query.order_by(Company.created_at.desc()).all()
        return jsonify([c.to_dict() for c in companies]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@companies_bp.route('', methods=['POST'])
@jwt_required()
def create_company():
    try:
        data = request.get_json()
        if not data or not data.get('company_name'):
            return jsonify({'error': 'Company name is required'}), 400

        company = Company(
            company_name=data['company_name'],
            role=data.get('role', ''),
            contact_person=data.get('contact_person', ''),
            contact=data.get('contact', '')
        )
        db.session.add(company)
        db.session.commit()
        return jsonify(company.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@companies_bp.route('/<int:company_id>', methods=['PUT'])
@jwt_required()
def update_company(company_id):
    try:
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'error': 'Company not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        for field in ['company_name', 'role', 'contact_person', 'contact']:
            if field in data:
                setattr(company, field, data[field])

        db.session.commit()
        return jsonify(company.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@companies_bp.route('/<int:company_id>', methods=['DELETE'])
@jwt_required()
def delete_company(company_id):
    try:
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        db.session.delete(company)
        db.session.commit()
        return jsonify({'message': 'Company deleted'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@companies_bp.route('/import', methods=['POST'])
@jwt_required()
def import_companies():
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

        col_name = get_col(['Company Name', 'Company', 'Organization'])
        col_role = get_col(['Role', 'Role Offered', 'Job Role'])
        col_person = get_col(['Contact Person', 'HR Name', 'Contact'])
        col_contact = get_col(['Contact', 'Phone', 'Mobile', 'Contact Phone'])

        if not col_name:
            return jsonify({'error': 'Required column (Company Name) not found in the Excel file.'}), 400

        success_count = 0
        updated_count = 0
        row_errors = []

        for index, row in df.iterrows():
            try:
                name = str(row.get(col_name, '')).strip()
                if not name or name.lower() == 'nan':
                    continue

                company = Company.query.filter_by(company_name=name).first()
                is_new = False
                if not company:
                    company = Company(company_name=name)
                    db.session.add(company)
                    is_new = True
                
                if col_role: company.role = str(row.get(col_role, '')).strip().replace('nan', '')
                if col_person: company.contact_person = str(row.get(col_person, '')).strip().replace('nan', '')
                if col_contact: company.contact = str(row.get(col_contact, '')).strip().replace('nan', '')

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
