# Usar una imagen base más reciente
FROM python:3.9-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Configurar directorio de trabajo
WORKDIR /app

# Copiar archivos de requirements
COPY requirements.txt requirements-dev.txt ./

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "$ENVIRONMENT" = "development" ] ; then pip install --no-cache-dir -r requirements-dev.txt ; fi

# Copiar el código de la aplicación
COPY . .

# Exponer puertos necesarios
EXPOSE 8501

# Comando por defecto
CMD ["streamlit", "run", "src/ui/coordinator.py"]