# tests/test_ui/conftest.py

from asyncio.log import logger
from datetime import datetime  
from qasync import QEventLoop
import pytest
import asyncio
from PyQt6.QtWidgets import QApplication, QMessageBox, QWidget  # Añadido QWidget
from unittest.mock import Mock, AsyncMock
from src.ui.views.activity_view import ActivityView
from src.ui.views.participant_list_view import ParticipantListView
from src.ui.views.participant_filter_view import ParticipantFilterView

import qasync
from qasync import QEventLoop


@pytest.fixture(scope='session')
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app
    app.exit()

@pytest.fixture(scope='function')
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture(scope='function')
async def setup_test():
    yield
    await asyncio.sleep(0)



@pytest.fixture
def mock_batch_processor():
    processor = Mock()
    processor.process_image = AsyncMock()
    return processor

@pytest.fixture
def mock_preprocessor():
    preprocessor = Mock()
    preprocessor.preprocess_image = AsyncMock()
    return preprocessor

@pytest.fixture
def mock_data_manager():
   manager = Mock()
   manager.get_all_activities = AsyncMock(return_value=[{
       '_id': '1',
       'name': 'Test Activity',
       'location': 'Test Location',
       'start_date': datetime.now(),
       'status': 'active'
   }])
   
   manager.get_activity_participants = AsyncMock(return_value=[{
       '_id': '1', 
       'name': 'Test Participant',
       'birth_date': datetime.now(),
       'status': 'active'
   }])
   
   manager.get_activity = AsyncMock(return_value={
       '_id': '1',
       'name': 'Test Activity',
       'location': 'Test Location',
       'start_date': datetime.now()
   })
   
   manager.add_participant = AsyncMock(return_value='new_id')
   manager.get_all_participants = AsyncMock(return_value=[])
   manager.get_participants_by_community = AsyncMock(return_value=[])
   manager.delete_participant = AsyncMock(return_value=True)
   manager.update_participant = AsyncMock(return_value=True)
   
   return manager


@pytest.fixture
def mock_process_dialog():
    """Create a mock ProcessSurveysDialog."""
    dialog = Mock()
    dialog.exec = AsyncMock()
    dialog.surveys_processed = Mock()
    return dialog

@pytest.fixture
def mock_process_result():
    """Create mock survey processing results."""
    return [
        {
            "participant_id": "1",
            "responses": {"Q1": "X", "Q2": "", "Q3": "X"},
            "confidence": 0.95,
            "processed_at": "2024-01-01T00:00:00"
        },
        {
            "participant_id": "2",
            "responses": {"Q1": "", "Q2": "X", "Q3": "X"},
            "confidence": 0.92,
            "processed_at": "2024-01-01T00:00:00"
        }
    ]

@pytest.fixture
def sample_activity():
    """Create a sample activity for testing."""
    return {
        "_id": "test_activity",
        "name": "Test Activity",
        "description": "Test Description",
        "participant_ids": ["1", "2"],
        "created_at": "2024-01-01T00:00:00"
    }

@pytest.fixture
async def base_test_setup(qapp):
    loop = asyncio.get_event_loop()
    qapp._loop = loop
    yield


@pytest.fixture
async def test_activity_view(qapp, mock_data_manager, base_test_setup):
    view = ActivityView(mock_data_manager)
    await asyncio.sleep(0.1)
    return view

@pytest.fixture
def filter_view(qtbot, event_loop):
    view = ParticipantFilterView()
    qtbot.addWidget(view)
    return view

@pytest.fixture
def qtbot_async(qtbot, qapp):
    return qtbot

@pytest.fixture
def participant_view(qapp, mock_data_manager):
    view = ParticipantListView(mock_data_manager)
    return view

