from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
import logging
from ..models.activity import Activity as UIActivity, SurveyTemplate
from ...core.activity import Activity as DBActivity, ActivityStatus
from ..data_manager import UIDataManager

logger = logging.getLogger(__name__)

class ActivityController:
    def __init__(self, data_manager: UIDataManager):
        self.data_manager = data_manager
    
    def _convert_to_ui_model(self, db_activity: Dict) -> UIActivity:
        """Convierte un modelo de base de datos a modelo UI"""
        try:
            # Crear SurveyTemplate
            survey_template = SurveyTemplate(
                name=db_activity.get('survey_template', {}).get('name', ''),
                questions=db_activity.get('survey_template', {}).get('questions', []),
                type=db_activity.get('survey_template', {}).get('type', 'baseline')
            )
            
            # Crear Activity UI
            return UIActivity(
                name=db_activity.get('name', ''),
                description=db_activity.get('description', ''),
                survey_template=survey_template,
                start_date=db_activity.get('start_date', datetime.now()),
                end_date=db_activity.get('end_date'),
                location=db_activity.get('location', ''),
                participant_ids=db_activity.get('participant_ids', [])
            )
        except Exception as e:
            logger.error(f"Error al convertir a modelo UI: {e}")
            raise

    def _convert_to_db_model(self, ui_activity: UIActivity) -> Dict:
        """Convierte un modelo UI a modelo de base de datos"""
        try:
            return {
                "name": ui_activity.name,
                "description": ui_activity.description,
                "survey_template": ui_activity.survey_template.to_dict(),
                "start_date": ui_activity.start_date,
                "end_date": ui_activity.end_date,
                "location": ui_activity.location,
                "participant_ids": ui_activity.participant_ids,
                "status": ActivityStatus.PENDING.value,
                "updated_at": datetime.now()
            }
        except Exception as e:
            logger.error(f"Error al convertir a modelo DB: {e}")
            raise

    async def create_activity(self, activity: UIActivity) -> str:
        """Crea una nueva actividad"""
        try:
            db_activity = self._convert_to_db_model(activity)
            activity_id = await self.data_manager.insert_activity(db_activity)
            logger.info(f"Actividad creada con ID: {activity_id}")
            return activity_id
        except Exception as e:
            logger.error(f"Error al crear actividad: {e}")
            raise

    async def get_activity(self, activity_id: str) -> Optional[UIActivity]:
        """Obtiene una actividad por su ID"""
        try:
            db_activity = await self.data_manager.get_activity(activity_id)
            if db_activity:
                return self._convert_to_ui_model(db_activity)
            return None
        except Exception as e:
            logger.error(f"Error al obtener actividad: {e}")
            raise

    async def update_activity(self, activity_id: str, activity: UIActivity) -> bool:
        """Actualiza una actividad existente"""
        try:
            db_activity = self._convert_to_db_model(activity)
            success = await self.data_manager.update_activity(activity_id, db_activity)
            logger.info(f"Actividad {activity_id} actualizada: {success}")
            return success
        except Exception as e:
            logger.error(f"Error al actualizar actividad: {e}")
            raise

    async def delete_activity(self, activity_id: str) -> bool:
        """Elimina una actividad por su ID"""
        try:
            success = await self.data_manager.delete_activity(activity_id)
            logger.info(f"Actividad {activity_id} eliminada: {success}")
            return success
        except Exception as e:
            logger.error(f"Error al eliminar actividad: {e}")
            raise

    async def search_activities(self, query: str = "", 
                              filters: Dict = None) -> List[UIActivity]:
        """
        Busca actividades con filtros avanzados
        
        Args:
            query: Texto de búsqueda
            filters: Diccionario con filtros adicionales como:
                    - status: Estado de la actividad
                    - date_range: Tuple[datetime, datetime]
                    - location: str
        """
        try:
            # Construir query completa
            db_query = {}
            
            # Búsqueda por texto
            if query:
                db_query["$or"] = [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"location": {"$regex": query, "$options": "i"}}
                ]
            
            # Aplicar filtros adicionales
            if filters:
                if "status" in filters:
                    db_query["status"] = filters["status"]
                
                if "date_range" in filters:
                    start, end = filters["date_range"]
                    db_query["start_date"] = {"$gte": start, "$lte": end}
                
                if "location" in filters:
                    db_query["location"] = filters["location"]

            # Obtener resultados
            db_activities = await self.data_manager.find_many("activities", db_query)
            
            # Convertir a modelos UI
            return [self._convert_to_ui_model(act) for act in db_activities]
            
        except Exception as e:
            logger.error(f"Error en búsqueda de actividades: {e}")
            raise

    async def get_activity_statistics(self, activity_id: str) -> Dict:
        """Obtiene estadísticas de una actividad"""
        try:
            participants = await self.data_manager.get_activity_participants(activity_id)
            survey_results = await self.data_manager.get_survey_results(activity_id)
            
            return {
                "total_participants": len(participants),
                "total_surveys": len(survey_results),
                "completion_rate": len(survey_results) / len(participants) * 100 if participants else 0,
                "last_update": datetime.now()
            }
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            raise

    async def get_recent_activities(self, days: int = 7) -> List[UIActivity]:
        """Obtiene actividades recientes"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            db_activities = await self.data_manager.find_many(
                "activities",
                {
                    "start_date": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                }
            )
            
            return [self._convert_to_ui_model(act) for act in db_activities]
        except Exception as e:
            logger.error(f"Error al obtener actividades recientes: {e}")
            raise

    async def get_activities_by_location(self, location: str) -> List[UIActivity]:
        """Obtiene actividades por ubicación"""
        try:
            db_activities = await self.data_manager.find_many(
                "activities",
                {"location": {"$regex": location, "$options": "i"}}
            )
            return [self._convert_to_ui_model(act) for act in db_activities]
        except Exception as e:
            logger.error(f"Error al obtener actividades por ubicación: {e}")
            raise

    async def manage_participants(self, activity_id: str, 
                                participant_ids: List[str], 
                                action: str) -> bool:
        """
        Gestiona participantes de una actividad
        
        Args:
            activity_id: ID de la actividad
            participant_ids: Lista de IDs de participantes
            action: "add" o "remove"
        """
        try:
            activity = await self.data_manager.get_activity(activity_id)
            if not activity:
                raise ValueError(f"Actividad no encontrada: {activity_id}")

            current_participants = set(activity.get('participant_ids', []))
            
            if action == "add":
                current_participants.update(participant_ids)
            elif action == "remove":
                current_participants.difference_update(participant_ids)
            else:
                raise ValueError(f"Acción no válida: {action}")

            # Actualizar actividad
            success = await self.data_manager.update_activity(
                activity_id,
                {"participant_ids": list(current_participants)}
            )
            
            logger.info(
                f"Participantes {action}ed en actividad {activity_id}: {success}"
            )
            return success
            
        except Exception as e:
            logger.error(f"Error al gestionar participantes: {e}")
            raise