from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, 
                            QLineEdit, QTextEdit, QDateEdit, 
                            QPushButton, QComboBox, QHBoxLayout)
from PyQt6.QtCore import Qt
from ..models.activity import Activity, SurveyTemplate, SurveyType
from datetime import datetime

class ActivityDialog(QDialog):
    def __init__(self, parent=None, activity=None):
        super().__init__(parent)
        self.activity = activity
        self.setup_ui()
        if activity:
            self.load_activity_data()

    def setup_ui(self):
        self.setWindowTitle("Crear/Editar Actividad")
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Campos básicos
        self.name_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.location_edit = QLineEdit()
        self.start_date_edit = QDateEdit()
        self.end_date_edit = QDateEdit()
        
        # Selector de tipo de encuesta
        self.survey_type_combo = QComboBox()
        for survey_type in SurveyType:
            self.survey_type_combo.addItem(survey_type.value)

        # Añadir campos al formulario
        form_layout.addRow("Nombre:", self.name_edit)
        form_layout.addRow("Descripción:", self.description_edit)
        form_layout.addRow("Ubicación:", self.location_edit)
        form_layout.addRow("Fecha inicio:", self.start_date_edit)
        form_layout.addRow("Fecha fin:", self.end_date_edit)
        form_layout.addRow("Tipo de encuesta:", self.survey_type_combo)

        # Botones
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Guardar")
        self.cancel_button = QPushButton("Cancelar")
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)

        # Conexiones
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def load_activity_data(self):
        if self.activity:
            self.name_edit.setText(self.activity.name)
            self.description_edit.setText(self.activity.description or "")
            self.location_edit.setText(self.activity.location)
            self.start_date_edit.setDate(self.activity.start_date)
            if self.activity.end_date:
                self.end_date_edit.setDate(self.activity.end_date)
            index = self.survey_type_combo.findText(self.activity.survey_template.type.value)
            if index >= 0:
                self.survey_type_combo.setCurrentIndex(index)

    def get_activity_data(self) -> Activity:
        return Activity(
            name=self.name_edit.text(),
            description=self.description_edit.toPlainText(),
            survey_template=SurveyTemplate(
                name=f"Survey_{self.name_edit.text()}",
                questions=[],  # Se llenarán después
                type=SurveyType(self.survey_type_combo.currentText()),
            ),
            start_date=self.start_date_edit.date().toPyDate(),
            end_date=self.end_date_edit.date().toPyDate(),
            location=self.location_edit.text(),
        )