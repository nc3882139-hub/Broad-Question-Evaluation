from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services import rubric_service

router = APIRouter(prefix="/api", tags=["rubrics"])


class ConceptIn(BaseModel):
    concept: str
    weight: float = 1
    optional: bool = False


class RubricIn(BaseModel):
    question: str
    max_marks: float = 5
    reference_answer: str = ""
    concepts: Optional[List[ConceptIn]] = None
    auto_suggest: bool = True


class SuggestIn(BaseModel):
    question: str = ""
    reference_answer: str
    max_marks: float = 5


@router.post("/rubric/suggest")
def suggest(payload: SuggestIn):
    return rubric_service.suggest_concepts(payload.reference_answer, payload.max_marks,
                                           question=payload.question)


@router.post("/rubric")
def create_rubric(payload: RubricIn, db: Session = Depends(get_db)):
    concepts = payload.concepts
    if not concepts and payload.auto_suggest and payload.reference_answer.strip():
        concepts = [ConceptIn(**c) for c in rubric_service.suggest_concepts(
            payload.reference_answer, payload.max_marks, question=payload.question)["concepts"]]
    if not concepts:
        concepts = [ConceptIn(concept=payload.question, weight=payload.max_marks)]
    rubric = rubric_service.save_rubric({
        "question": payload.question, "max_marks": payload.max_marks,
        "reference_answer": payload.reference_answer, "source": "teacher",
        "concepts": [c.model_dump() if hasattr(c, "model_dump") else c.dict() for c in concepts]}, db)
    return rubric


@router.get("/rubrics")
def list_rubrics(db: Session = Depends(get_db)):
    return rubric_service.list_rubrics(db)


@router.get("/rubric/{rubric_id}")
def get_rubric(rubric_id: str, db: Session = Depends(get_db)):
    r = rubric_service.get_rubric(db, rubric_id)
    if not r:
        raise HTTPException(404, "Rubric not found")
    return r