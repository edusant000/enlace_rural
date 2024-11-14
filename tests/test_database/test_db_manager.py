import pytest
from unittest.mock import MagicMock, patch
from pymongo.errors import AutoReconnect, OperationFailure
from bson.objectid import ObjectId
from datetime import datetime, timezone
import asyncio
from src.database.db_manager import DatabaseManager, ConnectionError, OperationError

class TestDatabaseManager:
    def test_connection_retry(self, test_collection_name):
        """Test de reintentos de conexión."""
        # Crear cliente y colección mockeados
        mock_collection = MagicMock()
        mock_collection.insert_one.side_effect = AutoReconnect("Test disconnect")
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        
        # Crear instancia de DatabaseManager con cliente mockeado
        manager = DatabaseManager(client=mock_client, database="test_db")
        
        with pytest.raises(ConnectionError) as exc_info:
            manager.insert_one(test_collection_name, {"test": "data"})
        
        assert "No se pudo reconectar" in str(exc_info.value)
        assert mock_collection.insert_one.call_count == 3

    def test_connection_retry_backoff(self, test_collection_name):
        """Test del backoff exponencial en reintentos."""
        sleep_times = []

        def mock_sleep(seconds):
            sleep_times.append(seconds)

        # Crear cliente y colección mockeados
        mock_collection = MagicMock()
        mock_collection.insert_one.side_effect = AutoReconnect("Test disconnect")
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        manager = DatabaseManager(client=mock_client, database="test_db")

        with patch('time.sleep', side_effect=mock_sleep):
            with pytest.raises(ConnectionError):
                manager.insert_one(test_collection_name, {"test": "data"})

        expected_delays = [1, 2]
        assert sleep_times == expected_delays
        assert mock_collection.insert_one.call_count == 3

    def test_retry_on_various_exceptions(self, test_collection_name):
        """Test del comportamiento del retry con diferentes excepciones."""
        call_count = 0

        def mock_insert_one(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise AutoReconnect("Test disconnect")
            return MagicMock(inserted_id=ObjectId())

        # Crear cliente y colección mockeados
        mock_collection = MagicMock()
        mock_collection.insert_one.side_effect = mock_insert_one
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        manager = DatabaseManager(client=mock_client, database="test_db")
        result = manager.insert_one(test_collection_name, {"test": "data"})
        
        assert result is not None
        assert call_count == 3
        assert mock_collection.insert_one.call_count == 3

    @pytest.mark.asyncio
    async def test_concurrent_retries(self, test_collection_name):
        """Test de reintentos en operaciones concurrentes."""
        retry_counts = {}

        def mock_insert_one(document):
            doc_id = document.get('id', 'unknown')
            retry_counts[doc_id] = retry_counts.get(doc_id, 0) + 1
            if retry_counts[doc_id] < 2:
                raise AutoReconnect(f"Test disconnect for {doc_id}")
            return MagicMock(inserted_id=ObjectId())

        # Crear cliente y colección mockeados
        mock_collection = MagicMock()
        mock_collection.insert_one.side_effect = mock_insert_one
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        manager = DatabaseManager(client=mock_client, database="test_db")

        async def concurrent_insert(doc_id):
            return manager.insert_one(
                test_collection_name,
                {"id": doc_id, "test": "data"}
            )

        tasks = [concurrent_insert(f"doc_{i}") for i in range(3)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verificar que cada operación se reintentó al menos una vez
        for i in range(3):
            assert retry_counts[f"doc_{i}"] >= 2

        assert all(not isinstance(r, Exception) for r in results)
        assert mock_collection.insert_one.call_count >= 6

    def test_non_reconnect_errors(self, test_collection_name):
        """Test de errores que no son de reconexión."""
        # Crear cliente y colección mockeados
        mock_collection = MagicMock()
        mock_collection.insert_one.side_effect = OperationFailure("Test failure")
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        manager = DatabaseManager(client=mock_client, database="test_db")

        with pytest.raises(OperationError):
            manager.insert_one(test_collection_name, {"test": "data"})

        assert mock_collection.insert_one.call_count == 1