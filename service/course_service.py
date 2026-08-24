from dao.course_dao import CourseDAO
from dao.certificate_dao import CertificateDAO
from service.audit_service import AuditService

class CourseService:
    def __init__(self, course_dao=None, certificate_dao=None, audit_service=None):
        self.course_dao = course_dao or CourseDAO()
        self.certificate_dao = certificate_dao or CertificateDAO()
        self.audit_service = audit_service or AuditService()

    def create_course(self, title, description, instructor_id, prerequisite_ids=None):
        course = self.course_dao.create_course(title, description, instructor_id, prerequisite_ids)
        self.audit_service.log(
            action="CREATE_COURSE",
            user_id=instructor_id,
            details=f"Course '{title}' (ID: {course.id}) created"
        )
        return course

    def enroll_user(self, user_id, course_id):
        if self.course_dao.get_enrollment(user_id, course_id):
            raise ValueError("Already enrolled in this course")

        # Validate prerequisites
        met, unmet = self.course_dao.are_prerequisites_completed(user_id, course_id)
        if not met:
            unmet_names = ", ".join([c.title for c in unmet])
            raise ValueError(f"Prerequisites not met. Please complete: {unmet_names}")

        enrollment = self.course_dao.enroll_student(user_id, course_id)
        self.audit_service.log(
            action="ENROLL_COURSE",
            user_id=user_id,
            details=f"Enrolled in course ID {course_id}"
        )
        return enrollment

    def toggle_lesson_completion(self, user_id, course_id, lesson_id, completed=None):
        enrollment = self.course_dao.get_enrollment(user_id, course_id)
        if not enrollment:
            raise ValueError("You must be enrolled in this course to mark lesson progress.")

        # Determine current status if completed is None
        completed_ids = self.course_dao.get_completed_lesson_ids(user_id, course_id)
        if completed is None:
            new_status = (lesson_id not in completed_ids)
        else:
            new_status = bool(completed)

        self.course_dao.mark_lesson_progress(user_id, lesson_id, new_status)
        new_progress = self.course_dao.calculate_course_progress(user_id, course_id)

        self.audit_service.log(
            action="LESSON_PROGRESS_UPDATE",
            user_id=user_id,
            details=f"Lesson {lesson_id} marked as {'completed' if new_status else 'incomplete'} in course {course_id}. Overall: {new_progress}%"
        )

        cert = None
        if new_progress >= 100.0:
            cert = self.certificate_dao.create_certificate(user_id, course_id)
            self.audit_service.log(
                action="CERTIFICATE_ISSUED",
                user_id=user_id,
                details=f"Certificate {cert.certificate_code} issued for completing course {course_id}"
            )

        return new_status, new_progress, cert

    def delete_course(self, user_id, role, course_id):
        course = self.course_dao.get_course_by_id(course_id)
        if not course:
            raise ValueError("Course not found")
        if role != "ADMIN" and course.instructor_id != user_id:
            raise ValueError("You do not have permission to delete this course.")

        title = course.title
        self.course_dao.delete_course(course_id)
        self.audit_service.log(
            action="DELETE_COURSE",
            user_id=user_id,
            details=f"Course '{title}' (ID: {course_id}) deleted"
        )
        return True

    def delete_module(self, user_id, role, course_id, module_id):
        from models.course import Module, Enrollment
        from config.database import db
        course = self.course_dao.get_course_by_id(course_id)
        if not course:
            raise ValueError("Course not found")
        if role != "ADMIN" and course.instructor_id != user_id:
            raise ValueError("You do not have permission to delete modules in this course.")

        module = db.session.get(Module, module_id)
        if not module or module.course_id != course_id:
            raise ValueError("Module not found in this course")

        mod_title = module.title
        self.course_dao.delete_module(module_id)

        # Recalculate progress for enrolled students
        enrollments = Enrollment.query.filter_by(course_id=course_id).all()
        for e in enrollments:
            self.course_dao.calculate_course_progress(e.user_id, course_id)

        self.audit_service.log(
            action="DELETE_MODULE",
            user_id=user_id,
            details=f"Module '{mod_title}' (ID: {module_id}) deleted from course ID {course_id}"
        )
        return True