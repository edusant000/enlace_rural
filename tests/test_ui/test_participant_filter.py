# tests/test_ui/test_participant_filter.py

import pytest
from PyQt6.QtCore import Qt
from datetime import datetime
from src.ui.views.participant_filter_view import ParticipantFilterView

@pytest.fixture
def filter_view(qtbot):
    view = ParticipantFilterView()
    qtbot.addWidget(view)
    return view

@pytest.mark.asyncio
async def test_filter_signals(filter_view, qtbot):
    """Test that filter signals are emitted correctly"""
    signals_received = []
    filter_view.filtersChanged.connect(lambda f: signals_received.append(f))
    
    # Clear any pending signals
    qtbot.wait(100)
    signals_received.clear()
    
    # Set text all at once instead of individual keystrokes
    filter_view.name_filter.setText("Test")
    qtbot.wait(100)
    
    assert len(signals_received) == 1
    assert signals_received[0]['name'] == "Test"

@pytest.mark.asyncio
async def test_community_filter(filter_view, qtbot):
    filter_view.community_filter.addItem("Community 1")
    filter_view.community_filter.setCurrentText("Community 1")
    
    assert filter_view.community_filter.currentText() == "Community 1"