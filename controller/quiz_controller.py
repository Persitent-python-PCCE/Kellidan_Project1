from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_jwt_extended import get_jwt, get_jwt_identity
from dao.quiz_dao import QuizDAO
from service.quiz_service import QuizService
from utils.decorators import role_required

quiz_bp = Blueprint('quiz', __name__)
quiz_dao = QuizDAO()
quiz_service = QuizService(quiz_dao)

@quiz_bp.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@role_required("STUDENT", "ADMIN", "INSTRUCTOR")
def attempt_quiz(quiz_id):
    user_id = get_jwt_identity()
    quiz = quiz_dao.get_quiz_by_id(quiz_id)
    if not quiz:
        flash("Quiz not found", "danger")
        return redirect(url_for('course.web_list_courses'))

    if request.method == 'POST':
        try:
            score, _ = quiz_service.evaluate_quiz(int(user_id), quiz_id, request.form)
            flash(f"Quiz completed! You scored {score:.2f}%", "info")
            return redirect(url_for('quiz.view_progress'))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template('quiz.html', quiz=quiz, current_user=get_jwt())

@quiz_bp.route('/courses/<int:course_id>/quizzes/create', methods=['GET', 'POST'])
@role_required("INSTRUCTOR", "ADMIN")
def create_quiz(course_id):
    if request.method == 'POST':
        title = request.form.get('title')
        if not title:
            flash("Quiz title is required", "danger")
            return render_template('create_quiz.html', course_id=course_id, current_user=get_jwt())
        quiz = quiz_dao.create_quiz(course_id, title)
        
        # Add question if provided in form
        q_text = request.form.get('question_text')
        opt_a = request.form.get('option_a')
        opt_b = request.form.get('option_b')
        opt_c = request.form.get('option_c')
        opt_d = request.form.get('option_d')
        correct = request.form.get('correct_option')
        if q_text and opt_a and opt_b and opt_c and opt_d and correct:
            quiz_dao.add_question(quiz.id, q_text, opt_a, opt_b, opt_c, opt_d, correct.upper())

        flash("Quiz created successfully!", "success")
        return redirect(url_for('course.web_course_details', course_id=course_id))

    return render_template('create_quiz.html', course_id=course_id, current_user=get_jwt())

@quiz_bp.route('/progress', methods=['GET'])
@role_required("STUDENT")
def view_progress():
    user_id = get_jwt_identity()
    results = quiz_dao.get_user_results(int(user_id))
    return render_template('progress.html', results=results, current_user=get_jwt())

@quiz_bp.route('/courses/<int:course_id>/quizzes/<int:quiz_id>/delete', methods=['POST'])
@role_required("INSTRUCTOR", "ADMIN")
def delete_quiz(course_id, quiz_id):
    user_id = get_jwt_identity()
    role = get_jwt().get("role")
    try:
        quiz_service.delete_quiz(int(user_id), role, course_id, quiz_id)
        flash("Quiz deleted successfully!", "info")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('course.web_course_details', course_id=course_id))