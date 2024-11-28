# tests/test_ui/test_participant_list_view.py

import os
import pytest
from PyQt6.QtWidgets import QApplication, QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt
from src.ui.dialogs.reports_dialog import ReportsDialog
from src.ui.views.participant_list_view import ParticipantListView
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from datetime import datetime, timedelta

# Fixture para la aplicación Qt
@pytest.fixture(scope="module")
def app():
    app = QApplication([])
    yield app
    app.quit()

# Fixture para el data_manager mockeado
@pytest.fixture
def mock_data_manager():
    manager = Mock()
    # Usar AsyncMock para métodos asíncronos
    manager.get_all_participants = AsyncMock()
    manager.get_all_participants.return_value = [
        {
            'id': '1',
            'name': 'Juan Pérez',
            'community': 'Comunidad 1',
            'birth_date': '01/01/1990',
            'gender': 'Hombre',
            'education_level': 'Preparatoria',
            'status': 'Activo'
        },
        {
            'id': '2',
            'name': 'María García',
            'community': 'Comunidad 2',
            'birth_date': '15/05/1985',
            'gender': 'Mujer',
            'education_level': 'Universidad',
            'status': 'Activo'
        }
    ]
    return manager

@pytest.mark.asyncio
async def test_load_participants(participant_view, mock_data_manager):
    """Prueba la carga inicial de participantes"""
    # Asegurarnos de que el método retorne una lista válida
    mock_data_manager.get_all_participants.return_value = [
        {
            'id': '1',
            'name': 'Juan Pérez',
            'community': 'Comunidad 1',
            'birth_date': '01/01/1990',
            'gender': 'Hombre',
            'education_level': 'Preparatoria',
            'status': 'Activo'
        },
        {
            'id': '2',
            'name': 'María García',
            'community': 'Comunidad 2',
            'birth_date': '15/05/1985',
            'gender': 'Mujer',
            'education_level': 'Universidad',
            'status': 'Activo'
        }
    ]
    
    await participant_view.load_participants()
    
    # Verificar que se llamó al data_manager
    mock_data_manager.get_all_participants.assert_called_once()
    
    # Verificar que se agregaron los participantes a la tabla
    assert participant_view.participants_table.rowCount() == 2
    
    # Verificar los datos del primer participante
    assert participant_view.participants_table.item(0, 1).text() == 'Juan Pérez'
    assert participant_view.participants_table.item(0, 2).text() == 'Comunidad 1'

def test_filter_participants(participant_view):
    participant_view.participants_table.setRowCount(2)
    for col in range(7):
        participant_view.participants_table.setItem(0, col, QTableWidgetItem(""))
        participant_view.participants_table.setItem(1, col, QTableWidgetItem(""))
    
    participant_view.participants_table.setItem(0, 1, QTableWidgetItem("Juan Pérez"))
    participant_view.participants_table.setItem(0, 2, QTableWidgetItem("Comunidad 1"))
    participant_view.participants_table.setItem(1, 1, QTableWidgetItem("María García"))
    participant_view.participants_table.setItem(1, 2, QTableWidgetItem("Comunidad 2"))
    
    filters = {
        'name': 'Juan',
        'community': 'Todas las comunidades',
        'age_range': 'Todas las edades',
        'gender': 'Todos',
        'education': 'Todos'
    }
    
    participant_view.filter_view.filtersChanged.emit(filters)

@pytest.mark.asyncio
async def test_remove_participant(participant_view, mock_data_manager, monkeypatch):
    """Prueba la eliminación de un participante"""
    # Simular la selección de una fila
    participant_view.participants_table.setRowCount(1)
    participant_view.participants_table.setItem(0, 0, QTableWidgetItem("1"))
    participant_view.participants_table.setItem(0, 1, QTableWidgetItem("Juan Pérez"))
    participant_view.participants_table.selectRow(0)
    
    # Mockear QMessageBox para simular que el usuario confirma la eliminación
    with patch('PyQt6.QtWidgets.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes):
        await participant_view.remove_participant()
    
    # Verificar que se llamó al data_manager
    mock_data_manager.delete_participant.assert_called_once_with("1")

@pytest.mark.asyncio
async def test_export_buttons(app, mock_data_manager):
    """Test de botones de exportación"""
    view = ParticipantListView(mock_data_manager)
    
    # Verificar que los botones existen
    assert view.export_csv_button is not None
    assert view.export_excel_button is not None
    assert view.export_pdf_button is not None
    assert view.view_reports_button is not None
    
    # Verificar que están conectados
    assert view.export_csv_button.receivers(view.export_csv_button.clicked) > 0
    assert view.export_excel_button.receivers(view.export_excel_button.clicked) > 0
    assert view.export_pdf_button.receivers(view.export_pdf_button.clicked) > 0
    assert view.view_reports_button.receivers(view.view_reports_button.clicked) > 0

@pytest.mark.asyncio
async def test_show_reports_dialog(participant_view, monkeypatch):
    """Test de apertura del diálogo de reportes"""
    dialog_shown = False
    
    class MockReportsDialog:
        def __init__(self, data_manager, parent=None):
            nonlocal dialog_shown
            dialog_shown = True
            self.data_manager = data_manager
            self.parent = parent
    
        async def load_initial_data(self):
            return
    
        def exec(self):
            return True
    
    # Obtener el módulo donde ParticipantListView importa ReportsDialog
    import sys
    module_path = 'src.ui.views.participant_list_view'
    if module_path in sys.modules:
        # Si el módulo ya está importado, necesitamos patchear donde se usa
        with patch.object(sys.modules[module_path], 'ReportsDialog', MockReportsDialog):
            await participant_view.show_reports()
            await asyncio.sleep(0.1)
            assert dialog_shown, "El diálogo de reportes no se mostró"
    else:
        # Si el módulo no está importado, usamos el path directo
        with patch('src.ui.views.participant_list_view.ReportsDialog', MockReportsDialog):
            await participant_view.show_reports()
            await asyncio.sleep(0.1)
            assert dialog_shown, "El diálogo de reportes no se mostró"

@pytest.fixture
def participant_view(app, mock_data_manager):
    """Fixture que proporciona una instancia de ParticipantListView"""
    view = ParticipantListView(mock_data_manager)
    return view

@pytest.mark.asyncio
async def test_export_csv_functionality(participant_view, tmp_path, monkeypatch):
    """Test de funcionalidad de exportación a CSV"""
    filename = tmp_path / "test_export.csv"
    
    # Modificar para usar patch en lugar de setattr
    with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', 
              return_value=(str(filename), "CSV Files (*.csv)")):
        await participant_view.export_to_csv()
    
    await asyncio.sleep(0.1)  # Dar tiempo para el procesamiento
    assert os.path.exists(filename)


@pytest.mark.asyncio
async def test_export_excel_functionality(participant_view, tmp_path):
    """Test de funcionalidad de exportación a Excel"""
    filename = tmp_path / "test_export.xlsx"
    with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', 
              return_value=(str(filename), "Excel Files (*.xlsx)")):
        await participant_view.export_to_excel()
    
    assert os.path.exists(filename)
    assert os.path.getsize(filename) > 0

@pytest.mark.asyncio
async def test_export_pdf_functionality(participant_view, tmp_path, mock_data_manager):
    """Test de funcionalidad de exportación a PDF"""
    filename = tmp_path / "test_export.pdf"
    
    # Configurar datos de prueba con el formato correcto
    test_data = [{
        'id': '1',
        'name': 'Test User',
        'community': 'Test Community',
        'birth_date': '2000-01-01',
        'gender': 'M',
        'education_level': 'High School',
        'status': 'Active',
        'activities': ['Activity 1'],
        'Actividad': 'Test Activity'  # Añadir este campo
    }]
    
    # Configurar los mocks necesarios
    mock_data_manager.get_activity_participants.return_value = test_data
    mock_data_manager.get_all_participants.return_value = test_data
    
    with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName',
              return_value=(str(filename), "PDF Files (*.pdf)")):
        await participant_view.export_to_pdf()
    
    await asyncio.sleep(0.1)
    assert os.path.exists(filename)

@pytest.mark.asyncio
async def test_export_error_handling(participant_view):
    """Test de manejo de errores en exportación"""
    with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', 
              return_value=("", "")):  # Usuario cancela
        await participant_view.export_to_csv()
        # Verificar que no hay error cuando se cancela

    with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', 
              return_value=("/ruta/invalida/archivo.csv", "CSV Files (*.csv)")):
        with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
            await participant_view.export_to_csv()
            mock_warning.assert_called_once()  # Verificar que se mostró advertencia


@pytest.fixture
def sample_data():
    return [
        {
            'id': '1',
            'name': 'Juan Pérez',
            'community': 'Comunidad A',
            'birth_date': '1990-01-01',
            'gender': 'Masculino',
            'education_level': 'Universidad'
        },
        {
            'id': '2',
            'name': 'María García',
            'community': 'Comunidad B',
            'birth_date': '1995-06-15',
            'gender': 'Femenino',
            'education_level': 'Preparatoria'
        }
    ]


@pytest.mark.asyncio
async def test_filter_by_name(qtbot, sample_data):
    view = ParticipantListView(None)
    qtbot.addWidget(view)
    view.update_table(sample_data)  # Quitar await
    
    filters = {
        'name': 'Juan',
        'community': 'Todas las comunidades',
        'age_range': 'Todas las edades',
        'gender': 'Todos',
        'education': 'Todos'
    }
    await view.apply_filters(filters)


@pytest.mark.asyncio
async def test_filter_by_community(qtbot, sample_data):
    view = ParticipantListView(None)
    qtbot.addWidget(view)
    view.update_table(sample_data)  # Quitar await
    
    filters = {
        'name': '',
        'community': 'Comunidad A',
        'age_range': 'Todas las edades',
        'gender': 'Todos',
        'education': 'Todos'
    }
    
    await view.apply_filters(filters)
    visible_rows = [i for i in range(view.participants_table.rowCount()) 
                   if not view.participants_table.isRowHidden(i)]
    assert len(visible_rows) == 1
    assert view.participants_table.item(visible_rows[0], 2).text() == 'Comunidad A'



@pytest.mark.asyncio
async def test_multiple_filters(qtbot, sample_data):
    view = ParticipantListView(None)
    qtbot.addWidget(view)
    view.update_table(sample_data)  # Quitar await
    
    filters = {
        'name': 'María',
        'community': 'Comunidad B',
        'age_range': '26-35',
        'gender': 'Femenino',
        'education': 'Preparatoria'
    }
    
    await view.apply_filters(filters)
    visible_rows = [i for i in range(view.participants_table.rowCount()) 
                   if not view.participants_table.isRowHidden(i)]
    assert len(visible_rows) == 1
    assert view.participants_table.item(visible_rows[0], 1).text() == 'María García'