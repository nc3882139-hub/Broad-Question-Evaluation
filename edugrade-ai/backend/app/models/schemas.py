from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RubricOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str
    max_marks: float = Field(default=5, gt=0, le=1000)
    reference_answer: str = Field(default="", max_length=50000)
    concepts: Optional[List[dict]] = None


class EvaluateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_id: Optional[str] = None       # from POST /api/upload
    raw_text: Optional[str] = Field(default=None, max_length=200000)
    student_name: str = Field(default="Unknown Student", max_length=200)
    exam_name: str = Field(default="Untitled Exam", max_length=200)
    rubrics: Optional[List[RubricOverride]] = None

    @field_validator("file_id")
    @classmethod
    def valid_file_id(cls, value):
        if value is not None and not value.isdigit():
            raise ValueError("file_id must be a numeric identifier")
        return value


class SentimentIn(BaseModel):
    text: str = Field(min_length=1, max_length=200000)