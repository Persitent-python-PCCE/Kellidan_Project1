from flask import Blueprint, render_template
from flask_jwt_extended import get_jwt, get_jwt_identity
from dao.user_dao import UserDAO
from dao.course_dao import CourseDAO
from dao.audit_dao import AuditDAO
from utils.decorators import role_required

admin_bp = Blueprint('admin', __name__)
audit_dao = AuditDAO()

@admin_bp.route('/dashboard/admin', methods=['GET'])
@role_required("ADMIN")
def admin_dashboard():
    users = UserDAO().get_all()
    courses = CourseDAO().get_all_courses()
    recent_logs = audit_dao.get_recent_logs(limit=10)
    return render_template('admin_dashboard.html', users=users, courses=courses, recent_logs=recent_logs, current_user=get_jwt())

@admin_bp.route('/dashboard/admin/audit-logs', methods=['GET'])
@role_required("ADMIN")
def admin_audit_logs():
    logs = audit_dao.get_recent_logs(limit=150)
    return render_template('admin_audit_logs.html', logs=logs, current_user=get_jwt())

@admin_bp.route('/dashboard/instructor', methods=['GET'])
@role_required("INSTRUCTOR", "ADMIN")
def instructor_dashboard():
    user_id = get_jwt_identity()
    role = get_jwt().get("role")
    if role == "ADMIN":
        courses = CourseDAO().get_all_courses()
    else:
        courses = CourseDAO().get_courses_by_instructor(int(user_id))
    return render_template('instructor_dashboard.html', courses=courses, current_user=get_jwt())

@admin_bp.route('/dashboard/student', methods=['GET'])
@role_required("STUDENT", "ADMIN")
def student_dashboard():
    user_id = get_jwt_identity()
    enrolled_courses = CourseDAO().get_enrolled_courses(int(user_id))
    all_courses = CourseDAO().get_all_courses()
    return render_template('student_dashboard.html', enrolled_courses=enrolled_courses, all_courses=all_courses, current_user=get_jwt())

@admin_bp.route('/dashboard/admin/users/<int:user_id>/delete', methods=['POST'])
@role_required("ADMIN")
def delete_user(user_id):
    from flask import redirect, url_for, flash
    current_admin_id = get_jwt_identity()
    if int(current_admin_id) == user_id:
        flash("You cannot delete your own admin account!", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    user_dao = UserDAO()
    user_to_delete = user_dao.get_by_id(user_id)
    if not user_to_delete:
        flash("User not found", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    username = user_to_delete.username
    user_dao.delete(user_to_delete)
    from service.audit_service import AuditService
    AuditService().log(action="DELETE_USER", user_id=int(current_admin_id), details=f"User '{username}' (ID: {user_id}) deleted by admin")
    flash(f"User '{username}' deleted successfully!", "info")
    return redirect(url_for('admin.admin_dashboard'))