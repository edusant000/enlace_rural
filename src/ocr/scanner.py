import cv2
import numpy as np
import pytesseract
import os
from typing import Dict, Optional, List, Tuple, Union
from dataclasses import dataclass
import logging
from pathlib import Path

# Definir la excepción personalizada al inicio del archivo
class ScannerError(Exception):
    """Excepción personalizada para errores del scanner."""
    pass

@dataclass
class SurveyField:
    """Representa un campo en la encuesta."""
    name: str
    box_coordinates: Tuple[int, int, int, int]  # x, y, width, height
    field_type: str  # 'text', 'checkbox', 'number'
    options: List[str] = None  # Para campos checkbox

class SurveyScanner:
    """Clase para escanear y extraer datos de encuestas usando OCR."""
    
    VALID_FIELD_TYPES = ['text', 'checkbox', 'number']
    
    # src/ocr/scanner.py

    def __init__(self, template_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.template = self._load_template(template_path) if template_path else None
        self.fields: List[SurveyField] = []
        
        # Configurar Tesseract con la ruta correcta
        pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'  # Cambiado de /opt/homebrew/bin/tesseract
        tessdata_path = '/usr/local/share/tessdata'
        
        # Configuración completa de OCR
        custom_config = (
            f'--tessdata-dir "{tessdata_path}" '
            '--oem 3 '
            '--psm 6 '
            '-l spa ' # Añadir español
            '-c preserve_interword_spaces=1 '
            '-c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ0123456789_$:/ "' # Expandir caracteres permitidos
        )
        self.tesseract_config = custom_config
        
    def _load_template(self, template_path: str) -> np.ndarray:
        """
        Carga el template de la encuesta para alineación.
        
        Args:
            template_path: Ruta al archivo de template
            
        Returns:
            np.ndarray: Imagen del template
            
        Raises:
            FileNotFoundError: Si el template no existe
            ValueError: Si el template no se puede cargar
        """
        if not Path(template_path).exists():
            raise FileNotFoundError(f"Template no encontrado: {template_path}")
            
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            raise ValueError(f"No se pudo cargar el template: {template_path}")
            
        return template
        
    def register_field(self, field: SurveyField) -> None:
        """
        Registra un nuevo campo para extraer de la encuesta.
        
        Args:
            field: Campo a registrar
            
        Raises:
            ValueError: Si el tipo de campo no es válido o falta configuración
        """
        if field.field_type not in self.VALID_FIELD_TYPES:
            raise ValueError(f"Tipo de campo inválido: {field.field_type}")
            
        if field.field_type == 'checkbox' and not field.options:
            raise ValueError("Los campos checkbox requieren opciones")
            
        self.fields.append(field)
        
    def scan_survey(self, image: Union[str, np.ndarray]) -> Dict[str, str]:
        """
        Escanea una imagen de encuesta y extrae los datos.
        
        Args:
            image: Ruta a la imagen o array de imagen
            
        Returns:
            Dict[str, str]: Valores extraídos de los campos
            
        Raises:
            ScannerError: Si hay errores durante el escaneo
        """
        try:
            # Cargar imagen si es una ruta
            if isinstance(image, str):
                if not Path(image).exists():
                    raise ScannerError(f"Archivo no encontrado: {image}")
                image_array = cv2.imread(image)
                if image_array is None:
                    raise ScannerError(f"No se pudo cargar la imagen: {image}")
            else:
                image_array = image
                    
            # Alinear con template si existe
            if self.template is not None:
                aligned = self._align_with_template(image_array)
            else:
                aligned = image_array
                
            # Extraer datos de cada campo
            results = {}
            for field in self.fields:
                value = self._extract_field_value(aligned, field)
                results[field.name] = value
                
            return results
            
        except Exception as e:
            self.logger.error(f"Error escaneando encuesta: {str(e)}")
            raise ScannerError(str(e))
            
    def _align_with_template(self, image: np.ndarray) -> np.ndarray:
        """
        Alinea la imagen con el template usando feature matching.
        
        Args:
            image: Imagen a alinear
            
        Returns:
            np.ndarray: Imagen alineada
        """
        # Convertir a escala de grises si es necesario
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Detectar keypoints
        sift = cv2.SIFT_create()
        kp1, des1 = sift.detectAndCompute(self.template, None)
        kp2, des2 = sift.detectAndCompute(gray, None)
        
        if des1 is None or des2 is None:
            return image
        
        # Matching
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(des1, des2, k=2)
        
        # Filtrar buenos matches
        good = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                good.append(m)
                
        # Encontrar homografía
        if len(good) > 10:
            src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
            
            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            if M is not None:
                h, w = self.template.shape
                aligned = cv2.warpPerspective(image, M, (w, h))
                return aligned
            
        return image
        
    def _extract_field_value(self, image: np.ndarray, field: SurveyField) -> str:
        """
        Extrae el valor de un campo específico.
        
        Args:
            image: Imagen de la encuesta
            field: Campo a extraer
            
        Returns:
            str: Valor extraído
        """
        x, y, w, h = field.box_coordinates
        roi = image[y:y+h, x:x+w]
        
        if field.field_type == 'checkbox':
            return self._process_checkbox(roi, field.options)
        elif field.field_type == 'number':
            text = self._process_text(roi)
            # Intentar extraer solo números
            numbers = ''.join(filter(str.isdigit, text))
            return numbers if numbers else ''
        else:
            return self._process_text(roi)
            
    def _process_checkbox(self, roi: np.ndarray, options: List[str]) -> str:
        """
        Procesa región de checkboxes y determina cual está marcado.
        
        Args:
            roi: Región de interés de la imagen
            options: Lista de opciones posibles
            
        Returns:
            str: Opciones marcadas
        """
        # Convertir a escala de grises si es necesario
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi
            
        # Binarizar
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Analizar cada checkbox
        checked = []
        height_per_option = roi.shape[0] / len(options)
        
        for i, option in enumerate(options):
            y_start = int(i * height_per_option)
            y_end = int((i + 1) * height_per_option)
            
            # Contar píxeles marcados en esta región
            region = binary[y_start:y_end, :]
            marked_pixels = np.count_nonzero(region == 0)
            
            if marked_pixels > (region.size * 0.2):  # Umbral de 20%
                checked.append(option)
                
        return ", ".join(checked) if checked else ""
        
    def _process_text(self, roi: np.ndarray) -> str:
        """
        Procesa región de texto usando Tesseract.
        
        Args:
            roi: Región de interés de la imagen
            
        Returns:
            str: Texto extraído
        """
        try:
            # Asegurar que la imagen está en escala de grises
            if len(roi.shape) == 3:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            else:
                gray = roi
                
            # Mejorar contraste
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # Aplicar umbral adaptativo
            binary = cv2.adaptiveThreshold(
                enhanced,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2
            )
            
            # Procesar con Tesseract
            text = pytesseract.image_to_string(binary, config=self.tesseract_config)
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Error en OCR: {str(e)}")
            return ""