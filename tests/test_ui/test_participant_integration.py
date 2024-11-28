# tests/test_ui/test_participant_integration.py

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from datetime import datetime
from unittest.mock import AsyncMock, Mock
import logging
logger = logging.getLogger(__name__)

@pytest.fixture
def mock_integration_data():
    return [
        {
            'id': '1',
            'name': 'Juan Pérez',
            'community': 'Comunidad A',
            'birth_date': '1990-01-01',
            'gender': 'Masculino',
            'education_level': 'Universidad',
            'status': 'Activo'
        },
        {
            'id': '2',
            'name': 'María García',
            'community': 'Comunidad B',
            'birth_date': '1995-06-15',
            'gender': 'Femenino',
            'education_level': 'Preparatoria',
            'status': 'Activo'
        }
    ]

@pytest.mark.asyncio
async def test_filter_integration(qtbot, participant_view, mock_data_manager, mock_integration_data):
    """Test de integración del sistema de filtrado"""
    mock_data_manager.get_all_participants = AsyncMock(return_value=mock_integration_data)
    
    # Agregar log para debug
    logger.debug(f"Mock data: {mock_integration_data}")
    
    await participant_view.load_participants()
    qtbot.wait(100)  # Dar tiempo para que se actualice la UI

    logger.debug(f"Community filter items: {[participant_view.filter_view.community_filter.itemText(i) for i in range(participant_view.filter_view.community_filter.count())]}")

@pytest.mark.asyncio
async def test_filter_db_integration(qtbot, participant_view, mock_data_manager, mock_integration_data):
    """Test de integración del filtrado con la base de datos"""
    filtered_data = [d for d in mock_integration_data if d['community'] == 'Comunidad A']
    mock_data_manager.get_all_participants = AsyncMock(return_value=mock_integration_data)
    mock_data_manager.get_participants_by_community = AsyncMock(return_value=filtered_data)
    
    await participant_view.load_participants()
    qtbot.wait(100)
    
    filters = {
        'name': '',
        'community': 'Comunidad A',
        'age_range': 'Todas las edades',
        'gender': 'Todos',
        'education': 'Todos'
    }
    
    await participant_view.apply_filters(filters)
    visible_rows = [i for i in range(participant_view.participants_table.rowCount()) 
                   if not participant_view.participants_table.isRowHidden(i)]
    assert len(visible_rows) == 1
    assert participant_view.participants_table.item(visible_rows[0], 2).text() == 'Comunidad A'



@pytest.mark.asyncio
async def test_filter_error_handling(qtbot, participant_view, mock_data_manager):
    """Test del manejo de errores en la integración"""
    # Simular error en la base de datos
    mock_data_manager.get_all_participants.side_effect = Exception("Error de conexión")
    
    # Intentar cargar participantes
    await participant_view.load_participants()
    
    # Verificar que la tabla está vacía
    assert participant_view.participants_table.rowCount() == 0
    
    # Verificar que los filtros están en estado inicial
    assert participant_view.filter_view.community_filter.currentText() == "Todas las comunidades"