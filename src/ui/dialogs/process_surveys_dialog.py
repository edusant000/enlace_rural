# src/ui/dialogs/process_surveys_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QProgressBar, QMessageBox, QFileDialog,
                           QScrollArea, QWidget, QGridLayout, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QImage
import os
import logging
from typing import List, Dict
from ...ocr.batch_processor import BatchProcessor
from ...ocr.preprocessor import Preprocessor
from ..views.image_management_view import ImageManagementView

logger = logging.getLogger(__name__)

class ProcessSurveysDialog(QDialog):
    surveys_processed = pyqtSignal(list)  # Emite lista de resultados OCR

    def __init__(self, activity_id: str, parent=None):
        super().__init__(parent)
        self.activity_id = activity_id
        self.image_paths = []
        self.ocr_results = []
        self.batch_processor = BatchProcessor()
        self.preprocessor = Preprocessor()
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self.setWindowTitle("Procesar Encuestas")
        self.setModal(True)
        self.resize(1000, 800)

        main_layout = QVBoxLayout(self)

        # Integrar ImageManagementView
        self.image_view = ImageManagementView(self)
        self.image_view.processing_complete.connect(self.handle_processing_complete)
        main_layout.addWidget(self.image_view)

        # Botón de guardar
        self.save_btn = QPushButton("Guardar Resultados")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_results)
        main_layout.addWidget(self.save_btn)

    def handle_processing_complete(self, results: Dict):
        """Maneja los resultados del procesamiento OCR"""
        self.ocr_results = list(results.values())
        self.save_btn.setEnabled(True)

    async def save_results(self):
        """Guarda los resultados del OCR"""
        try:
            self.surveys_processed.emit(self.ocr_results)
            QMessageBox.information(
                self,
                "Éxito",
                "Resultados guardados exitosamente"
            )
            self.accept()
        except Exception as e:
            logger.error(f"Error al guardar resultados: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al guardar resultados: {str(e)}"
            )