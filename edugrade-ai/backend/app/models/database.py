from datetime import datetime

from sqlalchemy import (JSON, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text, create_engine, inspect, text)
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(128), index=True, nullable=True)


class AnswerSheet(Base):
    __tablename__ = "answer_sheets"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    filename = Column(String(500))
    file_path = Column(String(1000))
    pages = Column(Integer, default=1)
    status = Column(String(40), default="uploaded")   # uploaded|parsed|evaluated
    text_mode = Column(Integer, default=0)            # 1 = PDF had a text layer
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(128), index=True, nullable=True)


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    sheet_id = Column(Integer, ForeignKey("answer_sheets.id"))
    number = Column(Integer)
    text = Column(Text)
    page = Column(Integer, default=1)


class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True)
    question_row_id = Column(Integer, ForeignKey("questions.id"))
    text = Column(Text)
    pages = Column(String(100), default="")


class Rubric(Base):
    __tablename__ = "rubrics"
    id = Column(Integer, primary_key=True)
    external_id = Column(String(120), index=True)
    question_text = Column(Text)
    max_marks = Column(Float, default=5)
    reference_answer = Column(Text, default="")
    source = Column(String(30), default="teacher")
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(128), index=True, nullable=True)
    approval_status = Column(String(20), default="approved")


class Concept(Base):
    __tablename__ = "concepts"
    id = Column(Integer, primary_key=True)
    rubric_row_id = Column(Integer, ForeignKey("rubrics.id"))
    concept = Column(Text)
    weight = Column(Float, default=1)
    optional = Column(Integer, default=0)


class Evaluation(Base):
    __tablename__ = "evaluations"
    id = Column(Integer, primary_key=True)
    sheet_id = Column(Integer, ForeignKey("answer_sheets.id"), nullable=True)
    result_json = Column(Text)
    total_score = Column(Float)
    max_marks = Column(Float)
    percentage = Column(Float)
    confidence = Column(Float)
    processing_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(128), index=True, nullable=True)
    review_status = Column(String(30), default="review_required")
    teacher_score = Column(Float, nullable=True)
    locked = Column(Integer, default=0)


class SentimentResult(Base):
    __tablename__ = "sentiment_results"
    id = Column(Integer, primary_key=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"))
    question_number = Column(Integer)
    label = Column(String(30))
    probabilities = Column(JSON)
    confidence = Column(Float)


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"))
    report_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)
    if not settings.DATABASE_URL.startswith("sqlite"):
        return
    additions = {
        "students": {"user_id": "VARCHAR(128)"},
        "answer_sheets": {"user_id": "VARCHAR(128)"},
        "rubrics": {"user_id": "VARCHAR(128)", "approval_status": "VARCHAR(20)"},
        "evaluations": {"user_id": "VARCHAR(128)", "review_status": "VARCHAR(30)",
                        "teacher_score": "FLOAT", "locked": "INTEGER"},
    }
    with engine.begin() as connection:
        tables = inspect(connection)
        for table, columns in additions.items():
            existing = {c["name"] for c in tables.get_columns(table)}
            for name, sql_type in columns.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()