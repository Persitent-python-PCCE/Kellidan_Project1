from config.database import db
from models.course import Course, Module, Lesson, Material, Enrollment
from models.progress import LessonProgress
from datetime import datetime, timezone

class CourseDAO:
    def create_course(self, title, description, instructor_id, prerequisite_ids=None):
        course = Course(title=title, description=description, instructor_id=instructor_id)
        if prerequisite_ids:
            prereqs = Course.query.filter(Course.id.in_(prerequisite_ids)).all()
            course.prerequisites = prereqs
        db.session.add(course)
        db.session.commit()
        return course

    def get_all_courses(self):
        return Course.query.all()

    def get_course_by_id(self, course_id):
        return db.session.get(Course, course_id)

    def get_courses_by_instructor(self, instructor_id):
        return Course.query.filter_by(instructor_id=instructor_id).all()

    def get_enrolled_courses(self, user_id):
        enrollments = Enrollment.query.filter_by(user_id=user_id).all()
        return [e.course for e in enrollments if e.course]

    def enroll_student(self, user_id, course_id):
        enrollment = Enrollment(user_id=user_id, course_id=course_id, progress=0.0)
        db.session.add(enrollment)
        db.session.commit()
        return enrollment

    def get_enrollment(self, user_id, course_id):
        return Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()

    def add_module(self, course_id, title):
        module = Module(course_id=course_id, title=title)
        db.session.add(module)
        db.session.commit()
        return module

    def add_lesson(self, module_id, title, content=""):
        lesson = Lesson(module_id=module_id, title=title, content=content)
        db.session.add(lesson)
        db.session.commit()
        return lesson

    def get_lesson_by_id(self, lesson_id):
        return db.session.get(Lesson, lesson_id)

    def add_material(self, module_id, filename, filepath, file_type):
        material = Material(module_id=module_id, filename=filename, filepath=filepath, file_type=file_type)
        db.session.add(material)
        db.session.commit()
        return material

    def get_material_by_id(self, material_id):
        return db.session.get(Material, material_id)

    def mark_lesson_progress(self, user_id, lesson_id, completed=True):
        progress_rec = LessonProgress.query.filter_by(user_id=user_id, lesson_id=lesson_id).first()
        if not progress_rec:
            progress_rec = LessonProgress(user_id=user_id, lesson_id=lesson_id, completed=completed)
            db.session.add(progress_rec)
        else:
            progress_rec.completed = completed
            progress_rec.completed_at = datetime.now(timezone.utc)
        db.session.commit()
        return progress_rec

    def get_completed_lesson_ids(self, user_id, course_id):
        course = self.get_course_by_id(course_id)
        if not course:
            return set()
        all_lesson_ids = [lesson.id for module in course.modules for lesson in module.lessons]
        if not all_lesson_ids:
            return set()
        completed_records = LessonProgress.query.filter(
            LessonProgress.user_id == user_id,
            LessonProgress.lesson_id.in_(all_lesson_ids),
            LessonProgress.completed.is_(True)
        ).all()
        return {r.lesson_id for r in completed_records}

    def calculate_course_progress(self, user_id, course_id):
        course = self.get_course_by_id(course_id)
        if not course:
            return 0.0
        all_lessons = [lesson for module in course.modules for lesson in module.lessons]
        quizzes = course.quizzes or []

        total_items = len(all_lessons) + len(quizzes)
        if total_items == 0:
            progress = 100.0
        else:
            completed_ids = self.get_completed_lesson_ids(user_id, course_id)
            completed_lesson_count = len(completed_ids)

            quiz_score_sum = 0.0
            if quizzes:
                from dao.quiz_dao import QuizDAO
                quiz_dao = QuizDAO()
                for quiz in quizzes:
                    highest_score = quiz_dao.get_highest_score_for_quiz(user_id, quiz.id)
                    quiz_score_sum += (highest_score / 100.0)

            total_completed = completed_lesson_count + quiz_score_sum
            progress = round(min(100.0, (total_completed / total_items) * 100.0), 1)

        enrollment = self.get_enrollment(user_id, course_id)
        if enrollment:
            enrollment.progress = progress
            db.session.commit()
        return progress

    def are_prerequisites_completed(self, user_id, course_id):
        course = self.get_course_by_id(course_id)
        if not course or not course.prerequisites:
            return True, []
        unmet_prereqs = []
        for prereq in course.prerequisites:
            enrollment = self.get_enrollment(user_id, prereq.id)
            if not enrollment or enrollment.progress < 100.0:
                unmet_prereqs.append(prereq)
        return len(unmet_prereqs) == 0, unmet_prereqs

    def delete_course(self, course_id):
        course = self.get_course_by_id(course_id)
        if not course:
            return False
        course.prerequisites.clear()
        db.session.delete(course)
        db.session.commit()
        return True

    def delete_module(self, module_id):
        module = db.session.get(Module, module_id)
        if not module:
            return False
        db.session.delete(module)
        db.session.commit()
        return True