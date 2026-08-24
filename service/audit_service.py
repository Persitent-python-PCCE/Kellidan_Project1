from flask import request, has_request_context
from dao.audit_dao import AuditDAO

class AuditService:
    def __init__(self, audit_dao=None):
        self.audit_dao = audit_dao or AuditDAO()

    def log(self, action, user_id=None, details=None):
        ip_address = None
        if has_request_context():
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ip_address and ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()
        return self.audit_dao.log_event(
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            details=details
        )
