import pytest
import cv2
import numpy as np
from pathlib import Path
from src.ocr.batch_processor import SimpleBatchProcessor
from src.ocr.preprocessor import ImagePreprocessor

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