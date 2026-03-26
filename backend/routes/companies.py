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

        success_count = 0
        duplicate_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                name = str(row.get(next((c for c in df.columns if c.strip().lower() == 'company name'), None), '')).strip()
                if not name or name == 'nan':
                    continue

                if Company.query.filter_by(company_name=name).first():
                    duplicate_count += 1
                    continue

                company = Company(
                    company_name=name,
                    role=str(row.get(next((c for c in df.columns if c.strip().lower() == 'role'), ''), '')).strip().replace('nan', ''),
                    contact_person=str(row.get(next((c for c in df.columns if c.strip().lower() == 'contact person'), ''), '')).strip().replace('nan', ''),
                    contact=str(row.get(next((c for c in df.columns if c.strip().lower() == 'contact'), ''), '')).strip().replace('nan', '')
                )
                db.session.add(company)
                success_count += 1
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
