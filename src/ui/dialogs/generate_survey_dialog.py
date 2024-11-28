# src/ui/dialogs/generate_survey_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QProgressBar, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal
import os
from ..data_manager import UIDataManager
from ...utils.survey_generator import SurveyGenerator
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class GenerateSurveyDialog(QDialog):
    surveys_generated = pyqtSignal(str)  # Señal emitida cuando se generan las encuestas

    def __init__(self, activity_data: Dict, participants: List[Dict], parent=None):
        super().__init__(parent)
        self.activity_data = activity_data
        self.participants = participants
        self.survey_generator = SurveyGenerator()
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self.setWindowTitle("Generar Encuestas")
        self.setModal(True)
        self.resize(400, 200)

        layout = QVBoxLayout(self)

        # Información
        info_label = QLabel(
            f"Se generarán encuestas para {len(self.participants)} participantes\n"
            f"Actividad: {self.activity_data.get('name', 'Sin nombre')}"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(len(self.participants))
        layout.addWidget(self.progress_bar)

        # Botones
        button_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generar Encuestas")
        self.generate_button.clicked.connect(self.generate_surveys)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def generate_surveys(self):
        """Genera las encuestas para todos los participantes"""
        try:
            # Solicitar directorio de destino
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "Seleccionar Carpeta para Encuestas",
                os.path.expanduser("~")
            )

            if not output_dir:
                return

            self.generate_button.setEnabled(False)
            self.progress_bar.setValue(0)

            # Generar encuestas
            for i, participant in enumerate(self.participants):
                output_path = os.path.join(
                    output_dir,
                    f"survey_{participant.get('id', str(i))}.pdf"
                )

                self.survey_generator.generate_survey_pdf(
                    participant_id=participant.get('id', ''),
                    survey_name=self.activity_data.get('name', ''),
                    participant_name=participant.get('name', ''),
                    activity_data=self.activity_data,
                    output_path=output_path
                )

                self.progress_bar.setValue(i + 1)

            QMessageBox.information(
                self,
                "Éxito",
                f"Se generaron {len(self.participants)} encuestas en:\n{output_dir}"
            )
            self.surveys_generated.emit(output_dir)
            self.accept()

        except Exception as e:
            logger.error(f"Error al generar encuestas: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al generar encuestas: {str(e)}"
            )
            self.generate_button.setEnabled(True)