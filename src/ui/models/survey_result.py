# src/ui/models/survey_result.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
from .activity import Activity

@dataclass
class SurveyResult:
    """Modelo para los resultados de una encuesta."""
    participant_id: str
    activity_id: str
    responses: Dict[str, str]
    confidence: float
    processed_at: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convierte el resultado a diccionario para almacenamiento."""
        return {
            "participant_id": self.participant_id,
            "activity_id": self.activity_id,
            "responses": self.responses,
            "confidence": self.confidence,
            "processed_at": self.processed_at.replace(microsecond=0),  # Normalizar la fecha
            "notes": self.notes
        }
    @classmethod
    def from_dict(cls, data: Dict) -> 'SurveyResult':
        """Crea una instancia desde un diccionario."""
        processed_at = data["processed_at"]
        if isinstance(processed_at, str):
            processed_at = datetime.fromisoformat(processed_at.replace('Z', '+00:00'))
        
        return cls(
            participant_id=data["participant_id"],
            activity_id=data["activity_id"],
            responses=data["responses"],
            confidence=data["confidence"],
            processed_at=processed_at,
            notes=data.get("notes")
        )

    def is_complete(self) -> bool:
        """Verifica si todas las preguntas tienen respuesta."""
        return all(bool(answer.strip()) for answer in self.responses.values())

    def get_completion_rate(self) -> float:
        """Calcula la tasa de completitud."""
        if not self.responses:
            return 0.0
        answered = sum(1 for answer in self.responses.values() if answer.strip())
        return (answered / len(self.responses)) * 100