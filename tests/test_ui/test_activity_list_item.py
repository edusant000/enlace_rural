# tests/test_ui/test_activity_list_item.py

import pytest
from PyQt6.QtWidgets import QListWidgetItem, QMenu
from datetime import datetime
from src.ui.views.activity_view import ActivityListItem
from PyQt6.QtGui import QAction

@pytest.fixture
def sample_activity():
    return {
        'name': 'Actividad Test',
        'location': 'Ubicación Test',
        'start_date': datetime.now(),
        'status': 'active',
        'participant_ids': ['1', '2', '3'],
        'max_participants': 10,
        'surveys_ready': False
    }

def test_activity_list_item_creation(sample_activity):
    """Prueba la creación básica de un ActivityListItem"""
    item = ActivityListItem(sample_activity)
    assert isinstance(item, QListWidgetItem)
    assert 'Actividad Test' in item.text()
    assert 'Ubicación Test' in item.text()

def test_activity_list_item_with_empty_activity():
    """Prueba la creación con datos mínimos"""
    item = ActivityListItem({})
    assert 'Sin nombre' in item.text()
    assert 'Sin ubicación' in item.text()

def test_activity_list_item_status_display(sample_activity):
    """Prueba la visualización de diferentes estados"""
    states = ['active', 'pending', 'completed', 'cancelled']
    for status in states:
        sample_activity['status'] = status
        item = ActivityListItem(sample_activity)
        assert status.capitalize() in item.text()

def test_activity_list_item_participants_display(sample_activity):
    """Prueba la visualización del contador de participantes"""
    item = ActivityListItem(sample_activity)
    assert '3/10' in item.text()  # "3" participantes de "10" máximo

def test_activity_list_item_survey_indicator(sample_activity):
    """Prueba los indicadores de encuestas"""
    # Prueba con encuestas pendientes
    sample_activity['surveys_ready'] = False
    item = ActivityListItem(sample_activity)
    assert '🔴' in item.text()
    
    # Prueba con encuestas completadas
    sample_activity['surveys_ready'] = True
    item = ActivityListItem(sample_activity)
    assert '✅' in item.text()

@pytest.mark.usefixtures('qapp')
def test_activity_list_item_tooltip(sample_activity):
    """Prueba que el tooltip se genera correctamente"""
    item = ActivityListItem(sample_activity)
    tooltip = item.toolTip()
    
    assert sample_activity['name'] in tooltip
    assert sample_activity['location'] in tooltip
    assert 'Participantes:</b> 3 de 10' in tooltip  # Cambiar esta línea
    assert 'Encuestas:</b> Pendientes' in tooltip  # Y esta línea

@pytest.mark.usefixtures('qapp')
def test_context_menu_creation(sample_activity):
    """Prueba la creación del menú contextual"""
    item = ActivityListItem(sample_activity)
    menu = item.get_context_menu()
    
    actions = [action.text() for action in menu.actions() if action.text()]  # Ignorar separadores
    assert "✏️ Editar" in actions
    assert "🗑️ Eliminar" in actions


@pytest.mark.usefixtures('qapp')
def test_context_menu_status_specific_actions(sample_activity):
    """Prueba que el menú contextual muestra acciones específicas según el estado"""
    # Probar con estado activo
    sample_activity['status'] = 'active'
    item = ActivityListItem(sample_activity)
    menu = item.get_context_menu()
    actions = [action.text() for action in menu.actions() if action.text()]
    assert "✅ Marcar como completada" in actions
    
    # Probar con estado pendiente
    sample_activity['status'] = 'pending'
    item = ActivityListItem(sample_activity)
    menu = item.get_context_menu()
    actions = [action.text() for action in menu.actions() if action.text()]
    assert "▶️ Activar" in actions


@pytest.mark.usefixtures('qapp')
def test_context_menu_survey_actions(sample_activity):
    """Prueba las acciones relacionadas con encuestas en el menú contextual"""
    # Probar con encuestas pendientes
    sample_activity['surveys_ready'] = False
    item = ActivityListItem(sample_activity)
    menu = item.get_context_menu()
    actions = [action.text() for action in menu.actions() if action.text()]
    assert "📝 Generar encuestas" in actions
    
    # Probar con encuestas listas
    sample_activity['surveys_ready'] = True
    item = ActivityListItem(sample_activity)
    menu = item.get_context_menu()
    actions = [action.text() for action in menu.actions() if action.text()]
    assert "📊 Procesar encuestas" in actions

@pytest.mark.usefixtures('qapp')
def test_item_appearance_with_long_text(sample_activity):
    """Prueba que el item maneja correctamente textos largos"""
    sample_activity['name'] = 'Un nombre muy largo para probar el comportamiento ' * 3
    sample_activity['location'] = 'Una ubicación muy larga para probar ' * 3
    
    item = ActivityListItem(sample_activity)
    # Verificar que el tamaño del item es razonable
    size_hint = item.sizeHint()
    assert size_hint.height() >= 90  # Altura mínima esperada