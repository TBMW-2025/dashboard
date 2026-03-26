import io
import pandas as pd
from datetime import datetime
from flask import Blueprint, send_file, jsonify
from flask_jwt_extended import jwt_required

from models import Student, Company, Internship, Placement

export_bp = Blueprint('export_bp', __name__)

def generate_excel_response(df, prefix):
    # Create an in-memory output file for the new workbook.
    output = io.BytesIO()
    
    # Save the dataframe to the BytesIO object
    # using pandas to_excel method with the openpyxl engine
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        
    output.seek(0)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime('%Y-%m-%d')
    filename = f"{prefix}_{timestamp}.xlsx"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@export_bp.route('/students', methods=['GET'])
@jwt_required()
def export_students():
    try:
        students = Student.query.all()
        data = []
        for s in students:
            data.append({
                'Enrollment Number': s.enrollment_number,
                'Student Name': s.student_name,
                'Email ID': s.student_email_id,
                'Mobile Number': s.mobile_number,
                'Department': s.department_course,
                'Placement Status': s.placement_status
            })
        df = pd.DataFrame(data)
        return generate_excel_response(df, 'students')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/companies', methods=['GET'])
@jwt_required()
def export_companies():
    try:
        companies = Company.query.all()
        data = []
        for c in companies:
            data.append({
                'Company Name': c.company_name,
                'Role': c.role,
                'Contact Person': c.contact_person,
                'Contact': c.contact
            })
        df = pd.DataFrame(data)
        return generate_excel_response(df, 'companies')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/internships', methods=['GET'])
@jwt_required()
def export_internships():
    try:
        internships = Internship.query.all()
        data = []
        for i, intern in enumerate(internships):
            data.append({
                'Sr. No.': i + 1,
                'Year': intern.year,
                'Enrolment No.': intern.enrollment_number,
                'Programme': intern.programme,
                'Name of Student': intern.student.student_name if intern.student else '',
                'Gender': intern.gender,
                'Internship Place': intern.internship_place,
                'Internship Place 02': intern.internship_place_02,
                'Type of Organization': intern.organization_type
            })
        df = pd.DataFrame(data)
        return generate_excel_response(df, 'internships')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_bp.route('/placements', methods=['GET'])
@jwt_required()
def export_placements():
    try:
        placements = Placement.query.all()
        data = []
        for p in placements:
            data.append({
                'Student Name': p.student_name,
                'Company': p.company,
                'Role': p.role,
                'Salary': p.salary_lpa,
                'Placement Date': p.placement_date,
                'Status': p.status
            })
        df = pd.DataFrame(data)
        return generate_excel_response(df, 'placements')
    except Exception as e:
        return jsonify({'error': str(e)}), 500
