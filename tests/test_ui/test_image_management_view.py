import numpy as np
import pytest
from PyQt6.QtCore import Qt
from unittest.mock import Mock, AsyncMock, patch
from src.ui.views.image_management_view import ImageManagementView, ImageProcessingThread
import asyncio

@pytest.fixture
def image_view(qapp, mock_batch_processor):
    view = ImageManagementView()
    view.batch_processor = mock_batch_processor
    return view

@pytest.fixture
def mock_batch_processor():
    processor = Mock()
    processor.process_image.return_value = {
        "participant_id": "test_id",
        "responses": {"Q1": "X", "Q2": ""},
        "confidence": 0.95,
        "processed_at": "2024-01-01T00:00:00"
    }
    return processor

@pytest.fixture
def sample_images(tmp_path):
    """Crear imágenes de prueba temporales"""
    import numpy as np
    import cv2
    
    image_paths = []
    for i in range(3):
        img_path = tmp_path / f"test_survey_{i}.png"
        # Crear imagen dummy
        dummy_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        cv2.imwrite(str(img_path), dummy_image)
        image_paths.append(str(img_path))
    return image_paths

@pytest.fixture
def sample_result():
    return {
        "participant_id": "test_id",
        "responses": {"Q1": "X", "Q2": ""},
        "confidence": 0.95,
        "processed_at": "2024-01-01T00:00:00"
    }

@pytest.mark.asyncio
async def test_image_management_view_init(image_view):
    assert len(image_view.image_paths) == 0
    assert image_view.current_image_index == 0
    assert not image_view.process_btn.isEnabled()

@pytest.mark.asyncio
async def test_select_images(image_view, sample_images):
    with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames', 
              return_value=(sample_images, '')):
        image_view.select_images()
    
    assert len(image_view.image_paths) == len(sample_images)
    assert image_view.process_btn.isEnabled()
    assert image_view.current_image_index == 0

@pytest.mark.asyncio
async def test_process_images(image_view, sample_images, sample_result):
    image_view.image_paths = [sample_images[0]]
    completed_results = []
    image_view.processing_complete.connect(lambda x: completed_results.append(x))

    # Parchear el método 'start' para evitar que el hilo se inicie
    with patch.object(ImageProcessingThread, 'start', return_value=None):
        image_view.process_images()
        # Emitir manualmente la señal 'finished'
        image_view.processing_thread.finished.emit({str(sample_images[0]): sample_result})

    assert len(completed_results) == 1
    assert completed_results[0][str(sample_images[0])] == sample_result


@pytest.mark.asyncio
async def test_navigation(image_view, sample_images):
    image_view.image_paths = sample_images
    image_view.update_navigation_buttons()  # Añadir esta línea

    
    assert not image_view.prev_btn.isEnabled()
    assert image_view.next_btn.isEnabled()
    
    image_view.show_next_image()
    assert image_view.current_image_index == 1
    assert image_view.prev_btn.isEnabled()
    
    image_view.show_previous_image()
    assert image_view.current_image_index == 0
    assert not image_view.prev_btn.isEnabled()

@pytest.mark.asyncio
async def test_handle_processing_error(image_view):
    with patch('PyQt6.QtWidgets.QMessageBox.critical') as mock_critical:
        image_view.handle_processing_error("Test error")
        mock_critical.assert_called_once()
    assert image_view.process_btn.isEnabled()
    assert not image_view.progress_bar.isVisible()

@pytest.mark.asyncio
async def test_update_ocr_preview(image_view, sample_images, sample_result):
    image_view.image_paths = sample_images
    image_view.processed_results = {str(sample_images[0]): sample_result}
    
    image_view.update_ocr_preview()
    
    preview_text = image_view.ocr_preview.text()
    assert "test_id" in preview_text
    assert "95.00%" in preview_text  

@pytest.mark.asyncio
async def test_show_current_image_with_preprocessing(image_view, sample_images):
    image_view.image_paths = sample_images
    
    # Mock el preprocesador
    with patch.object(image_view.image_preprocessor, 'preprocess_image') as mock_preprocess:
        mock_preprocess.return_value = np.ones((100, 100), dtype=np.uint8) * 255
        image_view.show_current_image()
        
    assert mock_preprocess.called
    assert image_view.image_label.pixmap() is not None

@pytest.mark.asyncio
async def test_handle_result(image_view, sample_images, sample_result):
    image_view.image_paths = sample_images
    
    image_view.handle_result(str(sample_images[0]), sample_result)
    assert str(sample_images[0]) in image_view.processed_results
    
    # Verificar actualización de preview cuando es la imagen actual
    preview_text = image_view.ocr_preview.text()
    assert "test_id" in preview_text

@pytest.mark.asyncio
async def test_processing_progress(image_view, sample_images, qtbot):
    image_view.image_paths = sample_images
    image_view.show()  # Mostrar el widget
    
    with patch.object(ImageProcessingThread, 'start'):
        image_view.process_images()
        image_view.processing_thread.progress.emit(50)
        assert image_view.progress_bar.value() == 50
        assert image_view.progress_bar.isVisible()