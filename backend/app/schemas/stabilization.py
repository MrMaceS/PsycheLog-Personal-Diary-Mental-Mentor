from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ExerciseType(str, Enum):
    BREATHING = "breathing"
    GROUNDING_54321 = "grounding_54321"
    AFFIRMATION = "affirmation"


class StabilizationSessionResponse(BaseModel):
    session_id: str
    exercise_type: ExerciseType
    instruction: str
    duration_seconds: int
    can_use_ai_followup: bool


class StabilizationCompleteRequest(BaseModel):
    session_id: str
    mood_after: Optional[str] = Field(None, max_length=50)
    brief_note: Optional[str] = Field(None, max_length=500)