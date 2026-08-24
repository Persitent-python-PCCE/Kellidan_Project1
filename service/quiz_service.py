from dao.course_dao import CourseDAO
from dao.certificate_dao import CertificateDAO
from service.audit_service import AuditService

class QuizService:
    def __init__(self, quiz_dao, course_dao=None, certificate_dao=None, audit_service=None):
        self.quiz_dao = quiz_dao
        self.course_dao = course_dao or CourseDAO()
        self.certificate_dao = certificate_dao or CertificateDAO()
        self.audit_service = audit_service or AuditService()

    def evaluate_quiz(self, user_id, quiz_id, answers):
        quiz = self.quiz_dao.get_quiz_by_id(quiz_id)
        if not quiz or not quiz.questions:
            raise ValueError("Quiz contains no questions.")

        total = len(quiz.questions)
        correct = 0
        for q in quiz.questions:
            submitted = answers.get(str(q.id)) or answers.get(q.id)
            if submitted and str(submitted).upper() == q.correct_option.upper():
                correct += 1

        score = (correct / total) * 100
        result = self.quiz_dao.save_quiz_result(user_id, quiz_id, score)

        if quiz.course_id:
            new_progress = self.course_dao.calculate_course_progress(user_id, quiz.course_id)
            if new_progress >= 100.0:
                cert = self.certificate_dao.create_certificate(user_id, quiz.course_id)
                self.audit_service.log(
                    action="CERTIFICATE_ISSUED",
                    user_id=user_id,
                    details=f"Certificate {cert.certificate_code} issued for completing course {quiz.course_id}"
                )
            self.audit_service.log(
                action="QUIZ_SUBMITTED",
                user_id=user_id,
                details=f"Quiz {quiz_id} submitted with score {score:.2f}%. Course progress: {new_progress}%"
            )

        return score, result

    def delete_quiz(self, user_id, role, course_id, quiz_id):
        from models.course import Enrollment
        quiz = self.quiz_dao.get_quiz_by_id(quiz_id)
        if not quiz:
            raise ValueError("Quiz not found")

        course = self.course_dao.get_course_by_id(course_id)
        if not course:
            raise ValueError("Course not found")

        if role != "ADMIN" and course.instructor_id != user_id:
            raise ValueError("You do not have permission to delete quizzes in this course.")

        q_title = quiz.title
        self.quiz_dao.delete_quiz(quiz_id)

        # Recalculate progress for enrolled students
        enrollments = Enrollment.query.filter_by(course_id=course_id).all()
        for e in enrollments:
            self.course_dao.calculate_course_progress(e.user_id, course_id)

        if self.audit_service:
            self.audit_service.log(
                action="DELETE_QUIZ",
                user_id=user_id,
                details=f"Quiz '{q_title}' (ID: {quiz_id}) deleted from course ID {course_id}"
            )
        return True