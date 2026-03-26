from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from models import db, Student, Company, Placement, Internship
from sqlalchemy import func, case

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    try:
        total_students = Student.query.count()
        placed_students = Student.query.filter_by(placement_status='Yes').count()
        total_companies = Company.query.count()
        total_internships = Internship.query.count()
        pending_placements = Placement.query.filter_by(status='Pending').count()

        return jsonify({
            'total_students': total_students,
            'placed_students': placed_students,
            'total_companies': total_companies,
            'total_internships': total_internships,
            'pending_placements': pending_placements,
            'placement_rate': round((placed_students / total_students * 100), 1) if total_students > 0 else 0
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/department', methods=['GET'])
@jwt_required()
def get_department_stats():
    """Department-wise placement breakdown."""
    try:
        results = db.session.query(
            Student.department_course,
            func.count(Student.enrollment_number).label('total'),
            func.sum(case((Student.placement_status == 'Yes', 1), else_=0)).label('placed')
        ).group_by(Student.department_course).all()

        data = []
        for row in results:
            dept = row.department_course or 'Unknown'
            total = row.total or 0
            placed = int(row.placed or 0)
            data.append({
                'department': dept,
                'total': total,
                'placed': placed,
                'percentage': round((placed / total * 100), 1) if total > 0 else 0
            })

        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/students-yearly', methods=['GET'])
@jwt_required()
def get_students_yearly():
    """Students added per year, broken down by placement status."""
    try:
        students = Student.query.all()
        yearly = {}  # year -> {total, placed}
        for s in students:
            if s.created_at:
                year = str(s.created_at.year)
            else:
                year = 'Unknown'
            if year not in yearly:
                yearly[year] = {'total': 0, 'placed': 0}
            yearly[year]['total'] += 1
            if s.placement_status == 'Yes':
                yearly[year]['placed'] += 1

        sorted_years = sorted(k for k in yearly if k != 'Unknown')
        if 'Unknown' in yearly:
            sorted_years.append('Unknown')

        return jsonify({
            'labels': sorted_years,
            'total': [yearly[y]['total'] for y in sorted_years],
            'placed': [yearly[y]['placed'] for y in sorted_years]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/yearly', methods=['GET'])
@jwt_required()
def get_yearly_trend():
    """Yearly placement count starting from 2023."""
    try:
        from datetime import datetime
        current_year = datetime.utcnow().year
        start_year = 2023
        
        # Initialize dictionary with zeros for all years in range
        years_range = [str(y) for y in range(start_year, current_year + 1)]
        yearly = {year: 0 for year in years_range}
        
        placements = Placement.query.filter_by(status='Placed').all()
        for p in placements:
            if p.placement_date:
                try:
                    # Expecting YYYY-MM-DD
                    year = p.placement_date.split('-')[0]
                    if year in yearly:
                        yearly[year] += 1
                except Exception:
                    pass
        
        # Ensure labels are sorted
        sorted_years = sorted(yearly.keys())
        return jsonify({
            'labels': sorted_years,
            'data': [yearly[y] for y in sorted_years]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/salary', methods=['GET'])
@jwt_required()
def get_salary_distribution():
    """Salary distribution across placements."""
    try:
        ranges = [
            ('7-9 LPA', 7, 9),
            ('9-11 LPA', 9, 11),
            ('11-13 LPA', 11, 13),
            ('13-15 LPA', 13, 15),
            ('15-20 LPA', 15, 20),
            ('20+ LPA', 20, 9999)
        ]
        placements = Placement.query.filter(
            Placement.salary_lpa.isnot(None),
            Placement.status == 'Placed'
        ).all()
        data = []
        for label, low, high in ranges:
            count = sum(1 for p in placements if low <= (p.salary_lpa or 0) < high)
            data.append({'range': label, 'count': count})
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
