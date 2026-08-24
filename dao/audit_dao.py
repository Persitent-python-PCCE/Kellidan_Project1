from config.database import db
from models.audit_log import AuditLog

class AuditDAO:
    def log_event(self, action, user_id=None, ip_address=None, details=None):
        log = AuditLog(
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            details=details
        )
        db.session.add(log)
        db.session.commit()
        return log

    def get_recent_logs(self, limit=100):
        return AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
