# tests/test_ui/test_data_manager.py

from typing import Dict
import pytest
import mongomock
from datetime import datetime
from bson import ObjectId
from unittest.mock import patch, MagicMock
from src.ui.data_manager import UIDataManager
from src.core.participant import Participant
from src.database.db_manager import DatabaseManager
from datetime import datetime, timedelta
from src.ui.models.survey_result import SurveyResult

import logging

# Configuración básica del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def mock_db():
    """Create a mock MongoDB database"""
    return mongomock.MongoClient().db

@pytest.fixture
def mock_db_manager(mock_db):
    """Create a DatabaseManager with mocked MongoDB"""
    class MockDatabaseManager(DatabaseManager):
        def __init__(self):
            self.db = mock_db
            
        def find_many(self, collection, query):
            return list(self.db[collection].find(query))
            
        def find_one(self, collection, query):
            return self.db[collection].find_one(query)
            
        def insert_one(self, collection, document):
            result = self.db[collection].insert_one(document)
            return str(result.inserted_id)
            
        def update_one(self, collection, query, update):
            result = self.db[collection].update_one(query, update)
            return result.modified_count > 0
            
        def delete_one(self, collection, query):
            result = self.db[collection].delete_one(query)
            return result.deleted_count > 0

    return MockDatabaseManager()

@pytest.fixture
def ui_data_manager(mock_db_manager):
    """Create UIDataManager with mocked database"""
    manager = UIDataManager(db_manager=mock_db_manager)
    return manager


@pytest.fixture
def sample_activity_dict():
    """Sample activity data"""
    return {
        "name": "Test Activity",
        "description": "Test Description",
        "location": "Test Location",
        "start_date": datetime(2024, 1, 1),
        "end_date": datetime(2024, 12, 31),
        "participant_ids": [],
        "created_at": datetime.now()
    }

@pytest.fixture
def sample_participant_data():
    """Sample participant data"""
    return {
        "name": "Test Participant",
        "birth_date": "01/01/1990",  # Formato correcto DD/MM/YYYY
        "community": "Test Community",
        "education_level": "Primary",
        "gender": "M"
    }

@pytest.fixture
def sample_survey_result():
    """Sample survey result data"""
    return {
        "participant_id": str(ObjectId()),
        "activity_id": str(ObjectId()),
        "responses": {
            "pregunta1": "respuesta1",
            "pregunta2": "respuesta2"
        },
        "confidence": 95.5,
        "processed_at": datetime.now(),
        "notes": "Test notes"
    }

def test_get_all_activities(ui_data_manager, sample_activity_dict):
    # Insertar datos de prueba
    ui_data_manager.db_manager.db.activities.insert_one(sample_activity_dict)
    
    # Obtener actividades
    activities = ui_data_manager.get_all_activities()
    
    # Verificar resultados
    assert len(activities) == 1
    assert activities[0]["name"] == "Test Activity"

@pytest.mark.asyncio
async def test_insert_activity(ui_data_manager, sample_activity_dict):
    # Insertar actividad
    activity_id = await ui_data_manager.insert_activity(sample_activity_dict)
    
    # Verificar inserción
    assert activity_id is not None
    activity = await ui_data_manager.get_activity(activity_id)
    assert activity is not None
    assert activity["name"] == "Test Activity"

@pytest.mark.asyncio
async def test_update_activity(ui_data_manager, sample_activity_dict):
    # Insertar actividad
    activity_id = await ui_data_manager.insert_activity(sample_activity_dict)
    assert activity_id is not None
    
    # Actualizar actividad
    updated_data = sample_activity_dict.copy()
    updated_data["name"] = "Updated Activity"
    success = await ui_data_manager.update_activity(activity_id, updated_data)
    
    # Verificar actualización
    assert success is True
    activity = await ui_data_manager.get_activity(activity_id)
    assert activity["name"] == "Updated Activity"

@pytest.mark.asyncio
async def test_delete_activity(ui_data_manager, sample_activity_dict):
    # Insertar actividad
    activity_id = await ui_data_manager.insert_activity(sample_activity_dict)
    assert activity_id is not None
    
    # Eliminar actividad
    success = await ui_data_manager.delete_activity(activity_id)
    
    # Verificar eliminación
    assert success is True
    activity = await ui_data_manager.get_activity(activity_id)
    assert activity is None

@patch('src.core.participant.ParticipantIDGenerator')
def test_add_participant(mock_id_generator, ui_data_manager, sample_participant_data):
    # Configurar el mock del generador de ID
    mock_generator_instance = MagicMock()
    mock_generator_instance.generate_id.return_value = "test_id"
    mock_generator_instance.validate_date.return_value = True
    mock_id_generator.return_value = mock_generator_instance
    
    # Crear actividad primero
    activity_id = str(ObjectId())
    
    # Añadir participante
    participant_id = ui_data_manager.add_participant(sample_participant_data, activity_id)
    
    # Verificar inserción
    assert participant_id is not None
    participants = ui_data_manager.get_activity_participants(activity_id)
    assert len(participants) == 1
    assert participants[0]["name"] == "Test Participant"

# Configuración del event loop para pytest-asyncio
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# tests/test_ui/test_data_manager.py
# (Añadir estos tests al archivo existente)

@pytest.mark.asyncio
async def test_get_activities_by_location(ui_data_manager):
    """Prueba la búsqueda de actividades por ubicación"""
    # Insertar múltiples actividades
    activities = [
        {"name": "Activity 1", "location": "Location A"},
        {"name": "Activity 2", "location": "Location A"},
        {"name": "Activity 3", "location": "Location B"}
    ]
    
    for activity in activities:
        await ui_data_manager.insert_activity(activity)
    
    # Buscar por ubicación
    location_a_activities = await ui_data_manager.get_activities_by_location("Location A")
    assert len(location_a_activities) == 2

def test_get_activity_participants_empty(ui_data_manager):
    """Prueba obtener participantes de una actividad que no tiene ninguno"""
    activity_id = str(ObjectId())
    participants = ui_data_manager.get_activity_participants(activity_id)
    assert len(participants) == 0

@pytest.mark.asyncio
async def test_invalid_activity_operations(ui_data_manager):
    """Prueba operaciones con IDs de actividad inválidos"""
    invalid_id = "invalid_id"
    
    # Intentar obtener actividad inexistente
    activity = await ui_data_manager.get_activity(invalid_id)
    assert activity is None
    
    # Intentar actualizar actividad inexistente
    success = await ui_data_manager.update_activity(invalid_id, {"name": "New Name"})
    assert not success
    
    # Intentar eliminar actividad inexistente
    success = await ui_data_manager.delete_activity(invalid_id)
    assert not success

def test_add_participant_invalid_data(ui_data_manager):
    """Prueba añadir participante con datos inválidos"""
    activity_id = str(ObjectId())
    invalid_data = {
        "name": "Test Participant",
        # Falta birth_date y community
    }
    
    participant_id = ui_data_manager.add_participant(invalid_data, activity_id)
    assert participant_id is None

@pytest.mark.asyncio
async def test_activity_full_lifecycle(ui_data_manager, sample_activity_dict, sample_participant_data):
    """Prueba el ciclo de vida completo de una actividad con participantes"""
    # 1. Crear actividad
    activity_id = await ui_data_manager.insert_activity(sample_activity_dict)
    assert activity_id is not None
    
    # 2. Añadir participantes
    participant_id = ui_data_manager.add_participant(sample_participant_data, activity_id)
    assert participant_id is not None
    
    # 3. Verificar participantes
    participants = ui_data_manager.get_activity_participants(activity_id)
    assert len(participants) == 1
    
    # 4. Actualizar actividad
    updated_data = sample_activity_dict.copy()
    updated_data["name"] = "Updated Name"
    success = await ui_data_manager.update_activity(activity_id, updated_data)
    assert success
    
    # 5. Eliminar actividad
    success = await ui_data_manager.delete_activity(activity_id)
    assert success
    
    # 6. Verificar que los participantes ya no estén asociados
    participants = ui_data_manager.get_activity_participants(activity_id)
    assert len(participants) == 0


# Nuevos tests para survey_results
@pytest.mark.asyncio
async def test_save_survey_result(ui_data_manager, sample_activity_dict, sample_participant_data, sample_survey_result):
    """Test saving a new survey result"""
    # Primero crear una actividad y un participante
    activity_id = await ui_data_manager.insert_activity(sample_activity_dict)
    assert activity_id is not None
    
    # Crear participante
    participant_id = ui_data_manager.add_participant(sample_participant_data, activity_id)
    assert participant_id is not None
    
    # Actualizar sample_survey_result con los IDs reales
    sample_survey_result["activity_id"] = activity_id
    sample_survey_result["participant_id"] = participant_id
    
    # Crear resultado de encuesta
    result = SurveyResult(**sample_survey_result)
    
    # Guardar resultado
    result_id = await ui_data_manager.save_survey_result(result)
    
    # Verificar que se guardó correctamente
    assert result_id is not None
    saved_result = await ui_data_manager.get_survey_result(result_id)
    assert saved_result is not None
    assert saved_result["participant_id"] == participant_id
    assert saved_result["confidence"] == sample_survey_result["confidence"]

@pytest.mark.asyncio
async def test_get_survey_results_by_activity(ui_data_manager, sample_activity_dict, 
                                            sample_participant_data, sample_survey_result):
    """Test getting survey results for a specific activity"""
    # Crear actividad
    activity_id = await ui_data_manager.insert_activity(sample_activity_dict)
    assert activity_id is not None
    
    # Crear dos participantes
    participant1_id = ui_data_manager.add_participant(sample_participant_data, activity_id)
    participant2_id = ui_data_manager.add_participant({
        **sample_participant_data,
        "name": "Test Participant 2"
    }, activity_id)
    
    # Crear múltiples resultados para la misma actividad
    result1 = SurveyResult(**{
        **sample_survey_result,
        "activity_id": activity_id,
        "participant_id": participant1_id
    })
    result2 = SurveyResult(**{
        **sample_survey_result,
        "activity_id": activity_id,
        "participant_id": participant2_id,
        "processed_at": datetime.now() + timedelta(days=1)
    })
    
    await ui_data_manager.save_survey_result(result1)
    await ui_data_manager.save_survey_result(result2)
    
    # Obtener resultados
    results = await ui_data_manager.get_survey_results(activity_id)
    assert len(results) == 2
    assert all(r["activity_id"] == activity_id for r in results)

@pytest.mark.asyncio
async def test_get_survey_results_with_date_filter(ui_data_manager, sample_activity_dict, 
                                                 sample_participant_data, sample_survey_result):
    """Test getting survey results with date filtering"""
    # Crear actividad
    activity_id = await ui_data_manager.insert_activity(sample_activity_dict)
    assert activity_id is not None
    logger.info(f"Activity ID creado: {activity_id}")
    
    # Crear participante
    participant_id = ui_data_manager.add_participant(sample_participant_data, activity_id)
    assert participant_id is not None
    logger.info(f"Participant ID creado: {participant_id}")
    
    # Crear resultados en diferentes fechas con una hora específica
    base_date = datetime(2024, 1, 1, 12, 0)  # Fecha base fija
    logger.info(f"Fecha base: {base_date}")
    
    # Primer resultado
    result1 = SurveyResult(**{
        **sample_survey_result,
        "activity_id": activity_id,
        "participant_id": participant_id,
        "processed_at": base_date
    })
    
    # Segundo resultado (7 días después)
    result2 = SurveyResult(**{
        **sample_survey_result,
        "activity_id": activity_id,
        "participant_id": participant_id,
        "processed_at": base_date + timedelta(days=7)
    })
    
    # Guardar resultados
    result1_id = await ui_data_manager.save_survey_result(result1)
    assert result1_id is not None
    logger.info(f"Result 1 ID: {result1_id}")
    
    result2_id = await ui_data_manager.save_survey_result(result2)
    assert result2_id is not None
    logger.info(f"Result 2 ID: {result2_id}")
    
    # Verificar que los resultados se guardaron correctamente
    all_results = await ui_data_manager.get_survey_results(activity_id)
    logger.info(f"Total resultados guardados: {len(all_results)}")
    for r in all_results:
        logger.info(f"Resultado guardado: {r.get('processed_at')}")
    
    # Filtrar por fecha
    filter_end = base_date + timedelta(days=3)
    logger.info(f"Filtrando desde {base_date} hasta {filter_end}")
    
    results = await ui_data_manager.get_survey_results(
        activity_id,
        start_date=base_date,
        end_date=filter_end
    )
    
    # Verificaciones detalladas
    assert len(results) == 1, f"Se esperaba 1 resultado, se obtuvieron {len(results)}"
    if results:
        result_date = results[0]["processed_at"]  # Ya es un datetime, no necesita conversión
        logger.info(f"Fecha del resultado encontrado: {result_date}")
        assert base_date <= result_date <= filter_end, f"La fecha {result_date} no está en el rango esperado"
@pytest.mark.asyncio
async def test_update_survey_result(ui_data_manager, sample_activity_dict, 
                                  sample_participant_data, sample_survey_result):
    """Test updating a survey result"""
    # Crear actividad y participante
    activity_id = await ui_data_manager.insert_activity(sample_activity_dict)
    participant_id = ui_data_manager.add_participant(sample_participant_data, activity_id)
    
    # Crear resultado inicial
    result = SurveyResult(**{
        **sample_survey_result,
        "activity_id": activity_id,
        "participant_id": participant_id
    })
    result_id = await ui_data_manager.save_survey_result(result)
    assert result_id is not None
    
    # Actualizar resultado
    update_data = {
        "confidence": 98.0,
        "notes": "Updated notes"
    }
    success = await ui_data_manager.update_survey_result(result_id, update_data)
    
    # Verificar actualización
    assert success is True
    updated_result = await ui_data_manager.get_survey_result(result_id)
    assert updated_result["confidence"] == 98.0
    assert updated_result["notes"] == "Updated notes"


@pytest.mark.asyncio
async def test_delete_survey_result(ui_data_manager, sample_activity_dict, 
                                  sample_participant_data, sample_survey_result):
    """Test deleting a survey result"""
    # Crear actividad y participante
    activity_id = await ui_data_manager.insert_activity(sample_activity_dict)
    participant_id = ui_data_manager.add_participant(sample_participant_data, activity_id)
    
    # Crear resultado
    result = SurveyResult(**{
        **sample_survey_result,
        "activity_id": activity_id,
        "participant_id": participant_id
    })
    result_id = await ui_data_manager.save_survey_result(result)
    assert result_id is not None
    
    # Eliminar resultado
    success = await ui_data_manager.delete_survey_result(result_id)
    
    # Verificar eliminación
    assert success is True
    deleted_result = await ui_data_manager.get_survey_result(result_id)
    assert deleted_result is None

@pytest.mark.asyncio
async def test_get_survey_results_invalid_activity(ui_data_manager):
    """Test getting survey results for invalid activity"""
    results = await ui_data_manager.get_survey_results("invalid_id")
    assert len(results) == 0

@pytest.mark.asyncio
async def test_save_survey_result_validation(ui_data_manager, sample_activity_dict, 
                                           sample_participant_data, sample_survey_result):
    """Test validation when saving survey result"""
    # Primero crear una actividad y un participante válidos
    activity_id = await ui_data_manager.insert_activity(sample_activity_dict)
    participant_id = ui_data_manager.add_participant(sample_participant_data, activity_id)
    
    # Actualizar sample_survey_result con IDs válidos
    sample_survey_result["activity_id"] = activity_id
    sample_survey_result["participant_id"] = participant_id
    
    # Probar con datos válidos
    valid_result = SurveyResult(**sample_survey_result)
    result_id = await ui_data_manager.save_survey_result(valid_result)
    assert result_id is not None
    
    # Probar con datos inválidos
    with pytest.raises(ValueError):
        invalid_result = SurveyResult(**{
            **sample_survey_result,
            "activity_id": "invalid_id"  # ID de actividad inválido
        })
        await ui_data_manager.save_survey_result(invalid_result)

@pytest.mark.asyncio
async def test_get_survey_results_aggregation(ui_data_manager, sample_activity_dict, 
                                            sample_participant_data, sample_survey_result):
    """Test getting aggregated survey results statistics"""
    # Crear actividad
    activity_id = await ui_data_manager.insert_activity(sample_activity_dict)
    
    # Crear múltiples participantes
    participant_ids = []
    for i in range(3):
        participant_id = ui_data_manager.add_participant({
            **sample_participant_data,
            "name": f"Test Participant {i}"
        }, activity_id)
        participant_ids.append(participant_id)
    
    # Crear múltiples resultados
    for i, participant_id in enumerate(participant_ids):
        result = SurveyResult(**{
            **sample_survey_result,
            "activity_id": activity_id,
            "participant_id": participant_id,
            "confidence": 90.0 + i
        })
        await ui_data_manager.save_survey_result(result)
    
    # Obtener estadísticas
    stats = await ui_data_manager.get_survey_results_statistics(activity_id)
    
    assert stats is not None
    assert stats["total_results"] == 3
    assert 90.0 <= stats["avg_confidence"] <= 92.0

@pytest.mark.asyncio
async def test_save_survey_result_nonexistent_activity(ui_data_manager, sample_survey_result):
    """Test saving survey result for non-existent activity"""
    result = SurveyResult(**sample_survey_result)
    
    # Intentar guardar resultado para una actividad que no existe
    with pytest.raises(ValueError, match="Actividad no encontrada"):
        await ui_data_manager.save_survey_result(result)
