import os
import pytest
from PyQt6.QtWidgets import QApplication
from unittest.mock import MagicMock, AsyncMock, patch
from src.ui.dialogs import ReportsDialog
from src.utils.logger import logger
import logging

@pytest.fixture
def app(qapp):
    """Fixture que proporciona la aplicación Qt"""
    return qapp

@pytest.fixture
def mock_data_manager():
    """Fixture que proporciona un data manager mockeado"""
    manager = MagicMock()
    test_data = [
        {
            'id': 'P1',
            'name': 'Juan',
            'community': 'Comunidad A',
            'gender': 'Hombre',
            'education_level': 'Secundaria',
            'activities': ['Actividad 1'],
            'registration_date': '2024-01-01'
        },
        {
            'id': 'P2',
            'name': 'María',
            'community': 'Comunidad A',  # Cambio aquí para el test de filtros
            'gender': 'Mujer',
            'education_level': 'Preparatoria',
            'activities': ['Actividad 1'],  # Cambio aquí para el test de filtros
            'registration_date': '2024-01-01'
        }
    ]
    
    manager.get_all_activities = AsyncMock(return_value=[
        {'id': 'A1', 'name': 'Actividad 1'},
        {'id': 'A2', 'name': 'Actividad 2'}
    ])
    manager.get_all_participants = AsyncMock(return_value=test_data)
    return manager



@pytest.mark.asyncio
async def test_reports_dialog_init(app, mock_data_manager):
    """Test de inicialización del diálogo"""
    dialog = ReportsDialog(mock_data_manager)
    
    # Verificar que los componentes se inicializaron
    assert dialog.period_combo is not None
    assert dialog.activity_combo is not None
    assert dialog.community_combo is not None
    assert dialog.tab_widget is not None

@pytest.mark.asyncio
async def test_load_initial_data(app, mock_data_manager):
    """Test de carga de datos iniciales"""
    dialog = ReportsDialog(mock_data_manager)
    await dialog.load_initial_data()
    
    # Verificar que se cargaron las actividades
    assert dialog.activity_combo.count() > 1  # Incluye "Todas las actividades"
    
    # Verificar que se cargaron las comunidades
    assert dialog.community_combo.count() > 1  # Incluye "Todas las comunidades"

@pytest.mark.asyncio
async def test_update_reports(app, mock_data_manager):
    """Test de actualización de reportes"""
    dialog = ReportsDialog(mock_data_manager)
    await dialog.load_initial_data()
    await dialog.update_reports()
    
    # Verificar que los gráficos se actualizaron
    assert dialog.demo_canvas.figure is not None
    assert dialog.part_canvas.figure is not None
    assert dialog.trend_canvas.figure is not None


@pytest.mark.asyncio
async def test_filters(app, mock_data_manager):
    """Test de funcionamiento de filtros"""
    logger.info("Iniciando test de filtros")
    dialog = ReportsDialog(mock_data_manager)
    await dialog.load_initial_data()
    
    # Log de verificación
    logger.debug(f"Datos iniciales: {mock_data_manager.get_all_participants.return_value}")
    
    # Cambiar filtros
    dialog.period_combo.setCurrentText("Último mes")
    dialog.activity_combo.setCurrentText("Actividad 1")
    dialog.community_combo.setCurrentText("Comunidad A")
    
    # Aplicar filtros
    await dialog.update_reports()
    
    # Verificar filtros
    participants = await dialog.get_filtered_participants()
    logger.debug(f"Participantes filtrados: {participants}")
    
    # Verificaciones
    assert len(participants) > 0, "No se encontraron participantes con los filtros aplicados"
    for p in participants:
        assert p['community'] == 'Comunidad A', f"Comunidad incorrecta: {p['community']}"
        assert 'Actividad 1' in p['activities'], f"Actividad no encontrada en: {p['activities']}"


@pytest.mark.asyncio
async def test_export_report(app, mock_data_manager, tmp_path):
    """Test de exportación de reporte"""
    dialog = ReportsDialog(mock_data_manager)
    await dialog.load_initial_data()
    
    # Configurar ruta de exportación
    filename = tmp_path / "test_report.pdf"
    with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', 
              return_value=(str(filename), "PDF Files (*.pdf)")):
        await dialog.export_report()
    
    assert os.path.exists(filename)
    assert os.path.getsize(filename) > 0


@pytest.mark.asyncio
async def test_chart_updates(app, mock_data_manager):
    """Test de actualización de gráficos individuales"""
    logger.info("Iniciando test de actualización de gráficos")
    dialog = ReportsDialog(mock_data_manager)
    await dialog.load_initial_data()
    
    test_data = mock_data_manager.get_all_participants.return_value
    assert len(test_data) > 0, "Los datos de prueba están vacíos"
    
    # Probar actualización de gráficos demográficos
    await dialog.update_demographic_charts(test_data)
    assert dialog.demo_canvas.figure.axes, "No se crearon los ejes para el gráfico demográfico"
    
    # Probar actualización de gráficos de participación
    await dialog.update_participation_charts(test_data)
    assert len(dialog.part_canvas.figure.axes) > 0, "No se crearon los ejes para el gráfico de participación"
    
    # Probar actualización de gráficos de tendencias
    await dialog.update_trend_charts(test_data)
    assert dialog.trend_canvas.figure.axes, "No se crearon los ejes para el gráfico de tendencias"


@pytest.mark.asyncio
async def test_filter_changes(app, mock_data_manager):
    """Test de cambios en filtros"""
    dialog = ReportsDialog(mock_data_manager)
    await dialog.load_initial_data()
    
    # Simular cambios en los filtros
    dialog.period_combo.setCurrentText("Último mes")
    await dialog.update_reports()
    
    dialog.activity_combo.setCurrentText("Actividad 1")
    await dialog.update_reports()
    
    dialog.community_combo.setCurrentText("Comunidad A")
    await dialog.update_reports()
    
    # Verificar que los datos filtrados son correctos
    filtered_data = await dialog.get_filtered_participants()
    assert all(p['community'] == 'Comunidad A' for p in filtered_data)

@pytest.fixture(autouse=True)
def setup_test_logging():
    """Configurar logging específico para tests"""
    logger.setLevel(logging.DEBUG)

@pytest.mark.asyncio
async def test_error_handling(app, mock_data_manager):
    """Test de manejo de errores"""
    logger.info("Iniciando test de manejo de errores")
    dialog = ReportsDialog(mock_data_manager)
    
    # Simular error en carga de datos
    error_message = "Error de prueba"
    mock_data_manager.get_all_activities.side_effect = Exception(error_message)
    logger.debug("Configurado error simulado en get_all_activities")
    
    # Verificar que la aplicación maneja el error graciosamente
    await dialog.load_initial_data()
    assert dialog.activity_combo.count() == 1, "Debería solo tener la opción por defecto"