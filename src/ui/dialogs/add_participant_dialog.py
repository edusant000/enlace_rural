# src/ui/dialogs/add_participant_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QSpinBox, QVBoxLayout, QMessageBox,
    QHBoxLayout, QLabel, QDateEdit, QWidget
)
from PyQt6.QtCore import pyqtSignal, Qt, QDate
from datetime import datetime

class AddParticipantDialog(QDialog):
    participantAdded = pyqtSignal(dict)
    
    EDUCATION_LEVELS = [
        "Sin educación formal",
        "Primaria incompleta",
        "Primaria completa",
        "Secundaria incompleta",
        "Secundaria completa",
        "Preparatoria",
        "Educación superior"
    ]
    
    GENDER_OPTIONS = [
        "Hombre",
        "Mujer",
        "Otro"
    ]
    
    INCOME_LEVELS = [
        "Menos de $5,000",
        "Entre $5,000 y $10,000",
        "Entre $10,000 y $15,000",
        "Entre $15,000 y $20,000",
        "Más de $20,000"
    ]
    
    def __init__(self, parent=None, participant_data=None):
        super().__init__(parent)
        self.participant_data = participant_data
        self.setWindowTitle("Añadir Participante" if not participant_data else "Editar Participante")
        self.setup_ui()
        
        if participant_data:
            self.load_participant_data()
            
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Título
        title = QLabel(self.windowTitle())
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2C3E50;
                padding: 10px 0;
            }
        """)
        layout.addWidget(title)
        
        # Formulario principal
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(10)
        
        # Campos obligatorios
        required_label = QLabel("* Campos obligatorios")
        required_label.setStyleSheet("color: #E74C3C;")
        layout.addWidget(required_label)
        
        # Nombre
        self.name_input = QLineEdit()
        self.setup_required_field(self.name_input, "Nombre completo")
        form_layout.addRow(self.create_label("Nombre*:"), self.name_input)
        
        # Fecha de nacimiento
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setDisplayFormat("dd/MM/yyyy")
        self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setMaximumDate(QDate.currentDate())
        self.birth_date_input.setMinimumDate(QDate.currentDate().addYears(-100))
        form_layout.addRow(self.create_label("Fecha de Nacimiento*:"), self.birth_date_input)
        
        # Comunidad
        self.community_input = QComboBox()
        self.community_input.setEditable(True)
        self.community_input.addItems(["Comunidad 1", "Comunidad 2", "Otra..."])
        form_layout.addRow(self.create_label("Comunidad*:"), self.community_input)
        
        # Nivel educativo
        self.education_level = QComboBox()
        self.education_level.addItems(self.EDUCATION_LEVELS)
        form_layout.addRow(self.create_label("Nivel Educativo:"), self.education_level)
        
        # Género
        self.gender = QComboBox()
        self.gender.addItems(self.GENDER_OPTIONS)
        form_layout.addRow(self.create_label("Género:"), self.gender)
        
        # Nivel de ingresos
        self.income_level = QComboBox()
        self.income_level.addItems(self.INCOME_LEVELS)
        form_layout.addRow(self.create_label("Nivel de Ingresos:"), self.income_level)
        
        # Dependientes
        self.dependents = QSpinBox()
        self.dependents.setRange(0, 20)
        self.dependents.setSpecialValueText("Sin dependientes")
        form_layout.addRow(self.create_label("Dependientes:"), self.dependents)
        
        layout.addWidget(form_widget)
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancelar")
        self.save_button = QPushButton("Guardar")
        
        self.cancel_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        
        self.save_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)
        
        layout.addLayout(buttons_layout)
        
        # Conectar señales
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.save_participant)
        
        # Establecer tamaño mínimo
        self.setMinimumWidth(400)
        
    def create_label(self, text: str) -> QLabel:
        """Crea una etiqueta con estilo consistente"""
        label = QLabel(text)
        label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2C3E50;
            }
        """)
        return label
        
    def setup_required_field(self, widget, placeholder: str):
        """Configura un campo requerido con estilo y placeholder"""
        widget.setPlaceholderText(placeholder)
        widget.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
            }
        """)
        
    def load_participant_data(self):
        """Carga los datos del participante para edición"""
        if not self.participant_data:
            return
            
        self.name_input.setText(self.participant_data.get('name', ''))
        
        # Convertir fecha de string a QDate
        birth_date_str = self.participant_data.get('birth_date', '')
        if birth_date_str:
            try:
                date = datetime.strptime(birth_date_str, '%d/%m/%Y')
                self.birth_date_input.setDate(QDate(date.year, date.month, date.day))
            except ValueError:
                pass
        
        # Cargar resto de campos
        self.community_input.setCurrentText(self.participant_data.get('community', ''))
        
        education = self.participant_data.get('education_level', '')
        if education in self.EDUCATION_LEVELS:
            self.education_level.setCurrentText(education)
            
        gender = self.participant_data.get('gender', '')
        if gender in self.GENDER_OPTIONS:
            self.gender.setCurrentText(gender)
            
        income = self.participant_data.get('income_level', '')
        if income in self.INCOME_LEVELS:
            self.income_level.setCurrentText(income)
            
        self.dependents.setValue(self.participant_data.get('dependents', 0))
        
    def validate_inputs(self) -> bool:
        """Valida los campos requeridos"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Campo requerido", "Por favor ingrese el nombre del participante")
            self.name_input.setFocus()
            return False
            
        if not self.community_input.currentText().strip():
            QMessageBox.warning(self, "Campo requerido", "Por favor seleccione o ingrese una comunidad")
            self.community_input.setFocus()
            return False
            
        return True
        
    def save_participant(self):
        """Guarda los datos del participante"""
        if not self.validate_inputs():
            return
            
        # Crear diccionario con datos del participante
        participant_data = {
            'name': self.name_input.text().strip(),
            'birth_date': self.birth_date_input.date().toString("dd/MM/yyyy"),
            'community': self.community_input.currentText().strip(),
            'education_level': self.education_level.currentText(),
            'gender': self.gender.currentText(),
            'income_level': self.income_level.currentText(),
            'dependents': self.dependents.value()
        }
        
        self.participantAdded.emit(participant_data)
        self.accept()