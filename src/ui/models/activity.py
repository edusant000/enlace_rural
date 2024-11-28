# src/ui/models/activity.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum

class SurveyType(Enum):
    BASELINE = "baseline"
    FOLLOWUP = "followup"
    IMPACT = "impact"

@dataclass
class SurveyTemplate:
    name: str
    questions: List[str]  # Lista de preguntas (marcadas con $)
    type: SurveyType
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "questions": self.questions,
            "type": self.type.value,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SurveyTemplate':
        return cls(
            name=data["name"],
            questions=data["questions"],
            type=SurveyType(data["type"]),
            created_at=data.get("created_at", datetime.now())
        )

@dataclass
class Activity:
    name: str
    description: Optional[str]
    survey_template: SurveyTemplate
    start_date: datetime
    end_date: Optional[datetime]
    location: str
    participant_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "survey_template": self.survey_template.to_dict(),
            "start_date": self.start_date,
            "end_date": self.end_date,
            "location": self.location,
            "participant_ids": self.participant_ids,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Activity':
        return cls(
            name=data["name"],
            description=data.get("description"),
            survey_template=SurveyTemplate.from_dict(data["survey_template"]),
            start_date=data["start_date"],
            end_date=data.get("end_date"),
            location=data["location"],
            participant_ids=data.get("participant_ids", []),
            created_at=data.get("created_at", datetime.now())
        )
