# tests/test_ui/test_async_operations.py

import pytest
from PyQt6.QtWidgets import QApplication
from src.ui.data_manager import UIDataManager
from src.ui.views.activity_view import ActivityView
from src.database.db_manager import DatabaseManager
from datetime import datetime
import asyncio
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_load_activities(activity_view, qtbot):
    """Prueba la carga asíncrona de actividades"""
    # Esperar a que se carguen las actividades
    await asyncio.sleep(1)
    
    # Verificar que la lista no está vacía
    assert activity_view.activities_list.count() > 0

# tests/test_ui/test_async_operations.py

@pytest.mark.asyncio
async def test_activity_selection(activity_view, mock_ui_data_manager, qtbot):
    """Prueba la selección de actividades y carga de participantes"""
    await activity_view.load_activities()
    await asyncio.sleep(0.1)
    
    first_item = activity_view.activities_list.item(0)
    assert first_item is not None
    
    # Set mock returns before calling handle_activity_selection
    mock_ui_data_manager.get_activity.return_value = {
        '_id': '1',
        'name': 'Test Activity'
    }
    
    mock_ui_data_manager.get_activity_participants.return_value = [{
        '_id': '1',
        'name': 'Test Participant',
        'birth_date': datetime.now()
    }]

    await activity_view._handle_activity_selection(first_item)
    await asyncio.sleep(0.2)
    
    assert activity_view.participants_table.rowCount() > 0

@pytest.fixture
def mock_db_manager():  # Remove async
    manager = Mock()
    manager.find_many = AsyncMock(return_value=[{
        '_id': '1',
        'name': 'Test Activity',
        'location': 'Test Location',
        'start_date': datetime.now(),
        'participant_ids': ['1', '2']
    }])
    manager.find_one = AsyncMock(return_value={
        '_id': '1',
        'name': 'Test Activity'
    })
    return manager

@pytest.fixture
def mock_ui_data_manager(mock_db_manager):
    manager = Mock()
    # Mock methods to return awaitable objects
    manager.get_all_activities = AsyncMock(return_value=[{
        '_id': '1',
        'name': 'Test Activity',
        'location': 'Test Location',
        'start_date': datetime.now(),
        'status': 'active'
    }])
    
    manager.get_activity = AsyncMock(return_value={
        '_id': '1',
        'name': 'Test Activity',
        'location': 'Test Location',
        'start_date': datetime.now()
    })
    
    manager.get_activity_participants = AsyncMock(return_value=[{
        '_id': '1',
        'name': 'Test Participant',
        'birth_date': datetime.now(),
        'status': 'active'
    }])

    manager.update_participants_table = AsyncMock()
    manager.add_participant = AsyncMock(return_value="new_id")
    
    return manager

@pytest.fixture
def activity_view(qtbot, mock_ui_data_manager, qapp, event_loop):  # Remove async
    view = ActivityView(mock_ui_data_manager)
    qtbot.addWidget(view)
    return view

@pytest.mark.asyncio
async def test_add_participant(activity_view, mock_ui_data_manager, qtbot):
    """Test adding a participant."""
    # Initial mock setup
    initial_participants = [{
        '_id': '1',
        'name': 'Initial Participant',
        'birth_date': datetime.now()
    }]
    
    new_participant = {
        '_id': '2',
        'name': 'New Participant',
        'birth_date': datetime.now(),
        'community': 'Test Community',
        'gender': 'Other',
        'education_level': 'Primary'
    }
    
    # Set up mock behavior
    mock_ui_data_manager.get_activity_participants.side_effect = [
        initial_participants,  # First call returns initial participants
        initial_participants + [new_participant]  # Second call includes new participant
    ]
    
    await activity_view.load_activities()
    first_item = activity_view.activities_list.item(0)
    await activity_view._handle_activity_selection(first_item)
    
    initial_count = activity_view.participants_table.rowCount()
    await mock_ui_data_manager.add_participant(new_participant, activity_view.current_activity_id)
    
    # Simulate reload of participants
    await activity_view._handle_activity_selection(first_item)
    await asyncio.sleep(0.1)
    
    # Verify participant was added
    assert activity_view.participants_table.rowCount() == initial_count + 1

@pytest.mark.asyncio
async def test_ui_responsiveness(activity_view, qtbot):
    """Prueba que la UI permanece responsiva durante operaciones asíncronas"""
    # Esperar a que la UI se inicialice
    await asyncio.sleep(0.1)
    
    # Verificar que los botones están en su estado inicial
    assert not activity_view.edit_activity_btn.isEnabled()
    assert not activity_view.delete_activity_btn.isEnabled()
    
    # La UI debería ser responsiva incluso durante la carga
    assert activity_view.add_activity_btn.isEnabled()