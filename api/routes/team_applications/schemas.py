from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, TypeAdapter, model_validator


class QuestionType(str, Enum):
    multiple_choice = "multiple_choice"
    input = "input"


class MultipleChoiceQuestion(BaseModel):
    id: str
    question: str
    type: Literal[QuestionType.multiple_choice]
    options: List[str] = Field(min_length=1)
    required: bool = True


class InputQuestion(BaseModel):
    id: str
    question: str
    type: Literal[QuestionType.input]
    required: bool = True
    placeholder: Optional[str] = None


Question = MultipleChoiceQuestion | InputQuestion


class TeamApplicationBase(BaseModel):
    team_id: UUID
    questions: List[Question] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_unique_question_ids(self) -> "TeamApplicationBase":
        ids = [q.id for q in self.questions]
        if len(ids) != len(set(ids)):
            raise ValueError("Question ids must be unique within a team application")
        return self


class TeamApplicationUpdate(BaseModel):
    questions: Optional[List[Question]] = None

    @model_validator(mode="after")
    def _validate_unique_question_ids(self) -> "TeamApplicationUpdate":
        if self.questions is None:
            return self
        ids = [q.id for q in self.questions]
        if len(ids) != len(set(ids)):
            raise ValueError("Question ids must be unique within a team application")
        return self


class TeamApplicationResponse(BaseModel):
    team_id: UUID
    questions: List[Question]


def pack_metadata(questions: List[Question]) -> Dict[str, Any]:
    return {"questions": [q.model_dump() for q in questions]}


def unpack_metadata(metadata_json: Dict[str, Any]) -> List[Question]:
    raw_questions = (metadata_json or {}).get("questions", [])
    adapter: TypeAdapter[List[Question]] = TypeAdapter(List[Question])  # type: ignore[arg-type]
    return adapter.validate_python(raw_questions)

