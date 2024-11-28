# src/ui/views/participant_filter_view.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLineEdit, QComboBox, QDateEdit)
from PyQt6.QtCore import pyqtSignal, Qt
from datetime import datetime

class ParticipantFilterView(QWidget):
    filtersChanged = pyqtSignal(dict)  # Add this line at class level

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_initializing = True
        self.setup_ui()
        self.setup_initial_values()
        self.connect_signals()
        self._is_initializing = False

    def setup_initial_values(self):
        self.age_range.setCurrentText("Todas las edades")
        self.gender.setCurrentText("Todos")
        self.education.setCurrentText("Todos")
        self.community_filter.setCurrentText("Todas las comunidades")  # Añadir esta línea

    def _emit_filters(self):
        if self._is_initializing:
            return
            
        filters = {
            'name': self.name_filter.text(),
            'community': self.community_filter.currentText(),
            'age_range': self.age_range.currentText(),
            'gender': self.gender.currentText(),
            'education': self.education.currentText()
        }
        self.filtersChanged.emit(filters)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Basic filters
        self.name_filter = QLineEdit()
        self.name_filter.setPlaceholderText("Buscar por nombre...")
        
        self.community_filter = QComboBox()
        self.community_filter.setEditable(True)
        
        # Demographic filters
        filters_layout = QHBoxLayout()
        
        self.age_range = QComboBox()
        self.age_range.addItems(["Todas las edades", "18-25", "26-35", "36-50", "50+"])
        
        self.gender = QComboBox()
        self.gender.addItems(["Todos", "Masculino", "Femenino", "Otro"])
        
        self.education = QComboBox()
        self.education.addItems(["Todos", "Primaria", "Secundaria", "Preparatoria", "Universidad"])
        
        filters_layout.addWidget(self.age_range)
        filters_layout.addWidget(self.gender)
        filters_layout.addWidget(self.education)
        
        # Add to main layout
        layout.addWidget(self.name_filter)
        layout.addWidget(self.community_filter)
        layout.addLayout(filters_layout)

    def connect_signals(self):
        self.name_filter.textChanged.connect(self._emit_filters)
        self.community_filter.currentTextChanged.connect(self._emit_filters)
        self.age_range.currentTextChanged.connect(self._emit_filters)
        self.gender.currentTextChanged.connect(self._emit_filters) 
        self.education.currentTextChanged.connect(self._emit_filters)