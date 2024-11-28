import asyncio
import logging
from pathlib import Path
import sys

# Añadir el directorio raíz al PATH para poder importar los módulos
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.append(str(root_dir))

from src.database.db_manager import DatabaseManager
from src.utils.test_data.generator import TestDataGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def populate_database():
    """Popula la base de datos con datos de prueba."""
    db_manager = DatabaseManager(
        host="localhost",
        port=27017,
        username="root",
        password="example"
    )
    
    try:
        # Generar datos
        generator = TestDataGenerator()
        data = generator.generate_all()
        
        # Limpiar colecciones existentes
        collections = ["activities", "participants", "survey_results"]
        for collection in collections:
            try:
                db_manager.db[collection].drop()
                logger.info(f"Colección {collection} limpiada")
            except Exception as e:
                logger.error(f"Error al limpiar colección {collection}: {e}")
        
        # Insertar nuevos datos
        for activity in data["activities"]:
            db_manager.insert_one("activities", activity)
        
        for participant in data["participants"]:
            db_manager.insert_one("participants", participant)
        
        for result in data["survey_results"]:
            db_manager.insert_one("survey_results", result)
        
        logger.info(f"""
        Datos insertados exitosamente:
        - {len(data['activities'])} actividades
        - {len(data['participants'])} participantes
        - {len(data['survey_results'])} resultados de encuestas
        """)
        
        # Verificar los datos insertados
        activities_count = db_manager.count_documents("activities", {})
        participants_count = db_manager.count_documents("participants", {})
        results_count = db_manager.count_documents("survey_results", {})
        
        logger.info(f"""
        Verificación de datos en la base de datos:
        - Actividades: {activities_count}
        - Participantes: {participants_count}
        - Resultados de encuestas: {results_count}
        """)
        
    except Exception as e:
        logger.error(f"Error al poblar la base de datos: {e}")
        raise
    finally:
        del db_manager

if __name__ == "__main__":
    populate_database()