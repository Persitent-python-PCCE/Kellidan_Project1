import os
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, send_from_directory, current_app
from flask_jwt_extended import get_jwt, get_jwt_identity
from dao.course_dao import CourseDAO
from dao.review_dao import ReviewDAO
from dao.certificate_dao import CertificateDAO
from service.course_service import CourseService
from service.audit_service import AuditService
from utils.decorators import role_required
from utils.file_handler import save_file

course_bp = Blueprint('course', __name__)
course_dao = CourseDAO()
review_dao = ReviewDAO()
certificate_dao = CertificateDAO()
audit_service = AuditService()
course_service = CourseService(course_dao, certificate_dao, audit_service)

@course_bp.route('/courses', methods=['GET'])
@role_required("ADMIN", "INSTRUCTOR", "STUDENT")
def web_list_courses():
    courses = course_dao.get_all_courses()
    return render_template('course_list.html', courses=courses, current_user=get_jwt())

@course_bp.route('/courses/create', methods=['GET', 'POST'])
@role_required("INSTRUCTOR", "ADMIN")
def web_create_course():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        prereq_ids = request.form.getlist('prerequisites', type=int)
        user_id = get_jwt_identity()
        if not title:
            flash("Course title is required", "danger")
            all_courses = course_dao.get_all_courses()
            return render_template('create_course.html', all_courses=all_courses, current_user=get_jwt())
        try:
            course = course_service.create_course(title, description, int(user_id), prerequisite_ids=prereq_ids)
            flash("Course created successfully!", "success")
            return redirect(url_for('course.web_course_details', course_id=course.id))
        except Exception as e:
            flash(str(e), "danger")
    all_courses = course_dao.get_all_courses()
    return render_template('create_course.html', all_courses=all_courses, current_user=get_jwt())

@course_bp.route('/courses/<int:course_id>', methods=['GET'])
@role_required("ADMIN", "INSTRUCTOR", "STUDENT")
def web_course_details(course_id):
    course = course_dao.get_course_by_id(course_id)
    if not course:
        flash("Course not found", "danger")
        return redirect(url_for('course.web_list_courses'))
    
    user_id = get_jwt_identity()
    enrollment = course_dao.get_enrollment(int(user_id), course_id)
    prereqs_met, unmet_prereqs = course_dao.are_prerequisites_completed(int(user_id), course_id)
    completed_lesson_ids = course_dao.get_completed_lesson_ids(int(user_id), course_id)
    reviews = review_dao.get_reviews_for_course(course_id)
    user_review = review_dao.get_user_review(int(user_id), course_id)
    certificate = certificate_dao.get_by_user_and_course(int(user_id), course_id)
    from dao.quiz_dao import QuizDAO
    quiz_dao = QuizDAO()
    quiz_scores = {q.id: quiz_dao.get_highest_score_for_quiz(int(user_id), q.id) for q in course.quizzes} if course.quizzes else {}

    return render_template(
        'course_details.html',
        course=course,
        is_enrolled=bool(enrollment),
        enrollment=enrollment,
        prereqs_met=prereqs_met,
        unmet_prereqs=unmet_prereqs,
        completed_lesson_ids=completed_lesson_ids,
        reviews=reviews,
        user_review=user_review,
        certificate=certificate,
        quiz_scores=quiz_scores,
        current_user=get_jwt()
    )

@course_bp.route('/courses/<int:course_id>/modules', methods=['POST'])
@role_required("INSTRUCTOR", "ADMIN")
def web_add_module(course_id):
    title = request.form.get('title')
    if title:
        course_dao.add_module(course_id, title)
        flash("Module added successfully!", "success")
    else:
        flash("Module title is required", "danger")
    return redirect(url_for('course.web_course_details', course_id=course_id))

@course_bp.route('/courses/<int:course_id>/modules/<int:module_id>/lessons', methods=['POST'])
@role_required("INSTRUCTOR", "ADMIN")
def web_add_lesson(course_id, module_id):
    title = request.form.get('title')
    content = request.form.get('content', '')
    if title:
        course_dao.add_lesson(module_id, title, content)
        flash("Lesson added successfully!", "success")
    else:
        flash("Lesson title is required", "danger")
    return redirect(url_for('course.web_course_details', course_id=course_id))

@course_bp.route('/courses/<int:course_id>/lessons/<int:lesson_id>/toggle', methods=['POST'])
@role_required("STUDENT", "INSTRUCTOR", "ADMIN")
def web_toggle_lesson(course_id, lesson_id):
    user_id = get_jwt_identity()
    try:
        new_status, new_progress, cert = course_service.toggle_lesson_completion(int(user_id), course_id, lesson_id)
        if cert:
            flash(f"🎉 Congratulations! You completed the course with 100% progress. Your certificate #{cert.certificate_code} has been issued!", "success")
        else:
            status_text = "completed" if new_status else "incomplete"
            flash(f"Lesson marked as {status_text}. Course progress: {new_progress}%", "info")
    except ValueError as e:
        flash(str(e), "warning")
    return redirect(url_for('course.web_course_details', course_id=course_id))

@course_bp.route('/courses/enroll/<int:course_id>', methods=['POST'])
@role_required("STUDENT")
def web_enroll(course_id):
    user_id = get_jwt_identity()
    try:
        course_service.enroll_user(int(user_id), course_id)
        flash("Enrolled successfully!", "success")
    except ValueError as e:
        flash(str(e), "warning")
    return redirect(url_for('course.web_course_details', course_id=course_id))

@course_bp.route('/courses/<int:course_id>/reviews', methods=['POST'])
@role_required("STUDENT", "INSTRUCTOR", "ADMIN")
def web_submit_review(course_id):
    user_id = get_jwt_identity()
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()
    if not rating or rating < 1 or rating > 5:
        flash("Please select a valid rating between 1 and 5 stars.", "danger")
    else:
        review_dao.add_or_update_review(int(user_id), course_id, rating, comment)
        audit_service.log(
            action="COURSE_REVIEW_SUBMITTED",
            user_id=int(user_id),
            details=f"User submitted rating {rating}/5 for course {course_id}"
        )
        flash("Thank you for your review!", "success")
    return redirect(url_for('course.web_course_details', course_id=course_id))

@course_bp.route('/courses/<int:course_id>/modules/<int:module_id>/upload', methods=['POST'])
@role_required("INSTRUCTOR", "ADMIN")
def upload_material(course_id, module_id):
    file = request.files.get('file')
    try:
        sec_name, rel_path, file_type = save_file(file, course_id, module_id, current_app.config['UPLOAD_FOLDER'])
        course_dao.add_material(module_id, sec_name, rel_path, file_type)
        flash("File uploaded successfully", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for('course.web_course_details', course_id=course_id))

@course_bp.route('/materials/download/<int:material_id>', methods=['GET'])
@role_required("ADMIN", "INSTRUCTOR", "STUDENT")
def download_material(material_id):
    mat = course_dao.get_material_by_id(material_id)
    if not mat:
        flash("File not found", "danger")
        return redirect(url_for('course.web_list_courses'))
    
    dir_path = os.path.dirname(os.path.join(current_app.config['UPLOAD_FOLDER'], mat.filepath))
    filename = os.path.basename(mat.filepath)
    return send_from_directory(dir_path, filename, as_attachment=True)

@course_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@role_required("INSTRUCTOR", "ADMIN")
def web_delete_course(course_id):
    user_id = get_jwt_identity()
    role = get_jwt().get("role")
    try:
        course_service.delete_course(int(user_id), role, course_id)
        flash("Course deleted successfully!", "info")
    except ValueError as e:
        flash(str(e), "danger")
    if role == "ADMIN":
        return redirect(url_for('admin.admin_dashboard'))
    return redirect(url_for('admin.instructor_dashboard'))

@course_bp.route('/courses/<int:course_id>/modules/<int:module_id>/delete', methods=['POST'])
@role_required("INSTRUCTOR", "ADMIN")
def web_delete_module(course_id, module_id):
    user_id = get_jwt_identity()
    role = get_jwt().get("role")
    try:
        course_service.delete_module(int(user_id), role, course_id, module_id)
        flash("Module deleted successfully!", "info")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('course.web_course_details', course_id=course_id))