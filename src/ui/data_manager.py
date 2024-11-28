# src/ui/data_manager.py

from typing import List, Dict, Optional, Any
import logging
import asyncio
from datetime import datetime
from bson import ObjectId
from ..database.db_manager import DatabaseManager
from ..core.activity import Activity
from ..core.participant import Participant
from .models.survey_result import SurveyResult

# Configurar el logger
logger = logging.getLogger(__name__)

class UIDataManager:
    def __init__(self, db_manager=None):
        self.db_manager = db_manager if db_manager else DatabaseManager()

        
    def _serialize_for_mongo(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert data types to MongoDB compatible format"""
        serialized = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                serialized[key] = value
            elif isinstance(value, dict):
                serialized[key] = self._serialize_for_mongo(value)
            elif isinstance(value, list):
                serialized[key] = [self._serialize_for_mongo(item) if isinstance(item, dict) else item for item in value]
            else:
                serialized[key] = value
        return serialized

    async def get_all_activities(self) -> List[Dict]:
        """Obtiene todas las actividades de la base de datos."""
        try:
            activities = await asyncio.to_thread(
                self.db_manager.find_many,
                "activities",
                {}
            )
            return sorted(activities, key=lambda x: x.get('created_at', ''), reverse=True)
        except Exception as e:
            logger.error(f"Error al obtener actividades: {e}")
            return []

            
    async def get_activity_participants(self, activity_id: str) -> List[Dict]:
        """Obtiene los participantes de una actividad específica."""
        try:
            return await asyncio.to_thread(
                self.db_manager.find_many,
                "participants",
                {"activities": activity_id}
            )
        except Exception as e:
            logger.error(f"Error al obtener participantes: {e}")
            return []

            
    async def add_participant(self, participant_data: Dict, activity_id: str) -> Optional[str]:
        """Añade un nuevo participante y lo asocia a una actividad."""
        try:
            participant = Participant(**participant_data)
            participant.join_activity(activity_id)
            return await asyncio.to_thread(
                self.db_manager.insert_one,
                "participants", 
                participant.to_dict()
            )
        except Exception as e:
            logger.error(f"Error al añadir participante: {e}")
            return None

    async def insert_activity(self, activity_data: Dict[str, Any]) -> Optional[str]:
        """Inserta una nueva actividad en la base de datos."""
        try:
            serialized_data = self._serialize_for_mongo(activity_data)
            return await asyncio.to_thread(
                self.db_manager.insert_one,
                "activities",
                serialized_data
            )
        except Exception as e:
            logger.error(f"Error al insertar actividad: {e}")
            return None

    async def get_activity(self, activity_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una actividad por su ID."""
        try:
            return await asyncio.to_thread(
                self.db_manager.find_one,
                "activities",
                {"_id": ObjectId(activity_id)}
            )
        except Exception as e:
            logger.error(f"Error al obtener actividad: {e}")
            return None

    async def update_activity(self, activity_id: str, activity_data: Dict[str, Any]) -> bool:
        """Actualiza una actividad existente."""
        try:
            serialized_data = self._serialize_for_mongo(activity_data)
            result = await asyncio.to_thread(
                self.db_manager.update_one,
                "activities",
                {"_id": ObjectId(activity_id)},
                {"$set": serialized_data}
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Error al actualizar actividad: {e}")
            return False

    async def delete_activity(self, activity_id: str) -> bool:
        """Elimina una actividad por su ID y limpia las referencias."""
        try:
            # Primero, obtener todos los participantes de la actividad
            participants = self.get_activity_participants(activity_id)
            
            # Eliminar la referencia a la actividad de cada participante
            for participant in participants:
                participant_id = str(participant["_id"])
                await asyncio.to_thread(
                    self.db_manager.update_one,
                    "participants",
                    {"_id": ObjectId(participant_id)},
                    {"$pull": {"activities": activity_id}}
                )
            
            # Luego eliminar la actividad
            result = await asyncio.to_thread(
                self.db_manager.delete_one,
                "activities",
                {"_id": ObjectId(activity_id)}
            )
            
            return bool(result)
        except Exception as e:
            logger.error(f"Error al eliminar actividad: {e}")
            return False

    async def get_activities_by_location(self, location: str) -> List[Dict[str, Any]]:
        """Obtiene actividades por ubicación."""
        try:
            return await asyncio.to_thread(
                self.db_manager.find_many,
                "activities",
                {"location": location}
            )
        except Exception as e:
            logger.error(f"Error al obtener actividades por ubicación: {e}")
            return []
        
    async def save_survey_result(self, result: SurveyResult) -> Optional[str]:
        """
        Guarda un nuevo resultado de encuesta en la base de datos.
        """
        try:
            # Validar que la actividad existe
            try:
                activity = await self.get_activity(result.activity_id)
            except Exception as e:
                raise ValueError(f"ID de actividad inválido: {str(e)}")
                
            if not activity:
                raise ValueError(f"Actividad no encontrada: {result.activity_id}")

            # Validar que el participante existe y está en la actividad
            participants = self.get_activity_participants(result.activity_id)
            participant_ids = [str(p.get("_id")) for p in participants]
            
            if result.participant_id not in participant_ids:
                raise ValueError(f"Participante no encontrado en la actividad: {result.participant_id}")

            # Convertir a diccionario y serializar
            result_dict = result.to_dict()
            result_dict = self._serialize_for_mongo(result_dict)
            
            inserted_id = await asyncio.to_thread(
                self.db_manager.insert_one,
                "survey_results",
                result_dict
            )
            
            if not inserted_id:
                raise ValueError("Error al insertar el resultado en la base de datos")
                
            return inserted_id
            
        except ValueError as ve:
            logger.error(f"Error de validación: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"Error al guardar resultado de encuesta: {str(e)}")
            return None

    async def get_survey_results(
        self,
        activity_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        try:
            # Crear la consulta base
            query = {"activity_id": activity_id}
            
            # Ajustar el formato de las fechas si existen
            if start_date or end_date:
                date_query = {}
                if start_date:
                    # Asegurar que la fecha está en UTC
                    date_query["$gte"] = start_date.replace(microsecond=0)
                    logger.info(f"Start date query: {date_query['$gte']}")
                if end_date:
                    date_query["$lte"] = end_date.replace(microsecond=0)
                    logger.info(f"End date query: {date_query['$lte']}")
                    
                query["processed_at"] = date_query

            logger.info(f"Query final: {query}")
            
            # Obtener resultados
            results = await asyncio.to_thread(
                self.db_manager.find_many,
                "survey_results",
                query
            )
            
            logger.info(f"Resultados encontrados: {len(results)}")
            for r in results:
                logger.info(f"Fecha encontrada: {r.get('processed_at')}")
            
            # Convertir resultados
            processed_results = []
            for r in results:
                try:
                    processed = SurveyResult.from_dict(r).to_dict()
                    processed_results.append(processed)
                except Exception as e:
                    logger.error(f"Error procesando resultado: {e}", exc_info=True)
                    continue
                    
            return processed_results
                
        except Exception as e:
            logger.error(f"Error al obtener resultados de encuestas: {e}")
            return []
    
    async def get_survey_result(self, result_id: str) -> Optional[Dict]:
        """
        Obtiene un resultado específico por su ID.
        
        Args:
            result_id: ID del resultado a buscar
            
        Returns:
            Dict: Resultado de la encuesta o None si no se encuentra
        """
        try:
            result = await asyncio.to_thread(
                self.db_manager.find_one,
                "survey_results",
                {"_id": ObjectId(result_id)}
            )
            
            return SurveyResult.from_dict(result).to_dict() if result else None
            
        except Exception as e:
            logger.error(f"Error al obtener resultado de encuesta: {e}")
            return None

    async def get_survey_results(
        self,
        activity_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Obtiene los resultados de encuestas para una actividad específica.
        
        Args:
            activity_id: ID de la actividad
            start_date: Fecha inicial para filtrar resultados (opcional)
            end_date: Fecha final para filtrar resultados (opcional)
            
        Returns:
            List[Dict]: Lista de resultados de encuestas
        """
        try:
            query = {"activity_id": activity_id}
            
            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query["$gte"] = start_date.replace(microsecond=0)
                if end_date:
                    date_query["$lte"] = end_date.replace(microsecond=0)
                    
                query["processed_at"] = date_query

            results = await asyncio.to_thread(
                self.db_manager.find_many,
                "survey_results",
                query
            )
            
            processed_results = []
            for r in results:
                try:
                    processed = SurveyResult.from_dict(r).to_dict()
                    processed_results.append(processed)
                except Exception as e:
                    logger.error(f"Error procesando resultado {r.get('_id')}: {str(e)}")
                    continue
                    
            return processed_results
                
        except Exception as e:
            logger.error(f"Error al obtener resultados de encuestas: {str(e)}")
            return []
    
    async def update_survey_result(
        self, 
        result_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """
        Actualiza un resultado existente.
        """
        try:
            # Obtener resultado actual
            current_result = await self.get_survey_result(result_id)
            if not current_result:
                raise ValueError(f"Resultado no encontrado: {result_id}")

            # Actualizar solo los campos proporcionados
            updated_data = {**current_result, **updates}
            
            # Validar y convertir a instancia de SurveyResult
            try:
                result = SurveyResult.from_dict(updated_data)
            except Exception as e:
                raise ValueError(f"Datos de actualización inválidos: {str(e)}")
            
            # Serializar y actualizar
            result_dict = self._serialize_for_mongo(result.to_dict())
            updated = await asyncio.to_thread(
                self.db_manager.update_one,
                "survey_results",
                {"_id": ObjectId(result_id)},
                {"$set": result_dict}
            )
            
            if not updated:
                raise ValueError("No se pudo actualizar el resultado")
                
            return True
                
        except ValueError as ve:
            logger.error(f"Error de validación: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"Error al actualizar resultado de encuesta: {str(e)}")
            return False

    async def delete_survey_result(self, result_id: str) -> bool:
        """
        Elimina un resultado de encuesta.
        
        Args:
            result_id: ID del resultado a eliminar
            
        Returns:
            bool: True si la eliminación fue exitosa
        """
        try:
            return await asyncio.to_thread(
                self.db_manager.delete_one,
                "survey_results",
                {"_id": ObjectId(result_id)}
            )
        except Exception as e:
            logger.error(f"Error al eliminar resultado de encuesta: {e}")
            return False
        
    async def get_survey_results_statistics(self, activity_id: str) -> Dict:
        """
        Obtiene estadísticas agregadas de los resultados de una actividad.
        """
        try:
            results = await self.get_survey_results(activity_id)
            if not results:
                return {
                    "total_results": 0,
                    "avg_confidence": 0.0,
                    "completion_rate": 0.0
                }

            # Convertir resultados a instancias de SurveyResult
            survey_results = [SurveyResult.from_dict(r) for r in results]
            
            # Calcular estadísticas
            total_results = len(survey_results)
            avg_confidence = sum(r.confidence for r in survey_results) / total_results
            completion_rate = sum(
                1 for r in survey_results if r.is_complete()
            ) / total_results * 100

            return {
                "total_results": total_results,
                "avg_confidence": round(avg_confidence, 2),
                "completion_rate": round(completion_rate, 2)
            }
                
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return {
                "total_results": 0,
                "avg_confidence": 0.0,
                "completion_rate": 0.0
            }
        
    async def get_all_participants(self) -> List[Dict]:
        """Obtiene todos los participantes de la base de datos."""
        try:
            return await asyncio.to_thread(
                self.db_manager.find_many,
                "participants",
                {}
            )
        except Exception as e:
            logger.error(f"Error al obtener todos los participantes: {e}")
            return []

    async def get_participant(self, participant_id: str) -> Optional[Dict]:
        """Obtiene un participante por su ID."""
        try:
            participant = await asyncio.to_thread(
                self.db_manager.find_one,
                "participants",
                {"_id": ObjectId(participant_id)}
            )
            return participant
        except Exception as e:
            logger.error(f"Error al obtener participante: {e}")
            return None

    async def get_participants_by_community(self, community: str) -> List[Dict]:
        """Obtiene los participantes de una comunidad específica."""
        try:
            return await asyncio.to_thread(
                self.db_manager.find_many,
                "participants",
                {"community": community}
            )
        except Exception as e:
            logger.error(f"Error al obtener participantes por comunidad: {e}")
            return []

    async def get_survey_results_by_query(self, query: Dict) -> List[Dict]:
        """
        Obtiene resultados de encuestas según un query específico.
        Este método es más flexible que get_survey_results y permite filtros más complejos.
        """
        try:
            results = await asyncio.to_thread(
                self.db_manager.find_many,
                "survey_results",
                query
            )
            
            processed_results = []
            for r in results:
                try:
                    processed = SurveyResult.from_dict(r).to_dict()
                    processed_results.append(processed)
                except Exception as e:
                    logger.error(f"Error procesando resultado {r.get('_id')}: {str(e)}")
                    continue
                    
            return processed_results
                
        except Exception as e:
            logger.error(f"Error al obtener resultados de encuestas: {str(e)}")
            return []
