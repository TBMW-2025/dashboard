"""
Seed the database with sample data.
Run: python seed.py (from the backend/ directory)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, Setting, Student, Company, Placement, Internship


def seed():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        # ── Admin User ──────────────────────────────────────────────
        admin = User(username='admin', email='admin@rru.ac.in', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        # ── Settings ───────────────────────────────────────────────
        default_setting = Setting(two_factor_enabled=False)
        db.session.add(default_setting)

        # ── Companies ──────────────────────────────────────────────
        companies = [
            Company(company_name='TechNova Solutions', role='Software Engineer Intern', contact_person='Alice Smith', contact='9876543210'),
            Company(company_name='Global Innovate', role='Data Analyst Intern', contact_person='Bob Jones', contact='8765432109')
        ]
        db.session.add_all(companies)
        db.session.commit() # Commit companies to get IDs

        # ── Students natively using enrollment_number safely ───────────────────────────────────────────────
        students = [
            Student(student_name='Aarav Mehta', enrollment_number='2023CS001', student_email_id='aarav@rru.ac.in', mobile_number='9876543211', department_course='B.Tech CSE', higher_education_plan='No', placement_status='Not Placed'),
            Student(student_name='Priya Sharma', enrollment_number='2023CS002', student_email_id='priya@rru.ac.in', mobile_number='9876543212', department_course='B.Tech IT', higher_education_plan='Yes', placement_status='Placed')
        ]
        db.session.add_all(students)
        db.session.commit() # Commit students to get IDs

        # ── Placements explicitly linking via string keys cleanly ─────────────────────────────────────────────
        placements = [
            Placement(
                enrollment_number=students[1].enrollment_number,
                student_name=students[1].student_name,
                company='Global Innovate', # Changed to match new company data
                role='Data Analyst Intern', # Changed to match new company data
                placement_date='15-03-2026', # Updated date
                salary_lpa=12.5, # Updated salary
                status='Placed'
            )
        ]
        db.session.add_all(placements)

        # ── Internships seamlessly bridged natively ────────────────────────────────────────────
        internships = [
            Internship(
                enrollment_number=students[0].enrollment_number,
                company_id=companies[0].company_id, # Use company ID from committed companies
                role='SWE Intern',
                duration='3 months',
                start_date='01-06-2025',
                status='Completed',
                stipend=15000
            )
        ]
        db.session.add_all(internships)

        db.session.commit()
        print("\n✅  Database seeded successfully!")
        print("    Admin credentials: admin / admin123")
        print(f"    {len(students_data)} students, {len(companies_data)} companies added.\n")


if __name__ == '__main__':
    seed()
