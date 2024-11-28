# src/ui/views/activity_detail_view.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QMessageBox,
    QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime
from ..models.activity import Activity
from ..dialogs.activity_dialog import ActivityDialog


class ActivityDetailView(QWidget):
    activity_updated = pyqtSignal(Activity)  # Emitida cuando se actualiza la actividad
    activity_deleted = pyqtSignal(str)      # Emitida cuando se elimina la actividad
    
    def __init__(self, activity: Activity, parent=None):
        super().__init__(parent)
        self.activity = activity
        self.setup_ui()
        self.update_activity_data()

    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.setup_header()
        
        # Contenido principal (scrolleable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        
        self.setup_info_section()
        self.setup_participants_section()
        self.setup_survey_section()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def setup_header(self):
        """Configurar la sección de encabezado"""
        header = QWidget()
        header.setStyleSheet("background-color: #ffffff;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # Título y tipo
        title_layout = QVBoxLayout()
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.type_label = QLabel()
        self.type_label.setStyleSheet("color: #666666;")
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.type_label)
        
        header_layout.addLayout(title_layout, stretch=1)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.edit_btn = QPushButton("Editar")
        self.edit_btn.clicked.connect(self.on_edit_clicked)
        buttons_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Eliminar")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        buttons_layout.addWidget(self.delete_btn)
        
        header_layout.addLayout(buttons_layout)
        
        # Agregar header al layout principal
        self.layout().addWidget(header)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #e0e0e0;")
        self.layout().addWidget(separator)

    def setup_info_section(self):
        """Configurar la sección de información general"""
        info_widget = QWidget()
        info_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
            }
        """)
        info_layout = QVBoxLayout(info_widget)
        
        # Título de la sección
        section_title = QLabel("Información General")
        section_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        info_layout.addWidget(section_title)
        
        # Grid para la información
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # Labels
        self.location_label = QLabel()
        self.start_date_label = QLabel()
        self.end_date_label = QLabel()
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        
        # Agregar al grid
        labels = [
            ("Ubicación:", self.location_label),
            ("Fecha de inicio:", self.start_date_label),
            ("Fecha de fin:", self.end_date_label),
            ("Descripción:", self.description_label)
        ]
        
        for i, (title, label) in enumerate(labels):
            title_label = QLabel(title)
            title_label.setStyleSheet("font-weight: bold; color: #666;")
            grid.addWidget(title_label, i, 0)
            grid.addWidget(label, i, 1)
        
        info_layout.addLayout(grid)
        info_layout.addStretch()
        
        self.content_layout.addWidget(info_widget)

    def setup_participants_section(self):
        """Configurar la sección de participantes"""
        participants_widget = QWidget()
        participants_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
            }
        """)
        participants_layout = QVBoxLayout(participants_widget)
        
        # Header de la sección
        header_layout = QHBoxLayout()
        section_title = QLabel("Participantes")
        section_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        header_layout.addWidget(section_title)
        
        self.participant_count_label = QLabel()
        self.participant_count_label.setStyleSheet("color: #666;")
        header_layout.addWidget(self.participant_count_label)
        
        header_layout.addStretch()
        
        add_participant_btn = QPushButton("Añadir Participante")
        header_layout.addWidget(add_participant_btn)
        
        participants_layout.addLayout(header_layout)
        
        # Lista de participantes (placeholder)
        self.participants_list = QLabel("Lista de participantes se implementará próximamente")
        self.participants_list.setAlignment(Qt.AlignmentFlag.AlignCenter)
        participants_layout.addWidget(self.participants_list)
        
        self.content_layout.addWidget(participants_widget)

    def setup_survey_section(self):
        """Configurar la sección de encuestas"""
        survey_widget = QWidget()
        survey_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
            }
        """)
        survey_layout = QVBoxLayout(survey_widget)
        
        # Header de la sección
        header_layout = QHBoxLayout()
        section_title = QLabel("Encuestas")
        section_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        header_layout.addWidget(section_title)
        
        header_layout.addStretch()
        
        process_surveys_btn = QPushButton("Procesar Encuestas")
        header_layout.addWidget(process_surveys_btn)
        
        survey_layout.addLayout(header_layout)
        
        # Información de encuestas (placeholder)
        self.survey_info = QLabel("Información de encuestas se implementará próximamente")
        self.survey_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        survey_layout.addWidget(self.survey_info)
        
        self.content_layout.addWidget(survey_widget)

    def update_activity_data(self):
        """Actualizar la interfaz con los datos de la actividad"""
        self.title_label.setText(self.activity.name)
        self.type_label.setText(f"Tipo: {self.activity.survey_template.type.value}")
        
        # Actualizar información general
        self.location_label.setText(self.activity.location)
        self.start_date_label.setText(self.activity.start_date.strftime("%d/%m/%Y"))
        
        if self.activity.end_date:
            self.end_date_label.setText(self.activity.end_date.strftime("%d/%m/%Y"))
        else:
            self.end_date_label.setText("No especificada")
            
        self.description_label.setText(self.activity.description or "Sin descripción")
        
        # Actualizar contador de participantes
        count = len(self.activity.participant_ids)
        self.participant_count_label.setText(f"Total: {count}")

    def on_edit_clicked(self):
        """Manejador para el botón de editar"""
        dialog = ActivityDialog(self, activity=self.activity)
        if dialog.exec():
            updated_activity = dialog.get_activity_data()
            self.activity = updated_activity
            self.update_activity_data()
            self.activity_updated.emit(updated_activity)

    def on_delete_clicked(self):
        """Manejador para el botón de eliminar"""
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Estás seguro de que deseas eliminar la actividad '{self.activity.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.activity_deleted.emit(str(self.activity))