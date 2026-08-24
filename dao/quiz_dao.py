from config.database import db
from models.quiz import Quiz, Question, QuizResult

class QuizDAO:
    def create_quiz(self, course_id, title):
        quiz = Quiz(course_id=course_id, title=title)
        db.session.add(quiz)
        db.session.commit()
        return quiz

    def add_question(self, quiz_id, text, a, b, c, d, correct):
        q = Question(quiz_id=quiz_id, question_text=text, option_a=a, option_b=b, option_c=c, option_d=d, correct_option=correct)
        db.session.add(q)
        db.session.commit()
        return q

    def get_quiz_by_id(self, quiz_id):
        return db.session.get(Quiz, quiz_id)

    def save_quiz_result(self, user_id, quiz_id, score):
        result = QuizResult(user_id=user_id, quiz_id=quiz_id, score=score)
        db.session.add(result)
        db.session.commit()
        return result

    def get_highest_score_for_quiz(self, user_id, quiz_id):
        result = QuizResult.query.filter_by(user_id=user_id, quiz_id=quiz_id).order_by(QuizResult.score.desc()).first()
        return result.score if result else 0.0

    def get_user_results(self, user_id):
        all_results = QuizResult.query.filter_by(user_id=user_id).all()
        highest_map = {}
        for r in all_results:
            if r.quiz_id not in highest_map or r.score > highest_map[r.quiz_id].score:
                highest_map[r.quiz_id] = r
        return list(highest_map.values())

    def delete_quiz(self, quiz_id):
        quiz = self.get_quiz_by_id(quiz_id)
        if not quiz:
            return False
        db.session.delete(quiz)
        db.session.commit()
        return True