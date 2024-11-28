import asyncio
import logging
from PyQt6.QtWidgets import (QComboBox, QSplitter, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFileDialog, QScrollArea, QProgressBar,
                           QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QImage, QPixmap
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional

from ..controllers.activity_controller import ActivityController
from ...ocr.batch_processor import BatchProcessor
from ...ocr.preprocessor import ImagePreprocessor
from ...utils.logger import setup_logger

logger = logging.getLogger(__name__)

class ImageProcessingThread(QThread):
    progress = pyqtSignal(int)
    result_ready = pyqtSignal(str, dict)  # Nueva señal
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, image_paths: List[Path], processor: BatchProcessor, parent=None):
        super().__init__(parent)
        self.image_paths = image_paths
        self.processor = processor
        self.results = {}

    def run(self):
        try:
            total = len(self.image_paths)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            for i, path in enumerate(self.image_paths):
                try:
                    # Procesar imagen
                    result = loop.run_until_complete(
                        self.processor.process_image(str(path))
                    )
                    self.results[str(path)] = result
                    self.result_ready.emit(str(path), result)
                    
                except Exception as e:
                    logger.error(f"Error processing {path}: {e}")
                    self.results[str(path)] = {"error": str(e)}
                
                self.progress.emit(int((i + 1) * 100 / total))
            
            self.finished.emit(self.results)
            loop.close()
            
        except Exception as e:
            self.error.emit(str(e))

class ImageManagementView(QWidget):
    processing_complete = pyqtSignal(dict)
    
    def __init__(self, data_manager=None, parent=None):
        super().__init__(parent)
        self.batch_processor = BatchProcessor()
        self.image_preprocessor = ImagePreprocessor()
        self.data_manager = data_manager
        self.image_paths: List[Path] = []
        self.current_image_index = 0
        self.processed_results: Dict = {}
        
        self.setup_ui()
        if self.data_manager:
            asyncio.create_task(self.load_activities())
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Selector de actividad
        activity_layout = QHBoxLayout()
        self.activity_combo = QComboBox()
        activity_layout.addWidget(QLabel("Actividad:"))
        activity_layout.addWidget(self.activity_combo)
        activity_layout.addStretch()
        
        # Controles superiores
        top_controls = QHBoxLayout()
        self.select_btn = QPushButton("Seleccionar Imágenes")
        self.select_btn.clicked.connect(self.select_images)
        self.process_btn = QPushButton("Procesar")
        self.process_btn.clicked.connect(self.process_images)
        self.process_btn.setEnabled(False)
        
        top_controls.addWidget(self.select_btn)
        top_controls.addWidget(self.process_btn)
        
        # Vista dividida
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel izquierdo: Imagen
        image_panel = QWidget()
        image_layout = QVBoxLayout(image_panel)
        
        self.scroll_area = QScrollArea()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(True)
        
        # Navegación
        nav_controls = QHBoxLayout()
        self.prev_btn = QPushButton("Anterior")
        self.next_btn = QPushButton("Siguiente")
        self.prev_btn.clicked.connect(self.show_previous_image)
        self.next_btn.clicked.connect(self.show_next_image)
        self.image_counter = QLabel("0/0")
        
        nav_controls.addWidget(self.prev_btn)
        nav_controls.addWidget(self.image_counter)
        nav_controls.addWidget(self.next_btn)
        
        image_layout.addWidget(self.scroll_area)
        image_layout.addLayout(nav_controls)
        splitter.addWidget(image_panel)
        
        # Panel derecho: OCR
        ocr_panel = QWidget()
        ocr_layout = QVBoxLayout(ocr_panel)
        self.ocr_preview = QLabel()
        self.ocr_preview.setWordWrap(True)
        self.ocr_preview.setStyleSheet("background-color: white; padding: 10px;")
        
        ocr_layout.addWidget(QLabel("Resultados OCR:"))
        ocr_layout.addWidget(self.ocr_preview)
        splitter.addWidget(ocr_panel)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Layout principal
        layout.addLayout(activity_layout)
        layout.addLayout(top_controls)
        layout.addWidget(self.progress_bar)
        layout.addWidget(splitter)
        
        self.setLayout(layout)
        self.update_navigation_buttons()

    async def load_activities(self):
        """Cargar actividades en el combo"""
        try:
            activities = await self.data_manager.get_all_activities()
            self.activity_combo.clear()
            for activity in activities:
                self.activity_combo.addItem(activity['name'], activity['_id'])
        except Exception as e:
            logger.error(f"Error cargando actividades: {e}")
            QMessageBox.warning(self, "Error", "No se pudieron cargar las actividades")

    def select_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar Imágenes",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        
        if files:
            self.image_paths = [Path(f) for f in files]
            self.current_image_index = 0
            self.process_btn.setEnabled(True)
            self.show_current_image()
            self.update_navigation_buttons()
            
    def process_images(self):
        if not self.image_paths or self.activity_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Error", "Seleccione una actividad y algunas imágenes")
            return
                
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_bar.show()
        self.process_btn.setEnabled(False)
        
        activity_id = self.activity_combo.currentData()
        self.processing_thread = ImageProcessingThread(self.image_paths, self.batch_processor)
        self.processing_thread.progress.connect(self.progress_bar.setValue)
        self.processing_thread.result_ready.connect(self.handle_result)
        self.processing_thread.finished.connect(lambda results: self.handle_processing_complete(results, activity_id))
        self.processing_thread.error.connect(self.handle_processing_error)
        self.processing_thread.start()
        
    async def handle_processing_complete(self, results: Dict, activity_id: str):
        """Maneja el completado del procesamiento y guarda los resultados"""
        try:
            self.processed_results = results
            self.progress_bar.setVisible(False)
            self.update_ocr_preview()
            
            # Guardar resultados en la base de datos
            if self.data_manager:
                for path, result in results.items():
                    if 'error' not in result:
                        await self.data_manager.save_survey_result(
                            activity_id=activity_id,
                            participant_id=result['participant_id'],
                            responses=result['responses']
                        )
            
            self.processing_complete.emit(results)
            QMessageBox.information(self, "Éxito", "Procesamiento completado")
            
        except Exception as e:
            logger.error(f"Error guardando resultados: {e}")
            QMessageBox.warning(self, "Error", f"Error guardando resultados: {str(e)}")
        
    def handle_processing_error(self, error_msg: str):
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Error en el procesamiento: {error_msg}")

    def handle_result(self, path: str, result: dict):
        self.processed_results[path] = result
        if path == str(self.image_paths[self.current_image_index]):
            self.update_ocr_preview()
        
    def show_current_image(self):
        if not self.image_paths:
            return
            
        current_path = self.image_paths[self.current_image_index]
        image = cv2.imread(str(current_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Preprocesar imagen para mejor visualización
        preprocessed = self.image_preprocessor.preprocess_image(str(current_path))
        if preprocessed is not None:
            image = cv2.cvtColor(preprocessed, cv2.COLOR_GRAY2RGB)
        
        h, w, ch = image.shape
        bytes_per_line = ch * w
        qt_image = QImage(image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Escalar manteniendo proporción
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.scroll_area.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        self.image_counter.setText(f"{self.current_image_index + 1}/{len(self.image_paths)}")
        self.update_ocr_preview()
        
    def show_next_image(self):
        if self.current_image_index < len(self.image_paths) - 1:
            self.current_image_index += 1
            self.show_current_image()
            self.update_navigation_buttons()
            
    def show_previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_current_image()
            self.update_navigation_buttons()
            
    def update_navigation_buttons(self):
        self.prev_btn.setEnabled(self.current_image_index > 0)
        self.next_btn.setEnabled(self.current_image_index < len(self.image_paths) - 1)
        
    def update_ocr_preview(self):
        if not self.image_paths:
            return
            
        current_path = str(self.image_paths[self.current_image_index])
        if current_path in self.processed_results:
            result = self.processed_results[current_path]
            preview_text = f"ID Participante: {result['participant_id']}\n"
            preview_text += "Respuestas:\n"
            for question, answer in result['responses'].items():
                preview_text += f"{question}: {answer}\n"
            preview_text += f"Confianza: {result['confidence']:.2%}"
            self.ocr_preview.setText(preview_text)
        else:
            self.ocr_preview.setText("Sin procesar")