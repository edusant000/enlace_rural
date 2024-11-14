import cv2
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from .preprocessor import ImagePreprocessor
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

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

    def _process_image(self, img_path: Path) -> Optional[Dict]:
        """
        Procesa una sola imagen.
        
        Args:
            img_path: Ruta de la imagen a procesar
            
        Returns:
            Optional[Dict]: Diccionario con información del procesamiento o None si falló
        """
        try:
            logger.debug(f"Procesando imagen: {img_path.name}")
            processed = self.preprocessor.preprocess_image(str(img_path))
            
            if processed is not None:
                # Evaluar calidad
                quality = self.preprocessor.assess_quality(processed)
                
                # Guardar imagen procesada
                output_path = self.output_dir / f"processed_{img_path.name}"
                cv2.imwrite(str(output_path), processed)
                
                logger.info(f"Imagen procesada: {img_path.name} con calidad {quality:.2f}")
                
                return {
                    'filename': img_path.name,
                    'quality': quality,
                    'output_path': str(output_path)
                }
            else:
                logger.warning(f"No se pudo procesar {img_path.name}")
                return None
                
        except Exception as e:
            logger.error(f"Error procesando {img_path.name}: {str(e)}")
            return None

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