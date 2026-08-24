from config.database import db

course_prerequisites = db.Table(
    'course_prerequisites',
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True),
    db.Column('prerequisite_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True)
)

class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    instructor = db.relationship('User', backref=db.backref('courses_taught', cascade="all, delete-orphan"))
    modules = db.relationship('Module', backref='course', cascade="all, delete-orphan")
    enrollments = db.relationship('Enrollment', backref='course', cascade="all, delete-orphan")
    quizzes = db.relationship('Quiz', backref='course', cascade="all, delete-orphan")
    reviews = db.relationship('CourseReview', backref='course', cascade="all, delete-orphan")
    certificates = db.relationship('Certificate', backref='course', cascade="all, delete-orphan")

    prerequisites = db.relationship(
        'Course',
        secondary=course_prerequisites,
        primaryjoin=(course_prerequisites.c.course_id == id),
        secondaryjoin=(course_prerequisites.c.prerequisite_id == id),
        backref=db.backref('prerequisite_for', lazy='dynamic')
    )

    @property
    def average_rating(self):
        if not self.reviews:
            return 0.0
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)

class Module(db.Model):
    __tablename__ = "modules"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)

    lessons = db.relationship('Lesson', backref='module', cascade="all, delete-orphan")
    materials = db.relationship('Material', backref='module', cascade="all, delete-orphan")

class Lesson(db.Model):
    __tablename__ = "lessons"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=True)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)

    progress_records = db.relationship('LessonProgress', backref='lesson', cascade="all, delete-orphan")

class Material(db.Model):
    __tablename__ = "materials"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)

class Enrollment(db.Model):
    __tablename__ = "enrollments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    progress = db.Column(db.Float, default=0.0)