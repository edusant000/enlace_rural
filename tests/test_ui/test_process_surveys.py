# tests/test_ui/test_process_surveys.py

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from unittest.mock import Mock, AsyncMock, patch
import os
from pathlib import Path
from src.ui.dialogs.process_surveys_dialog import ProcessSurveysDialog
from src.ocr.batch_processor import BatchProcessor
from src.ocr.preprocessor import Preprocessor
from src.ui.views.image_management_view import ImageManagementView

@pytest.fixture
def app():
    """Crear una aplicación Qt para los tests"""
    return QApplication([])

@pytest.fixture
def mock_batch_processor():
    """Mock del procesador OCR"""
    processor = Mock(spec=BatchProcessor)
    processor.process_image = AsyncMock(return_value={
        "participant_id": "test_id",
        "responses": {"Q1": "X", "Q2": "X"},
        "confidence": 0.95
    })
    return processor

@pytest.fixture
def mock_preprocessor():
    """Mock del preprocesador de imágenes"""
    preprocessor = Mock(spec=Preprocessor)
    preprocessor.preprocess_image = AsyncMock(return_value="processed_image_data")
    return preprocessor

@pytest.fixture
def sample_images(tmp_path):
    import numpy as np
    import cv2
    
    image_paths = []
    for i in range(3):
        img_path = tmp_path / f"test_survey_{i}.png"
        dummy_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        cv2.imwrite(str(img_path), dummy_image)
        image_paths.append(str(img_path))
    return image_paths

@pytest.fixture
def process_dialog(qapp, mock_batch_processor, mock_preprocessor):
    dialog = ProcessSurveysDialog("test_activity_id")
    dialog.batch_processor = mock_batch_processor
    dialog.preprocessor = mock_preprocessor
    return dialog

@pytest.mark.asyncio
async def test_process_surveys_dialog_init(process_dialog):
    assert process_dialog.activity_id == "test_activity_id"
    assert isinstance(process_dialog.image_view, ImageManagementView)
    assert not process_dialog.save_btn.isEnabled()


@pytest.mark.asyncio
async def test_save_results(process_dialog):
    process_dialog.ocr_results = [
        {"participant_id": "1", "responses": {"Q1": "X"}},
        {"participant_id": "2", "responses": {"Q1": "X"}}
    ]
    
    results_spy = []
    process_dialog.surveys_processed.connect(lambda x: results_spy.extend(x))
    await process_dialog.save_results()
    assert len(results_spy) == len(process_dialog.ocr_results)

@pytest.mark.asyncio
async def test_show_process_surveys_dialog(mock_activity_view, mock_process_dialog):
    """Probar la apertura del diálogo de procesamiento"""
    with patch.object(mock_activity_view, 'show_process_surveys_dialog', AsyncMock()) as mock_show:
        await mock_activity_view.show_process_surveys_dialog()
        mock_show.assert_called_once()

@pytest.mark.asyncio
async def test_on_surveys_processed(mock_activity_view, mock_process_result):
    """Probar el manejo de resultados del procesamiento"""
    mock_activity_view.current_activity_id = "test_id"
    
    # Configurar el valor de retorno específico para esta prueba
    mock_activity_view.data_manager.get_activity.return_value = {
        'id': 'test_id',
        'name': 'Test Activity',
        'participants': []
    }
    
    await mock_activity_view.on_surveys_processed(mock_process_result)
    
    # Verificar que se llamó correctamente
    mock_activity_view.data_manager.get_activity.assert_called_once_with("test_id")

@pytest.mark.asyncio
async def test_process_surveys_integration(
    mock_activity_view,
    mock_process_dialog,
    mock_process_result
):
    """Probar la integración completa del procesamiento de encuestas"""
    mock_activity_view.current_activity_id = "test_id"
    
    # Configurar el valor de retorno para esta prueba
    mock_activity_view.data_manager.get_activity.return_value = {
        'id': 'test_id',
        'name': 'Test Activity',
        'participants': []
    }
    
    # Simular procesamiento completo
    with patch.object(mock_activity_view, 'show_process_surveys_dialog', AsyncMock()) as mock_show:
        await mock_activity_view.show_process_surveys_dialog()
        await mock_activity_view.on_surveys_processed(mock_process_result)
        
        # Verificar la integración
        mock_show.assert_called_once()
        mock_activity_view.data_manager.get_activity.assert_called_once_with("test_id")
    
@pytest.mark.asyncio
async def test_process_results(process_dialog, sample_images, mock_batch_processor):
    """Probar el procesamiento y guardado de resultados"""
    sample_result = {
        "participant_id": "test_id",
        "responses": {"Q1": "X", "Q2": "X"},
        "confidence": 0.95
    }
    
    # Configurar el mock
    mock_batch_processor.process_image.return_value = sample_result
    process_dialog.image_view.batch_processor = mock_batch_processor
    process_dialog.image_view.image_paths = [sample_images[0]]
    
    # Simular procesamiento
    results_spy = []
    process_dialog.surveys_processed.connect(lambda x: results_spy.extend(x))
    
    # Emitir señal de procesamiento completado
    process_dialog.image_view.processing_complete.emit({str(sample_images[0]): sample_result})
    
    assert process_dialog.save_btn.isEnabled()
    
    # Guardar resultados
    await process_dialog.save_results()
    assert len(results_spy) == 1
    assert results_spy[0]["participant_id"] == "test_id"

@pytest.mark.asyncio
async def test_handle_processing_complete(process_dialog):
    test_results = {
        "img1.png": {
            "participant_id": "1",
            "responses": {"Q1": "X"},
            "confidence": 0.95
        }
    }
    process_dialog.handle_processing_complete(test_results)
    assert len(process_dialog.ocr_results) == 1
    assert process_dialog.save_btn.isEnabled()