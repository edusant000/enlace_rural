import asyncio
import pytest
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtCore import Qt
from src.ui.views.survey_results_view import SurveyResultsView
from datetime import datetime
import os

# Asegurarnos de que solo hay una instancia de QApplication
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

@pytest.fixture
def mock_data_manager(mocker):
    """Fixture que proporciona un data manager mockeado."""
    manager = mocker.Mock()
    
    async def mock_get_survey_results_by_query(query):
        return [{
            "participant_id": "1",
            "activity_id": "1",
            "responses": {
                "pregunta1": "respuesta1"
            },
            "confidence": "95.5",  # Ahora es string para evitar problemas de conversión
            "processed_at": datetime.now(),
            "notes": "Nota test"
        }]
    
    async def mock_get_participant(pid):
        return {
            "_id": pid,
            "name": "Participante Test",
            "community": "Comunidad Test"
        }
    
    async def mock_get_activity(aid):
        return {
            "_id": aid,
            "name": "Actividad Test"
        }
    
    async def mock_get_all_activities():
        return [{
            "_id": "1",
            "name": "Actividad Test"
        }]
    
    async def mock_get_all_participants():
        return [{
            "_id": "1",
            "name": "Participante Test",
            "community": "Comunidad Test"
        }]
    
    async def mock_get_participants_by_community(community):
        return [{
            "_id": "1",
            "name": "Participante Test",
            "community": community
        }]

    manager.get_survey_results_by_query.side_effect = mock_get_survey_results_by_query
    manager.get_participant.side_effect = mock_get_participant
    manager.get_activity.side_effect = mock_get_activity
    manager.get_all_activities.side_effect = mock_get_all_activities
    manager.get_all_participants.side_effect = mock_get_all_participants
    manager.get_participants_by_community.side_effect = mock_get_participants_by_community
    
    return manager


@pytest.fixture
def view(qapp, mock_data_manager):
    """Fixture que proporciona una instancia de SurveyResultsView."""
    view = SurveyResultsView(mock_data_manager)
    yield view
    # Limpiar después de cada test
    view.deleteLater()

@pytest.mark.asyncio
async def test_load_activities(qapp, view, mock_data_manager):
    """Prueba la carga de actividades."""
    await view.load_activities()
    
    # Verificar que las actividades se cargaron
    assert view.activity_combo.count() == 1
    assert view.activity_combo.itemText(0) == "Actividad Test"
    
    # Verificar que las comunidades se cargaron
    assert view.community_combo.count() == 2  # "Todas las comunidades" + 1 comunidad
    assert view.community_combo.itemText(0) == "Todas las comunidades"
    assert view.community_combo.itemText(1) == "Comunidad Test"

@pytest.mark.asyncio
async def test_load_results(qapp, view, mock_data_manager):
    """Prueba la carga de resultados."""
    # Configurar estado inicial
    view.current_activity_id = "1"
    
    # Configurar el mock para devolver datos del participante
    async def mock_get_participant(pid):
        return {
            "_id": pid,
            "name": "Participante Test",
            "community": "Comunidad Test"
        }
    mock_data_manager.get_participant.side_effect = mock_get_participant
    
    async def mock_get_survey_results_by_query(query):
        return [{
            "participant_id": "1",
            "activity_id": "1",
            "responses": {
                "pregunta1": "respuesta1"
            },
            "confidence": "95.5",  # Como string
            "processed_at": datetime.now(),
            "notes": "Nota test"
        }]
    mock_data_manager.get_survey_results_by_query.side_effect = mock_get_survey_results_by_query

    # Cargar resultados
    await view.load_results()
    
    # Verificar resultados
    assert len(view.current_results) == 1
    result = view.current_results[0]
    assert result["participant_id"] == "1"
    assert result["activity_id"] == "1"
    assert result["confidence"] == "95.5"  # Comparar como string
    
    # Dar tiempo para que se actualice la tabla
    await asyncio.sleep(0.1)
    
    # Verificar tabla
    assert view.results_table.rowCount() > 0
    assert view.results_table.item(0, 0).text() == "Participante Test"
    assert view.results_table.item(0, 1).text() == "Comunidad Test"


@pytest.mark.asyncio
async def test_export_results(qapp, view, mock_data_manager, tmp_path, monkeypatch):
    """Prueba la exportación de resultados."""
    # Crear el directorio temporal si no existe
    os.makedirs(tmp_path, exist_ok=True)
    
    # Configurar estado inicial
    view.current_activity_id = "1"
    
    # Mock para get_participant y get_activity
    async def mock_get_participant(pid):
        return {
            "_id": pid,
            "name": "Participante Test",
            "community": "Comunidad Test"
        }
    mock_data_manager.get_participant.side_effect = mock_get_participant
    
    async def mock_get_activity(aid):
        return {
            "_id": aid,
            "name": "Actividad Test"
        }
    mock_data_manager.get_activity.side_effect = mock_get_activity
    
    # Mock para survey results
    async def mock_get_survey_results_by_query(query):
        return [{
            "participant_id": "1",
            "activity_id": "1",
            "responses": {
                "pregunta1": "respuesta1"
            },
            "confidence": "95.5",
            "processed_at": datetime.now(),
            "notes": "Nota test"
        }]
    mock_data_manager.get_survey_results_by_query.side_effect = mock_get_survey_results_by_query
    
    await view.load_results()  # Cargar algunos resultados primero
    
    # Crear el archivo en el directorio temporal
    filename = os.path.join(tmp_path, "test_export.csv")
    
    # Simular selección de archivo
    def mock_save_dialog(*args, **kwargs):
        return (filename, "CSV (*.csv)")
    
    monkeypatch.setattr(
        'PyQt6.QtWidgets.QFileDialog.getSaveFileName',
        mock_save_dialog
    )
    
    # Ejecutar exportación
    await view.export_results()
    
    # Dar tiempo para que se complete la escritura del archivo
    await asyncio.sleep(0.1)
    
    # Verificar que el archivo existe
    assert os.path.exists(filename)
    
    # Verificar el contenido del archivo
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
        assert 'Participante,Comunidad,Actividad,Pregunta,Respuesta,Confianza,Fecha,Notas' in content
        assert 'Participante Test' in content
        assert 'Comunidad Test' in content
        assert 'respuesta1' in content
        assert '95.5%' in content

def test_view_creation(qapp, view):
    """Prueba la creación básica de la vista."""
    assert view is not None
    assert hasattr(view, 'activity_combo')
    assert hasattr(view, 'community_combo')
    assert hasattr(view, 'results_table')

@pytest.mark.asyncio
async def test_statistics_update(qapp, view, mock_data_manager):
    """Prueba la actualización de estadísticas."""
    view.current_activity_id = "1"
    await view.load_results()
    
    # Verificar que las etiquetas de estadísticas se actualizaron
    assert "Total Encuestas: 1" in view.total_surveys_label.text()
    assert "Confianza Promedio: 95.5%" in view.avg_confidence_label.text()