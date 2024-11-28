import pytest
import cv2
import numpy as np
from pathlib import Path
from src.ocr.batch_processor import SimpleBatchProcessor
from src.ocr.preprocessor import ImagePreprocessor
# Mantener los imports existentes y añadir:
from src.ocr.batch_processor import BatchProcessor
import asyncio
import pytesseract
import logging
logger = logging.getLogger(__name__)


# Configurar Tesseract (agregar después de los imports)
tessdata_dir_config = r'--tessdata-dir "/opt/homebrew/share/tessdata"'  # Ajusta esta ruta según tu sistema
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'  

@pytest.fixture
def batch_processor():
    return BatchProcessor()

@pytest.fixture
def sample_image():
    base_path = "/Users/edusant/Desktop/Itam/noveno_semestre/CDA/proyecto_ver_2/enlace_rural/tests/test_images/surveys/test_survey.png"
    image_path = Path(base_path)
    logger.warning(f"Usando imagen de prueba: {image_path}")
    if not image_path.exists():
        raise FileNotFoundError(f"Imagen no encontrada: {image_path}")
    return str(image_path)

@pytest.mark.asyncio
async def test_process_single_image(batch_processor, sample_image):
    """Test del procesamiento de una sola imagen."""
    result = await batch_processor.process_image(sample_image)
    
    assert isinstance(result, dict)
    assert "participant_id" in result
    assert "responses" in result
    assert "confidence" in result
    assert "processed_at" in result



def test_extract_participant_id(batch_processor, sample_image):
    processed_image = batch_processor.preprocessor.preprocess_image(sample_image)
    participant_id = batch_processor._extract_participant_id(processed_image)
    assert participant_id == "12345"

def test_process_responses(batch_processor, sample_image):
    processed_image = batch_processor.preprocessor.preprocess_image(sample_image)
    responses = batch_processor._process_responses(processed_image)
    assert isinstance(responses, dict)
    assert len(responses) > 0




def test_calculate_confidence(batch_processor):
    test_cases = [
        ({"Q1": "X", "Q2": "X"}, 1.0),
        ({"Q1": "X", "Q2": ""}, 0.5),
        ({}, 0.0),
        ({"Q1": "", "Q2": ""}, 0.0)
    ]
    
    for responses, expected in test_cases:
        confidence = batch_processor._calculate_confidence(responses)
        assert abs(confidence - expected) < 0.01

def test_error_handling(batch_processor, tmp_path):
    nonexistent = tmp_path / "nonexistent.png"
    with pytest.raises(FileNotFoundError):
        batch_processor.process_image(str(nonexistent))

@pytest.fixture
def sample_batch_dir(tmp_path):
    """Utiliza los archivos de prueba existentes en test_images/batch_input."""
    source_dir = Path(__file__).parent / "test_images" / "batch_input"
    batch_dir = tmp_path / "batch_input"
    
    # Copiar los archivos de prueba al directorio temporal
    batch_dir.mkdir(parents=True)
    for file in source_dir.glob("*"):
        if file.is_file():
            import shutil
            shutil.copy2(str(file), str(batch_dir / file.name))
    
    return batch_dir

def test_batch_processor_initialization(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()  # Crear el directorio de entrada
    
    processor = SimpleBatchProcessor(str(input_dir), str(output_dir))
    assert processor.input_dir == input_dir
    assert processor.output_dir == output_dir
    
def test_process_directory(sample_batch_dir, tmp_path):
    output_dir = tmp_path / "output"
    processor = SimpleBatchProcessor(str(sample_batch_dir), str(output_dir))
    results = processor.process_directory()
    
    assert results['successful'] >= 0
    assert isinstance(results['processed_images'], list)
    
def test_empty_directory(tmp_path):
    input_dir = tmp_path / "empty"
    input_dir.mkdir()
    output_dir = tmp_path / "output"
    
    processor = SimpleBatchProcessor(str(input_dir), str(output_dir))
    results = processor.process_directory()
    
    assert results == {}
    
def test_parallel_processing(sample_batch_dir, tmp_path):
    output_dir = tmp_path / "output"
    processor = SimpleBatchProcessor(str(sample_batch_dir), str(output_dir))
    results = processor.process_directory(parallel=True)
    
    assert results['successful'] >= 0
    assert isinstance(results['processed_images'], list)
    
def test_invalid_input_directory(tmp_path):
    nonexistent = tmp_path / "nonexistent"
    output_dir = tmp_path / "output"
    
    with pytest.raises((FileNotFoundError, NotADirectoryError)):
        SimpleBatchProcessor(str(nonexistent), str(output_dir))

def test_processing_stats(sample_batch_dir, tmp_path):
    output_dir = tmp_path / "output"
    processor = SimpleBatchProcessor(str(sample_batch_dir), str(output_dir))
    processor.process_directory()
    
    stats = processor.get_processing_stats()
    assert isinstance(stats, dict)
    assert 'total_processed' in stats
    assert 'total_files' in stats