# src/ocr/batch_processor.py

import re
import cv2
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from .preprocessor import ImagePreprocessor
import numpy as np
import pytesseract
from .scanner import SurveyScanner

logger = logging.getLogger(__name__)

class BatchProcessor:
   def __init__(self):
       self.preprocessor = ImagePreprocessor()
       self.scanner = SurveyScanner()
       
   async def process_image(self, image_path: str) -> Dict[str, Any]:
       try:
           processed_image = self.preprocessor.preprocess_image(image_path)
           
           participant_id = self._extract_participant_id(processed_image)
           responses = self._process_responses(processed_image) 
           confidence = self._calculate_confidence(responses)
           
           return {
               "participant_id": participant_id,
               "responses": responses,
               "confidence": confidence,
               "processed_at": datetime.now().isoformat()
           }
           
       except Exception as e:
           logger.error(f"Error procesando imagen {image_path}: {e}")
           raise
           
   def _extract_participant_id(self, image) -> str:
       try:
           height = image.shape[0]
           header_region = image[0:int(height * 0.2), :]
           enhanced = self.preprocessor._enhance_text_region(header_region)
           header_text = self.scanner._process_text(enhanced)
           
           match = re.search(r'ID_PARTICIPANTE\s*(\d+)', header_text)
           if match:
               return match.group(1).strip()
           return ""
           
       except Exception as e:
           logger.error(f"Error extrayendo ID: {e}")
           return ""

   def _process_responses(self, image) -> Dict[str, str]:
       try:
           responses = {}
           enhanced_image = self.preprocessor._enhance_text_region(image)
           text = self.scanner._process_text(enhanced_image)
           
           lines = text.split('\n')
           current_question = None
           
           for line in lines:
               line = line.strip()
               
               if '$' in line:
                   if current_question:
                       responses[current_question] = []
                   question_text = line[line.index('$')+1:].strip()
                   current_question = question_text
                   continue
               
               if current_question and re.match(r'^\d+[\s_]*$', line):
                   num = re.match(r'^\d+', line).group()
                   region = self._get_line_region(image, line)
                   if region is not None and self._detect_mark(region):
                       if current_question not in responses:
                           responses[current_question] = []
                       responses[current_question].append(num)
           
           return responses
               
       except Exception as e:
           logger.error(f"Error procesando respuestas: {e}")
           return {}

   def _get_line_region(self, image: np.ndarray, line_text: str) -> Optional[np.ndarray]:
       try:
           height = image.shape[0]
           section_height = 50
           
           for i in range(0, height, section_height):
               section = image[i:min(i + section_height, height), :]
               section_text = self.scanner._process_text(section)
               if line_text in section_text:
                   return section
           return None
           
       except Exception as e:
           logger.error(f"Error obteniendo región de línea: {e}")
           return None
       
   def _calculate_confidence(self, responses: Dict[str, str]) -> float:
       try:
           if not responses:
               return 0.0
           total_questions = len(responses)
           answered_questions = sum(1 for response in responses.values() if response)
           return answered_questions / total_questions
           
       except Exception as e:
           logger.error(f"Error calculando confianza: {e}")
           return 0.0
   
   def _detect_mark(self, image_region: np.ndarray) -> bool:
       try:
           if image_region is None or image_region.size == 0:
               return False

           enhanced = self.preprocessor._enhance_marks_region(image_region)
           contours, _ = cv2.findContours(enhanced, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
           
           for contour in contours:
               area = cv2.contourArea(contour)
               if area > 50:
                   return True
           return False
           
       except Exception as e:
           logger.error(f"Error detectando marca: {e}")
           return False


class SimpleBatchProcessor:
    """Clase para procesar múltiples imágenes en una carpeta."""
    
    def __init__(self, input_dir: str, output_dir: str):
        """
        Inicializa el procesador batch.
        
        Args:
            input_dir: Directorio con las imágenes a procesar
            output_dir: Directorio donde guardar las imágenes procesadas
            
        Raises:
            FileNotFoundError: Si el directorio de entrada no existe
            NotADirectoryError: Si la ruta de entrada no es un directorio
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Validar que el directorio de entrada existe y es un directorio
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
        if not self.input_dir.is_dir():
            raise NotADirectoryError(f"Input path is not a directory: {input_dir}")
            
        self.preprocessor = ImagePreprocessor()
        
        # Crear directorio de salida si no existe
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_directory(self, extensions: tuple = ('.png', '.jpg', '.jpeg'), parallel: bool = False) -> Dict:
        """
        Procesa todas las imágenes en el directorio de entrada.
        
        Args:
            extensions: Extensiones de archivo a procesar
            parallel: Si se procesa en paralelo
            
        Returns:
            Dict: Resultados del procesamiento
        """
        # Recopilar archivos a procesar
        image_files = []
        for ext in extensions:
            image_files.extend(self.input_dir.glob(f'*{ext}'))
        
        if not image_files:
            logger.info(f"No se encontraron imágenes en {self.input_dir}")
            return {}

        logger.info(f"Encontradas {len(image_files)} imágenes para procesar")
        
        # Inicializar resultados
        results = {
            'successful': 0,
            'failed': 0,
            'processed_images': [],
            'failed_files': []
        }

        if parallel:
            # Procesamiento en paralelo
            with ThreadPoolExecutor() as executor:
                futures = {executor.submit(self._process_image, img_path): img_path for img_path in image_files}
                for future in as_completed(futures):
                    img_path = futures[future]
                    try:
                        result = future.result()
                        if result:
                            results['successful'] += 1
                            results['processed_images'].append(result)
                        else:
                            results['failed'] += 1
                            results['failed_files'].append(str(img_path))
                    except Exception as e:
                        logger.error(f"Error procesando {img_path.name}: {str(e)}")
                        results['failed'] += 1
                        results['failed_files'].append(str(img_path))
        else:
            # Procesamiento secuencial
            for img_path in image_files:
                result = self._process_image(img_path)
                if result:
                    results['successful'] += 1
                    results['processed_images'].append(result)
                else:
                    results['failed'] += 1
                    results['failed_files'].append(str(img_path))

        # Mostrar resumen
        self._print_summary(results)
        
        return results

    def process_image(self, image_path: str) -> Dict[str, Any]:
        try:
            processed_image = self.preprocessor.preprocess_image(image_path)
            if processed_image is None:
                raise ValueError("No se pudo procesar la imagen")
                
            participant_id = self._extract_participant_id(processed_image)
            responses = self._process_responses(processed_image)
            confidence = self._calculate_confidence(responses)
            
            return {
                "participant_id": participant_id,
                "responses": responses,
                "confidence": confidence,
                "processed_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error procesando imagen {image_path}: {e}")
            raise

    def _print_summary(self, results: Dict):
        """
        Imprime un resumen del procesamiento.
        
        Args:
            results: Diccionario con los resultados del procesamiento
        """
        logger.info("\n=== Resumen de Procesamiento ===")
        logger.info(f"Total de imágenes procesadas exitosamente: {results['successful']}")
        logger.info(f"Total de imágenes fallidas: {results['failed']}")
        
        if results['successful'] > 0:
            # Calcular calidad promedio
            qualities = [img['quality'] for img in results['processed_images']]
            avg_quality = sum(qualities) / len(qualities)
            logger.info(f"Calidad promedio: {avg_quality:.2f}")
            
            # Mostrar mejor y peor imagen
            best_image = max(results['processed_images'], key=lambda x: x['quality'])
            worst_image = min(results['processed_images'], key=lambda x: x['quality'])
            
            logger.info(f"Mejor imagen procesada: {best_image['filename']} con calidad {best_image['quality']:.2f}")
            logger.info(f"Peor imagen procesada: {worst_image['filename']} con calidad {worst_image['quality']:.2f}")
                
        logger.info("=============================")

    def get_processing_stats(self) -> Dict:
        """
        Obtiene estadísticas del procesamiento.
        
        Returns:
            Dict: Estadísticas de procesamiento
        """
        stats = {
            'total_processed': 0,
            'total_files': 0,
            'avg_quality': 0.0,
            'processing_time': 0.0
        }
        
        # Contar archivos procesados
        processed_files = list(self.output_dir.glob('processed_*'))
        stats['total_processed'] = len(processed_files)
        
        # Contar archivos totales en directorio de entrada
        total_files = list(self.input_dir.glob('*.*'))
        stats['total_files'] = len(total_files)
        
        return stats