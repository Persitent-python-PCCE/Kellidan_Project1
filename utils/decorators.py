from functools import wraps
from flask import request, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt

def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") not in roles:
                if request.is_json or request.path.startswith("/api"):
                    return jsonify({"message": "Forbidden: Permission denied"}), 403
                return render_template("403.html", error="Forbidden: You do not have permission to access this resource."), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator