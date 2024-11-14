import cv2
import numpy as np
from typing import Optional, Dict, List, Union
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """
    Clase para preprocesar imágenes antes del OCR.
    Implementa mejoras de calidad y normalización de imágenes.
    """
    
    def __init__(self, min_quality_score: float = 0.5):
        """
        Inicializa el preprocesador de imágenes.
        
        Args:
            min_quality_score: Puntuación mínima de calidad (0-1)
        """
        self.min_quality_score = min_quality_score
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        self.quality_cache = {}
        self.max_image_size = 4000

    def preprocess_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Preprocesa una imagen para optimizarla para OCR.
        
        Args:
            image_path: Ruta a la imagen
            
        Returns:
            np.ndarray: Imagen procesada o None si la calidad es insuficiente
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si la imagen no puede ser cargada
        """
        # Verificar que el archivo existe
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        try:
            # Cargar imagen
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"No se pudo cargar la imagen: {image_path}")

            # Verificar calidad
            quality_score = self.assess_quality(image)
            if quality_score < self.min_quality_score:
                logger.warning(f"Calidad de imagen insuficiente ({quality_score:.2f}): {image_path}")
                return None

            # Aplicar preprocesamiento
            processed = self._process_steps(image)
            return processed

        except Exception as e:
            logger.error(f"Error en preprocesamiento de {image_path}: {str(e)}")
            if isinstance(e, FileNotFoundError):
                raise
            return None

    def check_image_problems(self, image: np.ndarray) -> Dict[str, bool]:
        """
        Identifica problemas específicos en la imagen.
        
        Args:
            image: Imagen a analizar
            
        Returns:
            Dict[str, bool]: Diccionario de problemas detectados
        """
        problems = {}
        
        # Verificar dimensiones
        height, width = image.shape[:2]
        problems['too_large'] = height > self.max_image_size or width > self.max_image_size
        
        # Convertir a escala de grises si es necesario
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Verificar brillo
        brightness = np.mean(gray)
        problems['too_dark'] = bool(brightness < 50)
        problems['too_bright'] = bool(brightness > 200)
        
        # Verificar contraste
        contrast = np.std(gray)
        problems['low_contrast'] = bool(contrast < 30)
        
        # Verificar borrosidad
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        problems['blurry'] = bool(np.var(laplacian) < 100)
        
        # Verificar rotación
        angle = self._detect_skew(gray)
        problems['skewed'] = bool(abs(angle) > 5.0)  # Umbral más realista para la rotación
        
        return problems

    def get_optimization_suggestions(self, problems: Dict[str, bool]) -> List[str]:
        """
        Proporciona sugerencias para mejorar la calidad de la imagen.
        
        Args:
            problems: Diccionario de problemas detectados
            
        Returns:
            List[str]: Lista de sugerencias de optimización
        """
        suggestions = []
        
        if problems.get('too_large', False):
            suggestions.append(f"Reducir el tamaño de la imagen a menos de {self.max_image_size}x{self.max_image_size} píxeles")
        if problems.get('too_dark', False):
            suggestions.append("Aumentar el brillo de la imagen")
        if problems.get('too_bright', False):
            suggestions.append("Reducir el brillo o aumentar el contraste")
        if problems.get('low_contrast', False):
            suggestions.append("Mejorar el contraste de la imagen")
        if problems.get('blurry', False):
            suggestions.append("Usar una imagen más nítida o aplicar técnicas de enfoque")
        if problems.get('skewed', False):
            suggestions.append("Corregir la rotación de la imagen")
        
        return suggestions

    def get_quality_metrics(self, image: np.ndarray) -> Dict[str, float]:
        """
        Obtiene métricas detalladas de calidad de la imagen.
        
        Args:
            image: Imagen a analizar
            
        Returns:
            Dict[str, float]: Diccionario con métricas de calidad
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        metrics = {
            'brightness': np.mean(gray) / 255.0,
            'contrast': np.std(gray) / 128.0,
            'sharpness': np.var(cv2.Laplacian(gray, cv2.CV_64F)) / 1000.0,
            'size_score': min(min(image.shape[:2]) / 1000.0, 1.0),
            'skew_angle': self._detect_skew(gray),
            'overall_quality': self.assess_quality(image)
        }
        
        return metrics

    def assess_quality(self, image: np.ndarray) -> float:
        """
        Evalúa la calidad de la imagen.
        
        Args:
            image: Imagen a evaluar
            
        Returns:
            float: Puntuación de calidad (0-1)
        """
        try:
            # Convertir a escala de grises si es necesario
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            scores = []
            
            # Verificar brillo y contraste
            brightness = np.mean(gray) / 255.0
            scores.append(1.0 - abs(0.5 - brightness))
            
            # Verificar borrosidad
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = np.var(laplacian)
            sharpness = min(variance / 1000.0, 1.0)
            scores.append(sharpness)
            
            # Verificar tamaño
            height, width = image.shape[:2]
            size_score = min(min(width, height) / 1000.0, 1.0)
            scores.append(size_score)
            
            # Verificar contraste
            contrast = np.std(gray) / 128.0
            scores.append(min(contrast, 1.0))
            
            # Verificar rotación
            angle = self._detect_skew(gray)
            skew_score = 1.0 - min(abs(angle) / 45.0, 1.0)
            scores.append(skew_score)
            
            return sum(scores) / len(scores)
            
        except Exception as e:
            logger.error(f"Error al evaluar calidad de la imagen: {str(e)}")
            return 0.0

    def _process_steps(self, image: np.ndarray) -> np.ndarray:
        """
        Aplica todos los pasos de preprocesamiento en orden.
        """
        # Convertir a escala de grises si es necesario
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Reducir ruido
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        
        # Mejorar contraste
        enhanced = self._enhance_contrast(denoised)
        
        # Binarizar
        binary = self._adaptive_threshold(enhanced)
        
        # Corregir rotación si es necesario
        angle = self._detect_skew(binary)
        if abs(angle) > 0.5:
            binary = self._correct_skew(binary, angle)
        
        return binary

    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Mejora el contraste usando CLAHE."""
        return self.clahe.apply(image)

    def _adaptive_threshold(self, image: np.ndarray) -> np.ndarray:
        """Aplica umbral adaptativo."""
        return cv2.adaptiveThreshold(
            image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )

    def _detect_skew(self, image: np.ndarray) -> float:
        """
        Detecta el ángulo de rotación de la imagen.
        
        Args:
            image: Imagen en escala de grises
                
        Returns:
            float: Ángulo de rotación en grados
        """
        try:
            # Binarizar la imagen para mejor detección de bordes
            _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Encontrar bordes
            edges = cv2.Canny(binary, 50, 150, apertureSize=3)
            
            # Detectar líneas usando la transformada de Hough
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                                minLineLength=100, maxLineGap=10)
            
            if lines is None or len(lines) == 0:
                return 0.0
                
            # Calcular ángulos de todas las líneas detectadas
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 - x1 == 0:  # Evitar división por cero
                    continue
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                # Normalizar ángulo al rango [-45, 45]
                if angle < -45:
                    angle += 90
                elif angle > 45:
                    angle -= 90
                angles.append(angle)
                
            if not angles:
                return 0.0
                
            # Usar la mediana para ser más robusto a valores atípicos
            return float(np.median(angles))
            
        except Exception as e:
            logging.warning(f"Error al detectar rotación: {str(e)}")
            return 0.0

    def _correct_skew(self, image: np.ndarray, angle: float = None) -> np.ndarray:
        """
        Corrige la rotación de la imagen.
        
        Args:
            image: Imagen a corregir
            angle: Ángulo de rotación (opcional)
            
        Returns:
            np.ndarray: Imagen corregida
        """
        if angle is None:
            angle = self._detect_skew(image)
        
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        corrected = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        return corrected