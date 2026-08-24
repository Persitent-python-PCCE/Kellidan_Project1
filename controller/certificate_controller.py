from flask import Blueprint, render_template, flash, redirect, url_for
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from dao.certificate_dao import CertificateDAO
from utils.decorators import role_required

certificate_bp = Blueprint('certificate', __name__)
certificate_dao = CertificateDAO()

@certificate_bp.route('/certificates/verify/<cert_code>', methods=['GET'])
def verify_certificate(cert_code):
    cert = certificate_dao.get_by_code(cert_code)
    current_user = None
    try:
        current_user = get_jwt()
    except Exception:
        pass
    return render_template('certificate_verify.html', cert=cert, cert_code=cert_code, current_user=current_user)

@certificate_bp.route('/certificates/view/<int:cert_id>', methods=['GET'])
@role_required("STUDENT", "INSTRUCTOR", "ADMIN")
def view_certificate(cert_id):
    cert = certificate_dao.get_by_id(cert_id)
    if not cert:
        flash("Certificate not found", "danger")
        return redirect(url_for('course.web_list_courses'))
    
    user_id = get_jwt_identity()
    role = get_jwt().get("role")
    if role != "ADMIN" and str(cert.user_id) != str(user_id):
        flash("You are not authorized to view this certificate", "danger")
        return redirect(url_for('course.web_list_courses'))

    return render_template('certificate.html', cert=cert, current_user=get_jwt())

@certificate_bp.route('/my-certificates', methods=['GET'])
@role_required("STUDENT", "INSTRUCTOR", "ADMIN")
def list_my_certificates():
    user_id = get_jwt_identity()
    certificates = certificate_dao.get_user_certificates(int(user_id))
    return render_template('my_certificates.html', certificates=certificates, current_user=get_jwt())
