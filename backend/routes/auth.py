import random
import time
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User

auth_bp = Blueprint('auth', __name__)

# ─── OTP Delivery Helpers ──────────────────────────────────────────────────────

def send_otp_email(to_email, otp, purpose="Login MFA"):
    """Send OTP via Gmail SMTP. Falls back to console print if not configured."""
    smtp_email = os.environ.get('SMTP_EMAIL', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))

    if not smtp_email or smtp_email == 'your_gmail@gmail.com' or not smtp_password or smtp_password == 'your_app_password_here':
        print(f"   ⚠️  SMTP not configured — email NOT sent to {to_email}.")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🔐 Placement Monitor — Your OTP ({purpose})'
        msg['From']    = f'Placement Monitor <{smtp_email}>'
        msg['To']      = to_email

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;background:#0f2236;color:#fff;border-radius:12px;padding:32px;">
          <h2 style="color:#ff8c00;margin-top:0;">Placement Monitor Dashboard</h2>
          <p style="color:#aaa;">Your OTP for <strong>{purpose}</strong>:</p>
          <div style="font-size:36px;font-weight:bold;letter-spacing:10px;color:#ff8c00;text-align:center;padding:20px 0;">{otp}</div>
          <p style="color:#888;font-size:13px;">This OTP expires in <strong>5 minutes</strong>. Do not share it with anyone.</p>
        </div>"""
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, to_email, msg.as_string())

        print(f"   ✅ Email OTP sent to {to_email}")
        return True
    except Exception as e:
        print(f"   ❌ Failed to send email OTP to {to_email}: {e}")
        return False


def send_otp_sms(mobile, otp):
    """
    SMS stub — prints to console.
    To enable real SMS: integrate Twilio / MSG91 here.
    Example with Twilio:
        from twilio.rest import Client
        client = Client(os.environ['TWILIO_SID'], os.environ['TWILIO_TOKEN'])
        client.messages.create(body=f'Your OTP is: {otp}', from_='+1...', to=mobile)
    """
    print(f"   📱 [SMS STUB] OTP {otp} would be sent to {mobile} — SMS gateway not configured.")


# ─── Routes ───────────────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid username or password'}), 401

        # ── Always generate OTP — 2FA is mandatory ────────────────────────────
        from models import Otp
        email_otp  = str(random.randint(100000, 999999))
        mobile_otp = str(random.randint(100000, 999999))

        Otp.query.filter_by(user_id=user.id).delete()

        new_otp = Otp(
            user_id=user.id,
            email_otp=email_otp,
            mobile_otp=mobile_otp,
            expiry_time=time.time() + 300   # 5-minute expiry
        )
        db.session.add(new_otp)
        db.session.commit()

        print("\n" + "="*60)
        print(f"🔐 [MFA] OTPs generated for admin: {user.username}")
        print(f"   📧 Email OTP  : {email_otp}   (→ {user.email or 'N/A'})")
        print(f"   📱 Mobile OTP : {mobile_otp}  (→ {user.mobile or 'N/A'})")
        print("="*60 + "\n")

        # Send via email
        if user.email:
            send_otp_email(user.email, email_otp)

        # Send via SMS
        if user.mobile:
            send_otp_sms(user.mobile, mobile_otp)

        return jsonify({
            'requires_2fa': True,
            'message': 'OTPs sent to your registered email and mobile.',
            'user_id': user.id,
            'email_hint': mask_email(user.email),
            'mobile_hint': mask_mobile(user.mobile)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def mask_email(email):
    if not email or '@' not in email:
        return 'N/A'
    local, domain = email.split('@', 1)
    return local[:2] + '***@' + domain


def mask_mobile(mobile):
    if not mobile:
        return 'N/A'
    m = mobile.replace(' ', '')
    return m[:3] + '****' + m[-3:] if len(m) > 6 else '***'


@auth_bp.route('/demo-bypass', methods=['POST'])
def demo_bypass():
    """Allows bypassing MFA for demo purposes when SMTP is unconfigured."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID required for bypass'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        token = create_access_token(
            identity=str(user.id),
            additional_claims={'role': user.role, 'username': user.username}
        )
        
        return jsonify({
            'access_token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'mobile': user.mobile,
                'role': user.role
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    try:
        from models import Otp
        data = request.get_json()
        user_id   = data.get('user_id')
        email_otp  = data.get('email_otp')
        mobile_otp = data.get('mobile_otp')

        if not user_id or not email_otp or not mobile_otp:
            return jsonify({'error': 'Missing user_id or OTP combinations'}), 400

        otp_record = Otp.query.filter_by(user_id=int(user_id)).first()
        if not otp_record:
            return jsonify({'error': 'No OTP requested or OTP expired'}), 400

        if time.time() > otp_record.expiry_time:
            db.session.delete(otp_record)
            db.session.commit()
            return jsonify({'error': 'OTP expired. Please login again.'}), 400

        if otp_record.email_otp != str(email_otp).strip() or \
           otp_record.mobile_otp != str(mobile_otp).strip():
            return jsonify({'error': 'Invalid OTPs provided'}), 401

        db.session.delete(otp_record)
        user = User.query.get(int(user_id))
        db.session.commit()

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'role': user.role, 'username': user.username}
        )
        return jsonify({'token': access_token, 'user': user.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/profile', methods=['GET', 'PUT'])
@jwt_required()
def admin_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if request.method == 'GET':
            return jsonify({
                'username': user.username,
                'email': user.email,
                'mobile': user.mobile or '',
                'role': user.role
            }), 200

        # PUT — update email and mobile
        data = request.get_json() or {}
        if 'email' in data and data['email']:
            user.email = data['email'].strip()
        if 'mobile' in data:
            user.mobile = data['mobile'].strip()
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully', 'user': user.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json() or {}
        current = data.get('current_password', '')
        new_pw  = data.get('new_password', '')

        if not current or not new_pw:
            return jsonify({'error': 'Current and new password are required'}), 400

        if not user.check_password(current):
            return jsonify({'error': 'Current password is incorrect'}), 401

        if len(new_pw) < 8:
            return jsonify({'error': 'New password must be at least 8 characters'}), 400

        user.set_password(new_pw)
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/settings/2fa', methods=['GET', 'POST'])
@jwt_required()
def toggle_2fa():
    try:
        from models import db, Setting
        setting = Setting.query.first()
        if not setting:
            setting = Setting(two_factor_enabled=False)
            db.session.add(setting)
            db.session.commit()

        if request.method == 'POST':
            data = request.get_json()
            setting.two_factor_enabled = bool(data.get('enabled', False))
            db.session.commit()

        return jsonify({'two_factor_enabled': setting.two_factor_enabled}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        from models import Otp
        data = request.get_json()
        email = data.get('email', '').strip()

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'message': 'If the email exists, an OTP has been sent.'}), 200

        otp_code = str(random.randint(100000, 999999))
        Otp.query.filter_by(user_id=user.id).delete()

        new_otp = Otp(
            user_id=user.id,
            email_otp=otp_code,
            mobile_otp='N/A',
            expiry_time=time.time() + 300
        )
        db.session.add(new_otp)
        db.session.commit()

        print("\n" + "="*60)
        print(f"🔐 [PASSWORD RESET] OTP for {user.email}: {otp_code}")
        print("="*60 + "\n")

        send_otp_email(user.email, otp_code, purpose="Password Reset")

        return jsonify({'message': 'If the email exists, an OTP has been sent.'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        from models import Otp
        data = request.get_json()
        email      = data.get('email')
        otp_code   = data.get('otp')
        new_password = data.get('new_password')

        if not email or not otp_code or not new_password:
            return jsonify({'error': 'Email, OTP, and new password are required'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'Invalid request'}), 400

        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters'}), 400

        otp_record = Otp.query.filter_by(user_id=user.id).first()
        if not otp_record:
            return jsonify({'error': 'No OTP requested or expired'}), 400

        if time.time() > otp_record.expiry_time:
            db.session.delete(otp_record)
            db.session.commit()
            return jsonify({'error': 'OTP expired'}), 400

        if otp_record.email_otp != str(otp_code).strip():
            return jsonify({'error': 'Invalid OTP'}), 401

        user.set_password(new_password)
        db.session.delete(otp_record)
        db.session.commit()

        return jsonify({'message': 'Password reset successfully. You can now log in.'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
