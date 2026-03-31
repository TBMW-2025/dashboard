from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, Placement, Student
import pandas as pd
from sqlalchemy import or_
from datetime import datetime

placements_bp = Blueprint('placements', __name__)


@placements_bp.route('', methods=['GET'])
@jwt_required()
def get_placements():
    try:
        prog = request.args.get('programme')
        query = Placement.query.order_by(Placement.created_at.desc())
        
        if prog:
            if prog == 'BCPA':
                query = query.join(Student, Placement.enrollment_number == Student.enrollment_number).filter(
                    or_(
                        Student.programme.like("%BCPA%"),
                        Student.programme.like("%BCPS%"),
                        Student.programme.like("%BACPA%")
                    )
                )
            else:
                query = query.join(Student, Placement.enrollment_number == Student.enrollment_number).filter(Student.programme.like(f"%{prog}%"))
            
        placements = query.all()
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

        def get_col(candidates):
            for cand in candidates:
                match = next((c for c in df.columns if str(c).strip().lower() == cand.strip().lower()), None)
                if match: return match
            return None

        col_enroll = get_col(['Enrolment No.', 'Enrolment No', 'Enrollment Number', 'Enrollment', 'Student Enrollment'])
        col_name = get_col(['Student Name', 'Name'])
        col_company = get_col(['Company Name', 'Company', 'Organization'])
        col_role = get_col(['Role', 'Role Offered'])
        col_date = get_col(['Date', 'Placement Date', 'Date of Placement'])
        col_salary = get_col(['Salary (LPA)', 'Salary', 'LPA', 'Package'])
        col_status = get_col(['Status', 'Placement Status'])

        if not col_enroll and not col_name:
            return jsonify({'error': 'Required column (Enrolment No. or Student Name) not found in the Excel file.'}), 400

        success_count = 0
        updated_count = 0
        row_errors = []

        for index, row in df.iterrows():
            try:
                # Robust enrollment parsing
                enroll_val = row.get(col_enroll)
                if pd.isnull(enroll_val): enroll = ''
                elif isinstance(enroll_val, (float, int)): enroll = str(int(enroll_val))
                else: enroll = str(enroll_val).strip()

                if not enroll or enroll.lower() == 'nan':
                    # Try matching by name if enrollment is missing
                    name_val = row.get(col_name)
                    name = str(name_val).strip() if pd.notnull(name_val) else ''
                    if name and name.lower() != 'nan':
                        student_match = Student.query.filter_by(student_name=name).first()
                        if student_match:
                            enroll = student_match.enrollment_number
                
                if not enroll or enroll.lower() == 'nan':
                    continue

                student = Student.query.get(enroll)
                if not student:
                    row_errors.append(f"Row {index + 2}: Student {enroll} not found in database.")
                    continue

                company_name = str(row.get(col_company, '')).strip().replace('nan', '') if col_company else ''
                if not company_name:
                    continue

                existing = Placement.query.get(enroll)
                is_new = False
                if existing:
                    existing.company = company_name
                    if col_role: existing.role = str(row.get(col_role, '')).strip().replace('nan', '')
                    if col_date: 
                        p_date = str(row.get(col_date, '')).strip().replace('nan', '')
                        if p_date: existing.placement_date = p_date
                    
                    if col_salary:
                        try:
                            s_val = str(row.get(col_salary, '0')).strip().lower().replace('nan', '0').split(' ')[0]
                            existing.salary_lpa = float(s_val)
                        except: pass
                    
                    existing.status = str(row.get(col_status, 'Placed')).strip().replace('nan', 'Placed') if col_status else existing.status
                else:
                    is_new = True
                    new_placement = Placement(
                        enrollment_number=enroll,
                        student_name=student.student_name,
                        company=company_name,
                        role=str(row.get(col_role, '')).strip().replace('nan', '') if col_role else '',
                        status=str(row.get(col_status, 'Placed')).strip().replace('nan', 'Placed') if col_status else 'Placed'
                    )
                    
                    if col_date:
                        p_date = str(row.get(col_date, '')).strip().replace('nan', '')
                        if p_date: new_placement.placement_date = p_date
                    
                    if not new_placement.placement_date:
                        new_placement.placement_date = datetime.now().strftime('%Y-%m-%d')

                    if col_salary:
                        try:
                            s_val = str(row.get(col_salary, '0')).strip().lower().replace('nan', '0').split(' ')[0]
                            new_placement.salary_lpa = float(s_val)
                        except: pass
                    
                    db.session.add(new_placement)
                
                # Sync back to student status
                student.placement_status = 'Yes' # Since they are in the placement table
                
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
