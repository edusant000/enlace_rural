import logging
from typing import Optional, Dict, List, Any, Union, Tuple
from pymongo import MongoClient, ASCENDING, DESCENDING, IndexModel
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure, AutoReconnect, DuplicateKeyError
from bson.objectid import ObjectId
from functools import wraps
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Excepción base para errores de base de datos."""
    pass

class ConnectionError(DatabaseError):
    """Error de conexión a la base de datos."""
    pass

class OperationError(DatabaseError):
    """Error en operaciones de la base de datos."""
    pass

def retry_on_disconnect(max_retries=3, delay=1):
    """
    Decorador mejorado para reintentar operaciones en caso de desconexión.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except AutoReconnect as e:
                    logger.warning(
                        f"Intento {attempt + 1}/{max_retries} fallido para {func.__name__}"
                    )
                    
                    if attempt == max_retries - 1:
                        logger.error(
                            f"Máximo de reintentos alcanzado para {func.__name__}"
                        )
                        raise ConnectionError(
                            f"No se pudo reconectar después de {max_retries} intentos"
                        ) from e
                    
                    wait_time = delay * (2 ** attempt)
                    logger.info(f"Esperando {wait_time} segundos antes del siguiente intento")
                    time.sleep(wait_time)
                except OperationFailure as e:
                    logger.error(f"Error de operación en {func.__name__}: {str(e)}")
                    raise OperationError(f"Error de operación: {str(e)}")
            
            raise ConnectionError(f"Error inesperado en reintentos de {func.__name__}")
            
        return wrapper
    return decorator

class DatabaseManager:
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 27017,
                 username: str = "root",
                 password: str = "example",
                 database: str = "enlace_rural",
                 max_pool_size: int = 50,
                 client=None):
        """
        Inicializa la conexión con MongoDB o utiliza un cliente proporcionado.
        """
        self.host = host
        self.port = port
        self.database = database
        
        if client:
            self.client = client
            self.db = self.client[database]
            logger.info("Usando cliente MongoDB proporcionado")
        else:
            self._connect(username, password, max_pool_size)
            
            # Validar conexión inicial solo si no es un cliente mockeado
            try:
                self.client.server_info()
                logger.info("Conexión inicial establecida exitosamente")
            except Exception as e:
                logger.error(f"Error en la conexión inicial: {str(e)}")
                raise ConnectionError(f"No se pudo establecer conexión inicial: {str(e)}")

    def _connect(self, username: str, password: str, max_pool_size: int):
        """
        Establece la conexión con MongoDB.
        """
        try:
            uri = f"mongodb://{username}:{password}@{self.host}:{self.port}/"
            self.client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=max_pool_size,
                waitQueueTimeoutMS=2500,
                connectTimeoutMS=2000,
                retryWrites=True,
                retryReads=True
            )
            self.db = self.client[self.database]
            
            # Verificar la conexión antes de crear índices
            self.client.server_info()
            self._ensure_indexes()
            logger.info(f"Conexión a MongoDB establecida en {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Error al conectar con MongoDB: {str(e)}")
            raise ConnectionError(f"No se pudo conectar a MongoDB: {str(e)}")

    def _ensure_indexes(self):
        """
        Asegura que existan los índices necesarios en las colecciones.
        """
        try:
            # Índices para activities
            if 'activities' in self.db.list_collection_names():
                self.db.activities.create_indexes([
                    IndexModel([('id', ASCENDING)], unique=True),
                    IndexModel([('coordinator_id', ASCENDING)]),
                    IndexModel([('status', ASCENDING)]),
                    IndexModel([('created_at', ASCENDING)]),
                    IndexModel([('updated_at', ASCENDING)])
                ])
            
            # Índices para participants
            if 'participants' in self.db.list_collection_names():
                self.db.participants.create_indexes([
                    IndexModel([('id', ASCENDING)], unique=True),
                    IndexModel([('community', ASCENDING)]),
                    IndexModel([('name', ASCENDING)]),
                    IndexModel([('created_at', ASCENDING)])
                ])
            
            # Índices para surveys
            if 'surveys' in self.db.list_collection_names():
                self.db.surveys.create_indexes([
                    IndexModel([('participant_id', ASCENDING)]),
                    IndexModel([('activity_id', ASCENDING)]),
                    IndexModel([('date', ASCENDING)])
                ])
            
            logger.info("Índices verificados/creados exitosamente")
            
        except Exception as e:
            logger.error(f"Error al crear índices: {str(e)}")
            raise OperationError(f"Error al crear índices: {str(e)}")

    @retry_on_disconnect()
    def insert_one(self, collection: str, document: Dict) -> Optional[str]:
        """
        Inserta un documento en la colección especificada.
        """
        try:
            if not isinstance(document, dict):
                raise OperationError("El documento debe ser un diccionario")
                
            if 'created_at' not in document:
                document['created_at'] = datetime.now(timezone.utc)
            if 'updated_at' not in document:
                document['updated_at'] = document['created_at']
                
            result = self.db[collection].insert_one(document)
            logger.info(f"Documento insertado exitosamente en {collection}")
            return str(result.inserted_id)
            
        except (AutoReconnect, OperationFailure) as e:
            # Re-levantar para que lo maneje el decorador
            raise
        except DuplicateKeyError as e:
            logger.error(f"Error de duplicado al insertar en {collection}: {str(e)}")
            raise OperationError(f"Documento duplicado: {str(e)}")
        except Exception as e:
            logger.error(f"Error al insertar documento en {collection}: {str(e)}")
            raise OperationError(f"Error al insertar documento: {str(e)}")

    def __del__(self):
        """Cierra la conexión cuando el objeto es destruido."""
        try:
            if hasattr(self, 'client'):
                self.client.close()
                logger.info("Conexión a MongoDB cerrada")
        except Exception as e:
            logger.error(f"Error al cerrar conexión: {str(e)}")