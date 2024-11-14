from typing import Dict, List, Optional, Set
from datetime import datetime, timezone
import logging
from .id_generator import ParticipantIDGenerator  # Asegúrate de que esta importación sea correcta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParticipantError(Exception):
    """Excepción personalizada para errores relacionados con participantes."""
    pass

class Participant:
    """
    Clase que representa un participante en Enlace Rural.
    Implementa la gestión de datos personales, actividades y respuestas de encuestas.
    """
    REQUIRED_FIELDS = {'name', 'birth_date', 'community'}
    UPDATABLE_FIELDS = {'education_level', 'gender', 'community', 'income_level', 'dependents'}
    
    def __init__(self, name: str, birth_date: str, community: str, 
                 education_level: Optional[str] = None, gender: Optional[str] = None,
                 income_level: Optional[str] = None, dependents: Optional[int] = None):
        """
        Inicializa un nuevo participante.
        
        Args:
            name: Nombre completo
            birth_date: Fecha de nacimiento (DD/MM/YYYY)
            community: Comunidad
            education_level: Nivel educativo (opcional)
            gender: Género (opcional)
            income_level: Nivel de ingresos (opcional)
            dependents: Número de dependientes (opcional)
                
        Raises:
            ParticipantError: Si los datos requeridos están ausentes o son inválidos
        """
        # Inicializar id_generator primero
        self.id_generator = ParticipantIDGenerator()
        
        self._validate_required_fields(name, birth_date, community)
        
        self.id = self.id_generator.generate_id(name, birth_date)
        self.name = name
        self.birth_date = birth_date
        self.community = community
        self.education_level = education_level
        self.gender = gender
        self.income_level = income_level
        self.dependents = dependents
        self.activities: Set[str] = set()
        self.survey_responses: List[Dict] = []
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        
    def _validate_required_fields(self, name: str, birth_date: str, community: str) -> None:
        """Valida que los campos requeridos no estén vacíos."""
        if not all([name, birth_date, community]):
            raise ParticipantError("Todos los campos requeridos deben estar completos")
        
        if not self.id_generator.validate_date(birth_date):
            raise ParticipantError("Formato de fecha inválido. Use DD/MM/YYYY")

            
    def update_info(self, **kwargs) -> None:
        """
        Actualiza información del participante.
        
        Args:
            **kwargs: Pares campo-valor para actualizar
            
        Raises:
            ParticipantError: Si se intenta actualizar un campo no permitido
        """
        invalid_fields = set(kwargs.keys()) - self.UPDATABLE_FIELDS
        if invalid_fields:
            raise ParticipantError(f"Campos no actualizables: {invalid_fields}")
            
        for field, value in kwargs.items():
            setattr(self, field, value)
                
        self.updated_at = datetime.now(timezone.utc)
        
    def join_activity(self, activity_id: str) -> None:
        """
        Añade una actividad al registro del participante.
        
        Args:
            activity_id: Identificador único de la actividad
        """
        if not activity_id:
            raise ParticipantError("ID de actividad no puede estar vacío")
            
        self.activities.add(activity_id)
        self.updated_at = datetime.now(timezone.utc)
        
    def leave_activity(self, activity_id: str) -> bool:
        """
        Elimina una actividad del registro del participante.
        
        Args:
            activity_id: Identificador único de la actividad
            
        Returns:
            bool: True si se eliminó la actividad, False si no existía
        """
        if activity_id in self.activities:
            self.activities.remove(activity_id)
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False
        
    def add_survey_response(self, survey_data: Dict) -> None:
        """
        Registra una nueva respuesta de encuesta.
        
        Args:
            survey_data: Diccionario con las respuestas y metadatos de la encuesta
            
        Raises:
            ParticipantError: Si los datos de la encuesta están incompletos
        """
        required_survey_fields = {'activity_id', 'date', 'responses'}
        if not all(field in survey_data for field in required_survey_fields):
            raise ParticipantError("Datos de encuesta incompletos")
            
        survey_data['timestamp'] = datetime.now(timezone.utc)
        self.survey_responses.append(survey_data)
        self.updated_at = datetime.now(timezone.utc)
        
    def verify_data(self) -> Dict[str, bool]:
        """
        Verifica que todos los datos necesarios estén completos.
        
        Returns:
            Dict[str, bool]: Estado de cada campo requerido
        """
        verification = {
            'name': bool(self.name.strip() if self.name else ''),
            'birth_date': bool(self.birth_date.strip() if self.birth_date else ''),
            'community': bool(self.community.strip() if self.community else ''),
            'has_id': bool(self.id)
        }
        return verification
        
    def to_dict(self) -> Dict:
        """
        Convierte el participante a un diccionario para almacenamiento.
        
        Returns:
            Dict: Representación del participante en formato diccionario
        """
        return {
            "id": self.id,
            "name": self.name,
            "birth_date": self.birth_date,
            "community": self.community,
            "education_level": self.education_level,
            "gender": self.gender,
            "income_level": self.income_level,
            "dependents": self.dependents,
            "activities": list(self.activities),
            "survey_responses": self.survey_responses,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
