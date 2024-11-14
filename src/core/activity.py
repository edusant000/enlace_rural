from datetime import datetime, timezone
import logging
import uuid
from typing import List, Dict, Set, Optional
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActivityStatus(Enum):
    PENDING = "Pendiente"
    IN_PROGRESS = "En Curso"
    COMPLETED = "Completada"
    CANCELLED = "Cancelada"

class Activity:
    """
    Clase que representa una actividad/grupo en Enlace Rural.
    Incluye manejo de zonas horarias y validaciones mejoradas.
    """
    def __init__(self, name: str, description: str, start_date: str, 
                 end_date: str, location: str, coordinator_id: str,
                 max_participants: Optional[int] = None):
        """
        Inicializa una nueva actividad.
        
        Args:
            name: Nombre de la actividad
            description: Descripción detallada
            start_date: Fecha de inicio (DD/MM/YYYY)
            end_date: Fecha de finalización (DD/MM/YYYY)
            location: Ubicación
            coordinator_id: ID del coordinador
            max_participants: Límite de participantes (opcional)
            
        Raises:
            ValueError: Si las fechas son inválidas o el fin es anterior al inicio
        """
        self._validate_input(name, description, location, coordinator_id, max_participants)
        
        self.id = str(uuid.uuid4())[:8]
        self.name = name.strip()
        self.description = description.strip()
        
        # Validar y establecer fechas
        start = self._validate_date(start_date)
        end = self._validate_date(end_date)
        if end <= start:
            raise ValueError("La fecha de finalización debe ser posterior a la fecha de inicio")
            
        self.start_date = start
        self.end_date = end
        self.location = location.strip()
        self.coordinator_id = coordinator_id
        self.max_participants = max_participants
        
        self.participants: Set[str] = set()
        self.admins: Set[str] = {coordinator_id}
        self.status = ActivityStatus.PENDING
        self.surveys_ready = False
        
        # Timestamps en UTC
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        
        # Registro de cambios
        self.change_log = [{
            'timestamp': self.created_at.isoformat(),
            'action': 'created',
            'by': coordinator_id
        }]

    def _validate_input(self, name: str, description: str, location: str, 
                       coordinator_id: str, max_participants: Optional[int]) -> None:
        """Valida los datos de entrada básicos."""
        if not all([name, description, location, coordinator_id]):
            raise ValueError("Todos los campos obligatorios deben estar completos")
            
        if max_participants is not None and max_participants <= 0:
            raise ValueError("El número máximo de participantes debe ser positivo")

    def _validate_date(self, date_str: str) -> datetime:
        """
        Valida y convierte fecha string a datetime UTC.
        
        Args:
            date_str: Fecha en formato DD/MM/YYYY
            
        Returns:
            datetime: Fecha convertida a UTC
            
        Raises:
            ValueError: Si el formato es incorrecto
        """
        try:
            dt = datetime.strptime(date_str, '%d/%m/%Y')
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError(f"Formato de fecha incorrecto: {date_str}. Use DD/MM/YYYY")

    def add_participant(self, participant_id: str, added_by: str) -> bool:
        """
        Añade un participante a la actividad.
        
        Args:
            participant_id: ID del participante
            added_by: ID del admin que añade
            
        Returns:
            bool: True si se añadió correctamente
        """
        if not self._is_admin(added_by):
            return False
            
        if self.max_participants and len(self.participants) >= self.max_participants:
            return False
            
        if participant_id in self.participants:
            return False
            
        self.participants.add(participant_id)
        self._update_timestamp(added_by, f"added_participant_{participant_id}")
        return True

    def remove_participant(self, participant_id: str, removed_by: str) -> bool:
        """
        Elimina un participante de la actividad.
        
        Args:
            participant_id: ID del participante
            removed_by: ID del admin que elimina
            
        Returns:
            bool: True si se eliminó correctamente
        """
        if not self._is_admin(removed_by):
            return False
            
        if participant_id not in self.participants:
            return False
            
        self.participants.remove(participant_id)
        self._update_timestamp(removed_by, f"removed_participant_{participant_id}")
        return True

    def make_admin(self, participant_id: str, promoted_by: str) -> bool:
        """
        Convierte a un participante en administrador.
        
        Args:
            participant_id: ID del participante a promover
            promoted_by: ID del admin que promueve
        """
        if not self._is_admin(promoted_by) or participant_id not in self.participants:
            return False
            
        if participant_id in self.admins:
            return False
            
        self.admins.add(participant_id)
        self._update_timestamp(promoted_by, f"promoted_admin_{participant_id}")
        return True

    def update_status(self, new_status: ActivityStatus, updated_by: str) -> bool:
        """
        Actualiza el estado de la actividad.
        
        Args:
            new_status: Nuevo estado
            updated_by: ID del admin que actualiza
        """
        if not self._is_admin(updated_by):
            return False
            
        old_status = self.status
        self.status = new_status
        self._update_timestamp(updated_by, f"status_change_{old_status.value}_to_{new_status.value}")
        return True

    def verify_participant_data(self, participant_data: Dict) -> bool:
        """
        Verifica que los datos de un participante estén completos.
        
        Args:
            participant_data: Diccionario con datos del participante
        """
        required_fields = {'name', 'birth_date', 'id'}
        return all(field in participant_data and participant_data[field] 
                  for field in required_fields)

    def mark_surveys_ready(self, marked_by: str) -> bool:
        """
        Marca las encuestas como listas para imprimir.
        
        Args:
            marked_by: ID del admin que marca
        """
        if not self._is_admin(marked_by):
            return False
            
        self.surveys_ready = True
        self._update_timestamp(marked_by, "surveys_marked_ready")
        return True

    def _is_admin(self, user_id: str) -> bool:
        """Verifica si un usuario es administrador."""
        return user_id in self.admins

    def _update_timestamp(self, user_id: str, action: str) -> None:
        """
        Actualiza timestamp y log de cambios.
        
        Args:
            user_id: ID del usuario que realiza la acción
            action: Descripción de la acción realizada
        """
        now = datetime.now(timezone.utc)
        self.updated_at = now
        self.change_log.append({
            'timestamp': now.isoformat(),
            'action': action,
            'by': user_id
        })

    def to_dict(self) -> Dict:
        """
        Convierte la actividad a un diccionario para almacenamiento.
        
        Returns:
            Dict: Representación del objeto en formato diccionario
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date.strftime('%d/%m/%Y'),
            "end_date": self.end_date.strftime('%d/%m/%Y'),
            "location": self.location,
            "coordinator_id": self.coordinator_id,
            "max_participants": self.max_participants,
            "participants": list(self.participants),
            "admins": list(self.admins),
            "status": self.status.value,
            "surveys_ready": self.surveys_ready,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "change_log": self.change_log
        }

class ActivityManager:
    """Gestor de actividades/grupos."""
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.collection_name = "activities"

    def create_activity(self, name: str, description: str, start_date: str,
                       end_date: str, location: str, coordinator_id: str,
                       max_participants: Optional[int] = None) -> Optional[Activity]:
        """Crea una nueva actividad."""
        try:
            activity = Activity(name, description, start_date, end_date,
                              location, coordinator_id, max_participants)
            activity_dict = activity.to_dict()
            
            inserted_id = self.db_manager.insert_one(self.collection_name, activity_dict)
            if inserted_id:
                return activity
            return None
        except Exception as e:
            logger.error(f"Error al crear actividad: {str(e)}")
            return None

    def get_activity(self, activity_id: str) -> Optional[Dict]:
        """Obtiene una actividad por su ID."""
        return self.db_manager.find_one(self.collection_name, {"id": activity_id})

    def update_activity(self, activity_id: str, update_data: Dict) -> bool:
        """Actualiza una actividad."""
        update_data['updated_at'] = datetime.now(timezone.utc)
        return self.db_manager.update_one(
            self.collection_name,
            {"id": activity_id},
            update_data
        )

    def delete_activity(self, activity_id: str, deleted_by: str) -> bool:
        """Elimina una actividad."""
        activity = self.get_activity(activity_id)
        if not activity or deleted_by not in activity.get('admins', []):
            return False
        return self.db_manager.delete_one(self.collection_name, {"id": activity_id})

    def list_coordinator_activities(self, coordinator_id: str) -> List[Dict]:
        """Lista actividades de un coordinador."""
        return self.db_manager.find_many(
            self.collection_name,
            {"$or": [
                {"coordinator_id": coordinator_id},
                {"admins": coordinator_id}
            ]}
        )

    def list_participant_activities(self, participant_id: str) -> List[Dict]:
        """Lista actividades de un participante."""
        return self.db_manager.find_many(
            self.collection_name,
            {"participants": participant_id}
        )

    def search_activities(self, query: str) -> List[Dict]:
        """Busca actividades por nombre o descripción."""
        return self.db_manager.find_many(
            self.collection_name,
            {
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"location": {"$regex": query, "$options": "i"}}
                ]
            }
        )

    def get_pending_surveys(self) -> List[Dict]:
        """Obtiene actividades con encuestas pendientes."""
        return self.db_manager.find_many(
            self.collection_name,
            {
                "status": ActivityStatus.IN_PROGRESS.value,
                "surveys_ready": False
            }
        )
