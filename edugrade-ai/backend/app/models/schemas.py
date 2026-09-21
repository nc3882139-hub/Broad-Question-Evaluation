from typing import List, Optional

from pydantic import BaseModel


class RubricOverride(BaseModel):
    question: str
    max_marks: float = 5
    reference_answer: str = ""
    concepts: Optional[List[dict]] = None


class EvaluateRequest(BaseModel):
    file_id: Optional[str] = None       # from POST /api/upload
    raw_text: Optional[str] = None      # direct-text mode (also used by the demo)
    student_name: str = "Unknown Student"
    exam_name: str = "Untitled Exam"
    rubrics: Optional[List[RubricOverride]] = None


class SentimentIn(BaseModel):
    text: str