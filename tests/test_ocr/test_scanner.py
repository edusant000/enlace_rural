import pytest
import numpy as np
import cv2
from pathlib import Path
from src.ocr.scanner import SurveyScanner, SurveyField, ScannerError

@pytest.fixture
def sample_image():
    """Crea una imagen de prueba con texto."""
    image = np.ones((200, 400), dtype=np.uint8) * 255
    cv2.putText(image, "Test Text", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, 0, 2)
    return image

@pytest.fixture
def sample_checkbox_image():
    """Crea una imagen de prueba con checkbox marcado."""
    image = np.ones((200, 100), dtype=np.uint8) * 255
    # Dibujar checkbox marcado
    cv2.rectangle(image, (10, 10), (30, 30), 0, 2)
    cv2.line(image, (10, 10), (30, 30), 0, 2)
    cv2.line(image, (10, 30), (30, 10), 0, 2)
    return image

@pytest.fixture
def sample_scanner():
    """Proporciona una instancia de SurveyScanner."""
    try:
        return SurveyScanner()
    except ScannerError:
        pytest.skip("Tesseract no está correctamente configurado")

@pytest.fixture
def sample_field():
    """Proporciona un campo de prueba."""
    return SurveyField("test_field", (0, 0, 100, 50), "text")

@pytest.fixture
def sample_checkbox_field():
    """Proporciona un campo checkbox de prueba."""
    return SurveyField(
        "checkbox_field",
        (5, 5, 40, 40),
        "checkbox",
        options=["Option 1"]
    )

def test_scanner_initialization():
    """Prueba la inicialización básica del scanner."""
    try:
        scanner = SurveyScanner()
        assert scanner is not None
        assert hasattr(scanner, 'fields')
        assert len(scanner.fields) == 0
    except ScannerError:
        pytest.skip("Tesseract no está correctamente configurado")

def test_register_field(sample_scanner, sample_field):
    """Prueba el registro de un campo."""
    sample_scanner.register_field(sample_field)
    assert len(sample_scanner.fields) == 1
    assert sample_scanner.fields[0].name == "test_field"

def test_register_invalid_field_type(sample_scanner):
    """Prueba el registro de un campo con tipo inválido."""
    with pytest.raises(ValueError):
        invalid_field = SurveyField("test", (0, 0, 100, 50), "invalid_type")
        sample_scanner.register_field(invalid_field)

def test_register_checkbox_without_options(sample_scanner):
    """Prueba el registro de un checkbox sin opciones."""
    with pytest.raises(ValueError):
        invalid_field = SurveyField("test", (0, 0, 100, 50), "checkbox")
        sample_scanner.register_field(invalid_field)

@pytest.mark.tesseract
def test_scan_text_field(sample_scanner, sample_image, sample_field):
    """Prueba el escaneo de un campo de texto."""
    sample_scanner.register_field(sample_field)
    results = sample_scanner.scan_survey(sample_image)
    assert "test_field" in results
    assert isinstance(results["test_field"], str)

@pytest.mark.tesseract
def test_scan_checkbox_field(sample_scanner, sample_checkbox_image, sample_checkbox_field):
    """Prueba el escaneo de un campo checkbox."""
    sample_scanner.register_field(sample_checkbox_field)
    results = sample_scanner.scan_survey(sample_checkbox_image)
    assert "checkbox_field" in results
    assert isinstance(results["checkbox_field"], str)

def test_invalid_template_path():
    """Prueba la carga de un template inexistente."""
    with pytest.raises(FileNotFoundError):
        SurveyScanner("nonexistent_template.png")

def test_scan_invalid_image_path(sample_scanner):
    """Prueba el escaneo de una imagen inexistente."""
    with pytest.raises(ScannerError):
        sample_scanner.scan_survey("nonexistent.png")

def test_multiple_fields(sample_scanner, sample_image):
    """Prueba el escaneo de múltiples campos."""
    fields = [
        SurveyField("field1", (0, 0, 100, 50), "text"),
        SurveyField("field2", (0, 50, 100, 50), "text"),
        SurveyField("field3", (0, 100, 100, 50), "text")
    ]
    for field in fields:
        sample_scanner.register_field(field)
    
    results = sample_scanner.scan_survey(sample_image)
    assert len(results) == 3
    assert all(f"field{i}" in results for i in range(1, 4))

def test_empty_image(sample_scanner, sample_field):
    """Prueba el escaneo de una imagen vacía."""
    empty_image = np.ones((100, 100), dtype=np.uint8) * 255
    sample_scanner.register_field(sample_field)
    results = sample_scanner.scan_survey(empty_image)
    assert results["test_field"] == ""

def test_tesseract_config(sample_scanner):
    """Prueba la configuración de Tesseract."""
    assert hasattr(sample_scanner, 'tesseract_config')
    assert '--tessdata-dir' in sample_scanner.tesseract_config
    assert '--oem 3' in sample_scanner.tesseract_config
    assert '--psm 6' in sample_scanner.tesseract_config

@pytest.mark.tesseract
def test_image_alignment(sample_scanner, sample_image):
    """Prueba la alineación de imágenes."""
    # Rotar la imagen ligeramente
    rows, cols = sample_image.shape
    M = cv2.getRotationMatrix2D((cols/2, rows/2), 5, 1)
    rotated = cv2.warpAffine(sample_image, M, (cols, rows))
    
    field = SurveyField("align_test", (40, 20, 200, 60), "text")
    sample_scanner.register_field(field)
    
    # La alineación debería permitir leer el texto incluso con la rotación
    results = sample_scanner.scan_survey(rotated)
    assert "align_test" in results
    assert isinstance(results["align_test"], str)

@pytest.mark.tesseract
def test_different_image_formats(sample_scanner, tmp_path, sample_image):
    """Prueba el escaneo de diferentes formatos de imagen."""
    field = SurveyField("format_test", (40, 20, 200, 60), "text")
    sample_scanner.register_field(field)
    
    # Guardar y cargar como PNG
    png_path = tmp_path / "test.png"
    cv2.imwrite(str(png_path), sample_image)
    results_png = sample_scanner.scan_survey(str(png_path))
    
    # Guardar y cargar como JPEG
    jpg_path = tmp_path / "test.jpg"
    cv2.imwrite(str(jpg_path), sample_image)
    results_jpg = sample_scanner.scan_survey(str(jpg_path))
    
    assert isinstance(results_png["format_test"], str)
    assert isinstance(results_jpg["format_test"], str)