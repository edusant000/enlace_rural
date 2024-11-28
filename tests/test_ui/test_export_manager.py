import pytest
from datetime import datetime
import os
import pandas as pd
from src.ui.utils.export_manager import ExportManager

@pytest.fixture
def sample_data():
    """Fixture que proporciona datos de muestra para testing."""
    return [
        {
            "participant_id": "1",
            "activity_id": "1",
            "responses": {
                "pregunta1": "respuesta1",
                "pregunta2": "respuesta2"
            },
            "confidence": 95.5,
            "processed_at": datetime.now(),
            "notes": "Nota de prueba"
        }
    ]

@pytest.fixture
def sample_participants():
    """Fixture que proporciona datos de participantes de muestra."""
    return {
        "1": {
            "name": "Participante Test",
            "community": "Comunidad Test"
        }
    }

@pytest.fixture
def sample_activities():
    """Fixture que proporciona datos de actividades de muestra."""
    return {
        "1": {
            "name": "Actividad Test"
        }
    }

def test_prepare_export_data(sample_data, sample_participants, sample_activities):
    """Prueba la preparación de datos para exportación."""
    result = ExportManager.prepare_export_data(
        sample_data,
        sample_participants,
        sample_activities
    )
    
    assert len(result) == 2  # Dos filas (una por cada respuesta)
    assert result[0]["Participante"] == "Participante Test"
    assert result[0]["Comunidad"] == "Comunidad Test"
    assert result[0]["Actividad"] == "Actividad Test"

@pytest.mark.parametrize("export_format,extension", [
    ("csv", ".csv"),
    ("excel", ".xlsx"),
    ("pdf", ".pdf")
])
def test_export_formats(tmp_path, sample_data, sample_participants, 
                       sample_activities, export_format, extension):
    """Prueba la exportación en diferentes formatos."""
    # Preparar datos
    export_data = ExportManager.prepare_export_data(
        sample_data,
        sample_participants,
        sample_activities
    )
    
    # Crear nombre de archivo temporal
    filename = tmp_path / f"test_export{extension}"
    
    # Exportar según formato
    if export_format == "csv":
        ExportManager.export_to_csv(str(filename), export_data)
    elif export_format == "excel":
        ExportManager.export_to_excel(str(filename), export_data)
    elif export_format == "pdf":
        ExportManager.export_to_pdf(str(filename), export_data)
    
    # Verificar que el archivo existe y no está vacío
    assert os.path.exists(filename)
    assert os.path.getsize(filename) > 0

def test_csv_content(tmp_path, sample_data, sample_participants, sample_activities):
    """Prueba el contenido del archivo CSV exportado."""
    export_data = ExportManager.prepare_export_data(
        sample_data,
        sample_participants,
        sample_activities
    )
    
    filename = tmp_path / "test_export.csv"
    ExportManager.export_to_csv(str(filename), export_data)
    
    # Leer el CSV y verificar contenido
    df = pd.read_csv(filename)
    assert not df.empty
    assert "Participante" in df.columns
    assert "Comunidad" in df.columns
    assert "Actividad" in df.columns
    assert len(df) == len(export_data)

def test_excel_content(tmp_path, sample_data, sample_participants, sample_activities):
    """Prueba el contenido del archivo Excel exportado."""
    export_data = ExportManager.prepare_export_data(
        sample_data,
        sample_participants,
        sample_activities
    )
    
    filename = tmp_path / "test_export.xlsx"
    ExportManager.export_to_excel(str(filename), export_data)
    
    # Leer el Excel y verificar contenido
    df = pd.read_excel(filename, sheet_name="Resultados")
    assert not df.empty
    assert "Participante" in df.columns
    assert "Comunidad" in df.columns
    assert "Actividad" in df.columns
    assert len(df) == len(export_data)

def test_export_with_empty_data(tmp_path):
    """Prueba la exportación con datos vacíos."""
    filename = tmp_path / "test_export.csv"
    with pytest.raises(ValueError, match="No hay datos para exportar"):
        ExportManager.export_to_csv(str(filename), [])

def test_export_with_invalid_file_path():
    """Prueba la exportación con una ruta de archivo inválida."""
    with pytest.raises(Exception):
        ExportManager.export_to_csv("/ruta/invalida/archivo.csv", [{"test": "data"}])

def test_export_with_invalid_data(tmp_path):
    """Prueba la exportación con datos inválidos."""
    filename = tmp_path / "test_export.csv"
    invalid_data = [{"Participante": float('nan')}]  # Usar una columna que sabemos que existe
    
    with pytest.raises(ValueError, match="Datos inválidos en el conjunto de datos"):
        ExportManager.export_to_csv(str(filename), invalid_data)


def test_excel_with_charts(tmp_path, sample_data, sample_participants, sample_activities):
    """Prueba la exportación a Excel incluyendo gráficos."""
    export_data = ExportManager.prepare_export_data(
        sample_data,
        sample_participants,
        sample_activities
    )
    
    import matplotlib.pyplot as plt
    charts = {}
    # Crear un gráfico de ejemplo
    plt.figure()
    plt.plot([1, 2, 3], [1, 2, 3])
    charts['test_chart'] = plt.gcf()
    
    filename = tmp_path / "test_export.xlsx"
    ExportManager.export_to_excel(str(filename), export_data, charts)
    
    # Verificar que el archivo existe y tiene el tamaño esperado
    assert os.path.exists(filename)
    assert os.path.getsize(filename) > 0
    
    # Verificar que tiene múltiples hojas
    xls = pd.ExcelFile(filename)
    assert 'Resultados' in xls.sheet_names
    assert 'Resumen' in xls.sheet_names
    assert 'Gráficos' in xls.sheet_names

def test_data_format_validation(sample_data, sample_participants, sample_activities):
    """Prueba la validación del formato de los datos preparados."""
    export_data = ExportManager.prepare_export_data(
        sample_data,
        sample_participants,
        sample_activities
    )
    
    for row in export_data:
        assert isinstance(row['Confianza'], str)
        assert row['Confianza'].endswith('%')
        assert isinstance(row['Fecha'], str)
        # Verificar que la fecha tiene el formato correcto
        datetime.strptime(row['Fecha'], '%Y-%m-%d')

def test_missing_participant_activity_data(sample_data):
    """Prueba el manejo de participantes o actividades faltantes."""
    # Datos sin participante o actividad correspondiente
    export_data = ExportManager.prepare_export_data(
        sample_data,
        {},  # Sin participantes
        {}   # Sin actividades
    )
    
    assert export_data[0]['Participante'] == 'Desconocido'
    assert export_data[0]['Actividad'] == 'Desconocida'


def test_export_error_handling(tmp_path):
    """Test de manejo de errores en exportación"""
    filename = tmp_path / "nonexistent_dir" / "test_export.csv"
    
    with pytest.raises(IOError, match="No se pudo crear el archivo"):
        ExportManager.export_to_csv(str(filename), [{"test": "data"}])