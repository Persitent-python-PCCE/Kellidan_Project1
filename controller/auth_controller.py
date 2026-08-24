from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, make_response
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies, get_jwt_identity
from dao.user_dao import UserDAO
from service.user_service import UserService
from service.audit_service import AuditService

auth_bp = Blueprint('auth', __name__)
user_service = UserService(UserDAO())
audit_service = AuditService()

@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    try:
        user = user_service.register_user(data.get('username'), data.get('password'), data.get('role', 'STUDENT').upper())
        audit_service.log("USER_REGISTER_API", user_id=user.id, details=f"User {user.username} registered with role {user.role}")
        return jsonify({"message": "Registered successfully", "user": user.to_dict()}), 201
    except ValueError as e:
        audit_service.log("USER_REGISTER_FAILED", details=f"Failed registration attempt for username: {data.get('username')}")
        return jsonify({"message": str(e)}), 400

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    user = user_service.authenticate_user(data.get('username'), data.get('password'))
    if not user:
        audit_service.log("USER_LOGIN_FAILED_API", details=f"Failed login attempt for username: {data.get('username')}")
        return jsonify({"message": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role, "username": user.username})
    audit_service.log("USER_LOGIN_SUCCESS_API", user_id=user.id, details=f"User {user.username} logged in via API")
    return jsonify({"access_token": token, "user": user.to_dict()}), 200

@auth_bp.route('/login', methods=['GET', 'POST'])
def web_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = user_service.authenticate_user(username, password)
        if not user:
            audit_service.log("USER_LOGIN_FAILED", details=f"Failed web login for username: {username}")
            flash("Invalid credentials", "danger")
            return render_template('login.html')

        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role, "username": user.username})
        audit_service.log("USER_LOGIN_SUCCESS", user_id=user.id, details=f"User {user.username} logged in via web")
        
        if user.role == "ADMIN":
            target_route = "admin.admin_dashboard"
        elif user.role == "INSTRUCTOR":
            target_route = "admin.instructor_dashboard"
        else:
            target_route = "admin.student_dashboard"
        
        response = make_response(redirect(url_for(target_route)))
        set_access_cookies(response, token)
        flash("Logged in successfully", "success")
        return response
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def web_register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'STUDENT').upper()
        try:
            user = user_service.register_user(username, password, role)
            audit_service.log("USER_REGISTER", user_id=user.id, details=f"Registered user {username} ({role})")
            flash("Registration successful. Please login.", "success")
            return redirect(url_for('auth.web_login'))
        except ValueError as e:
            audit_service.log("USER_REGISTER_FAILED", details=f"Registration error for {username}: {str(e)}")
            flash(str(e), "danger")
    return render_template('register.html')

@auth_bp.route('/logout')
def web_logout():
    try:
        user_id = get_jwt_identity()
        if user_id:
            audit_service.log("USER_LOGOUT", user_id=int(user_id), details="User logged out")
    except Exception:
        pass
    response = make_response(redirect(url_for('auth.web_login')))
    unset_jwt_cookies(response)
    flash("Logged out successfully", "info")
    return response