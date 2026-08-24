import uuid
from config.database import db
from models.certificate import Certificate

class CertificateDAO:
    def create_certificate(self, user_id, course_id):
        existing = Certificate.query.filter_by(user_id=user_id, course_id=course_id).first()
        if existing:
            return existing

        code = f"CERT-{uuid.uuid4().hex[:8].upper()}-{uuid.uuid4().hex[:4].upper()}"
        cert = Certificate(user_id=user_id, course_id=course_id, certificate_code=code)
        db.session.add(cert)
        db.session.commit()
        return cert

    def get_by_code(self, certificate_code):
        return Certificate.query.filter_by(certificate_code=certificate_code.strip().upper()).first()

    def get_by_id(self, cert_id):
        return db.session.get(Certificate, cert_id)

    def get_by_user_and_course(self, user_id, course_id):
        return Certificate.query.filter_by(user_id=user_id, course_id=course_id).first()

    def get_user_certificates(self, user_id):
        return Certificate.query.filter_by(user_id=user_id).order_by(Certificate.issued_at.desc()).all()
