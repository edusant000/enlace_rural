import pytest
import os
import logging
import mongomock
import pymongo
from pathlib import Path
from typing import Dict, Generator
from src.database.db_manager import DatabaseManager
import cv2
import numpy as np


def pytest_configure(config):
    """Configure pytest."""
    # Registrar marcadores personalizados
    config.addinivalue_line(
        "markers", 
        "asyncio: mark test as an asyncio coroutine"
    )
    config.addinivalue_line(
        "markers", 
        "slow: marca pruebas que son lentas de ejecutar"
    )
    config.addinivalue_line(
        "markers", 
        "integration: marca pruebas de integración"
    )
    
    # Crear directorios necesarios para pruebas
    test_dirs = [
        Path('tests/test_images/output'),
        Path('tests/test_images/temp'),
        Path('tests/test_database/temp')
    ]
    for dir_path in test_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

# Configuración de pytest-asyncio
pytest_plugins = ['pytest_asyncio']

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_environment() -> Dict[str, str]:
    """Fixture para variables de entorno de prueba."""
    return {
        'MONGODB_HOST': os.getenv('MONGODB_HOST', 'localhost'),
        'MONGODB_PORT': os.getenv('MONGODB_PORT', '27017'),
        'MONGODB_USERNAME': os.getenv('MONGODB_USERNAME', 'root'),
        'MONGODB_PASSWORD': os.getenv('MONGODB_PASSWORD', 'example'),
        'TEST_DATABASE': 'test_db'
    }

@pytest.fixture(scope="function")
def mock_db() -> Generator[mongomock.Database, None, None]:
    """
    Fixture que proporciona una base de datos MongoDB simulada para pruebas.
    """
    client = mongomock.MongoClient()
    db = client['test_db']
    
    # Crear colecciones necesarias
    collections = ['activities', 'participants', 'surveys', 'test_collection']
    for collection in collections:
        db.create_collection(collection)
    
    # Crear índices necesarios
    db.activities.create_index([('id', pymongo.ASCENDING)], unique=True)
    db.participants.create_index([('id', pymongo.ASCENDING)], unique=True)
    
    yield db
    
    # Limpiar después de las pruebas
    client.drop_database('test_db')
    client.close()

@pytest.fixture(scope="function")
def db_manager(test_environment) -> Generator[DatabaseManager, None, None]:
    """
    Fixture que proporciona una instancia real de DatabaseManager.
    """
    manager = DatabaseManager(
        host=test_environment['MONGODB_HOST'],
        port=int(test_environment['MONGODB_PORT']),
        username=test_environment['MONGODB_USERNAME'],
        password=test_environment['MONGODB_PASSWORD'],
        database=test_environment['TEST_DATABASE']
    )
    
    yield manager
    
    # Limpiar colecciones después de las pruebas
    collections = ['test_collection', 'activities', 'participants', 'surveys']
    for collection in collections:
        try:
            manager.db[collection].drop()
        except Exception as e:
            logging.warning(f"Error al limpiar colección {collection}: {str(e)}")
    
    manager.client.close()

@pytest.fixture(scope="function")
def test_collection_name() -> str:
    """Fixture para el nombre de la colección de prueba."""
    return "test_collection"

@pytest.fixture(scope="function")
def sample_data() -> Dict:
    """Fixture que proporciona datos de ejemplo para pruebas."""
    return {
        'activities': [
            {
                'id': 'ACT001',
                'coordinator_id': 'COORD001',
                'title': 'Test Activity 1',
                'status': 'active',
                'description': 'Test description 1'
            },
            {
                'id': 'ACT002',
                'coordinator_id': 'COORD001',
                'title': 'Test Activity 2',
                'status': 'pending',
                'description': 'Test description 2'
            }
        ],
        'participants': [
            {
                'id': 'PART001',
                'name': 'Test Participant 1',
                'community': 'Community A',
                'contact': '1234567890'
            },
            {
                'id': 'PART002',
                'name': 'Test Participant 2',
                'community': 'Community B',
                'contact': '0987654321'
            }
        ],
        'surveys': [
            {
                'participant_id': 'PART001',
                'activity_id': 'ACT001',
                'date': '2024-01-01',
                'responses': {'q1': 'r1', 'q2': 'r2'}
            }
        ]
    }

@pytest.fixture(scope="function")
def cleanup_test_files():
    """
    Fixture para limpiar archivos temporales después de las pruebas.
    """
    yield
    
    temp_dirs = [
        Path('tests/test_images/temp'),
        Path('tests/test_database/temp')
    ]
    
    for temp_dir in temp_dirs:
        if temp_dir.exists():
            for file in temp_dir.glob('*'):
                try:
                    if file.is_file():
                        file.unlink()
                except Exception as e:
                    logging.warning(f"Error al eliminar archivo temporal {file}: {str(e)}")

def pytest_addoption(parser):
    """Agregar opciones de línea de comandos personalizadas."""
    parser.addoption(
        "--use-real-db",
        action="store_true",
        default=False,
        help="Usar base de datos real en lugar de mock"
    )
    parser.addoption(
        "--skip-slow",
        action="store_true",
        default=False,
        help="Saltar pruebas lentas"
    )

def pytest_collection_modifyitems(config, items):
    """Modificar colección de pruebas según las opciones."""
    if config.getoption("--skip-slow"):
        skip_slow = pytest.mark.skip(reason="Omitido por --skip-slow")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers",
        "tesseract: mark tests that require tesseract to be installed"
    )


# Nuevos fixtures para OCR testing
@pytest.fixture
def sample_image():
    """
    Crea una imagen de prueba con características específicas para OCR:
    - Texto legible
    - Buen contraste
    - Líneas y formas para pruebas de rotación
    - Tamaño razonable
    - Versión en color (3 canales)
    """
    # Crear una imagen en color (3 canales)
    height, width = 800, 600
    image = np.ones((height, width, 3), dtype=np.uint8) * 255  # Fondo blanco
    
    # Añadir texto negro con buena legibilidad
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(image, "Sample Test", (50, 100), font, 2, (0, 0, 0), 3)
    cv2.putText(image, "OCR Processing", (50, 200), font, 2, (0, 0, 0), 3)
    
    # Añadir algunas formas geométricas para pruebas de rotación y contraste
    # Rectángulo
    cv2.rectangle(image, (50, 300), (200, 400), (0, 0, 0), 2)
    # Líneas horizontales y verticales
    cv2.line(image, (300, 50), (500, 50), (0, 0, 0), 2)  # Horizontal
    cv2.line(image, (300, 50), (300, 200), (0, 0, 0), 2)  # Vertical
    
    # Añadir áreas con diferentes niveles de contraste
    # Gris claro
    cv2.rectangle(image, (400, 300), (500, 400), (200, 200, 200), -1)
    # Gris oscuro
    cv2.rectangle(image, (400, 420), (500, 520), (100, 100, 100), -1)
    
    # Añadir un patrón para pruebas de nitidez
    for i in range(50, 250, 20):
        cv2.line(image, (50, 500 + i//10), (200, 500 + i//10), (0, 0, 0), 1)
    
    return image

@pytest.fixture
def sample_image_path(sample_image, tmp_path):
    """
    Guarda la imagen de prueba en un archivo temporal y retorna su path.
    """
    path = tmp_path / "test_image.png"
    cv2.imwrite(str(path), sample_image)
    return path


@pytest.fixture
def sample_batch_dir(cleanup_test_files):
    """Crea un directorio con múltiples imágenes de prueba."""
    batch_dir = Path('tests/test_images/temp/batch_input')
    batch_dir.mkdir(exist_ok=True)
    
    # Crear varias imágenes de prueba
    image = np.ones((800, 600), dtype=np.uint8) * 255
    cv2.putText(image, "Test Text", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, 0, 2)
    
    for i in range(3):
        path = batch_dir / f"test_image_{i}.png"
        cv2.imwrite(str(path), image)
        
    return batch_dir

@pytest.fixture
def sample_gray_image(sample_image):
    """
    Crea una versión en escala de grises de la imagen de prueba.
    """
    return cv2.cvtColor(sample_image, cv2.COLOR_BGR2GRAY)

@pytest.fixture
def sample_low_quality_image():
    """
    Crea una imagen de baja calidad para pruebas de rechazo y mejora.
    """
    # Crear una imagen borrosa y con bajo contraste
    height, width = 800, 600
    image = np.ones((height, width, 3), dtype=np.uint8) * 200  # Fondo gris claro
    
    # Añadir texto con bajo contraste
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(image, "Low Quality", (50, 100), font, 2, (180, 180, 180), 3)
    
    # Aplicar desenfoque gaussiano
    image = cv2.GaussianBlur(image, (15, 15), 0)
    
    return image

@pytest.fixture
def sample_rotated_image(sample_image):
    """
    Crea una versión rotada de la imagen de prueba.
    """
    height, width = sample_image.shape[:2]
    center = (width // 2, height // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, 15, 1.0)
    rotated = cv2.warpAffine(sample_image, rotation_matrix, (width, height))
    return rotated

@pytest.fixture
def sample_noisy_image(sample_image):
    """
    Crea una versión con ruido de la imagen de prueba.
    """
    noise = np.random.normal(0, 25, sample_image.shape).astype(np.uint8)
    noisy = cv2.add(sample_image, noise)
    return noisy