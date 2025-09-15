from pydantic import BaseModel, Field
from typing import List

class Turn(BaseModel):
    start: float
    end: float
    speaker: str = Field(pattern="^(agent|client)$")
    text: str

class Insight(BaseModel):
    timestamp: float
    message: str

class ScoreResult(BaseModel):
    score: int = Field(ge=0, le=100)
    client_satisfied: bool
    summary: str
    insights: List[Insight]
    topics: List[str]
    sentiment_curve: List[dict]  # [{"t":0,"sentiment":"negative"},...]

class GlobalState(BaseModel):
    uid: str
    audio_bytes: bytes = b""
    turns: List[Turn] = []
    score_result: ScoreResult | None = None