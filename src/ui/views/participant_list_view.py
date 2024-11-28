# src/ui/views/participant_list_view.py

from datetime import datetime  
from PyQt6.QtWidgets import (
    QFileDialog, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QLabel, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from src.ui.dialogs.reports_dialog import ReportsDialog
from ..dialogs.add_participant_dialog import AddParticipantDialog
import logging
import matplotlib.pyplot as plt
from typing import List, Dict, Optional
from ..utils.export_manager import ExportManager
from src.ui.views.participant_filter_view import ParticipantFilterView



logger = logging.getLogger(__name__)
logger.debug(f"ImportPath: {ReportsDialog.__module__}")  # Al inicio del archivo, después de las importaciones

class ParticipantListView(QWidget):
    participant_selected = pyqtSignal(str)  # Señal cuando se selecciona un participante
    
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.current_activity_id: Optional[str] = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Crear el filtro antes de usarlo
        self.filter_view = ParticipantFilterView(self)
        self.filter_view.filtersChanged.connect(self.apply_filters)
        
        # Panel de exportación
        export_panel = QWidget()
        export_layout = QHBoxLayout(export_panel)

        self.export_csv_button = QPushButton("Exportar CSV")
        self.export_excel_button = QPushButton("Exportar Excel")
        self.export_pdf_button = QPushButton("Generar Reporte PDF")
        self.view_reports_button = QPushButton("Ver Reportes")

        self.export_csv_button.clicked.connect(self.export_to_csv)
        self.export_excel_button.clicked.connect(self.export_to_excel)
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        self.view_reports_button.clicked.connect(self.show_reports)

        export_layout.addWidget(self.export_csv_button)
        export_layout.addWidget(self.export_excel_button)
        export_layout.addWidget(self.export_pdf_button)
        export_layout.addWidget(self.view_reports_button)
        export_layout.addStretch()

        # Panel de acciones
        action_panel = QWidget()
        action_layout = QHBoxLayout(action_panel)
        
        self.add_button = QPushButton("Añadir Participante")
        self.edit_button = QPushButton("Editar")
        self.remove_button = QPushButton("Eliminar")
        
        self.add_button.clicked.connect(self.show_add_dialog)
        self.edit_button.clicked.connect(self.show_edit_dialog)
        self.remove_button.clicked.connect(self.remove_participant)
        
        self.edit_button.setEnabled(False)
        self.remove_button.setEnabled(False)
        
        action_layout.addWidget(self.add_button)
        action_layout.addWidget(self.edit_button)
        action_layout.addWidget(self.remove_button)
        action_layout.addStretch()
        
        # Tabla de participantes
        self.participants_table = QTableWidget()
        self.setup_table()
        
        # Añadir todo al layout principal en orden
        layout.addWidget(self.filter_view)
        layout.addWidget(export_panel)
        layout.addWidget(action_panel)
        layout.addWidget(self.participants_table)
        
        self.apply_styles()
        
    def setup_table(self):
        """Configurar la tabla de participantes"""
        self.participants_table.setColumnCount(7)
        self.participants_table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Comunidad", "Fecha de Nacimiento",
            "Género", "Nivel Educativo", "Estado"
        ])
        
        # Configurar comportamiento de la tabla
        self.participants_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.participants_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.participants_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Configurar header
        header = self.participants_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Nombre se estira
        
        # Conectar selección
        self.participants_table.itemSelectionChanged.connect(self.on_selection_changed)
        
    def apply_styles(self):
        """Aplicar estilos adicionales específicos"""
        # Los estilos base vienen de main.qss
        
        # Personalización específica para botones de acción
        self.export_csv_button.setProperty("class", "secondary")
        self.export_excel_button.setProperty("class", "secondary")
        self.export_pdf_button.setProperty("class", "secondary")
        self.view_reports_button.setProperty("class", "secondary")
        
        self.add_button.setProperty("class", "primary")
        self.edit_button.setProperty("class", "warning")
        self.remove_button.setProperty("class", "danger")
        
        # Estilo específico para la tabla
        self.participants_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QTableWidget::item:selected {
                background-color: #e8f5fe;
                color: #0088cc;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                border-right: 1px solid #e0e0e0;
                border-bottom: 1px solid #e0e0e0;
                font-weight: bold;
            }
        """)
        
    async def load_participants(self, activity_id: Optional[str] = None):
        try:
            self.current_activity_id = activity_id
            if activity_id:
                participants = await self.data_manager.get_activity_participants(activity_id)
            else:
                participants = await self.data_manager.get_all_participants()
                
            # Actualizar filtro de comunidades en ParticipantFilterView
            communities = sorted(set(p.get('community', '') for p in participants))
            self.filter_view.community_filter.clear()
            self.filter_view.community_filter.addItem("Todas las comunidades")
            self.filter_view.community_filter.addItems(communities)
            
            self.current_participants = participants
            self.update_table(participants)
                
        except Exception as e:
            logger.error(f"Error al cargar participantes: {e}")
            QMessageBox.warning(self, "Error", "No se pudieron cargar los participantes")
            
    def update_table(self, participants: List[Dict]):
        """Actualizar la tabla con los participantes proporcionados"""
        self.participants_table.setRowCount(len(participants))
        for i, participant in enumerate(participants):
            self.set_table_row(i, participant)
            
    def set_table_row(self, row: int, participant: Dict):
        """Establecer los datos de una fila de la tabla"""
        self.participants_table.setItem(row, 0, QTableWidgetItem(str(participant.get('id', ''))))
        self.participants_table.setItem(row, 1, QTableWidgetItem(participant.get('name', '')))
        self.participants_table.setItem(row, 2, QTableWidgetItem(participant.get('community', '')))
        self.participants_table.setItem(row, 3, QTableWidgetItem(
            participant.get('birth_date', 'N/A')
        ))
        self.participants_table.setItem(row, 4, QTableWidgetItem(participant.get('gender', '')))
        self.participants_table.setItem(row, 5, QTableWidgetItem(participant.get('education_level', '')))
        self.participants_table.setItem(row, 6, QTableWidgetItem('Activo'))  # Por defecto
            
    async def apply_filters(self, filters: dict):
        """Aplicar filtros avanzados a los participantes"""
        for row in range(self.participants_table.rowCount()):
            show_row = True
            
            # Nombre
            name = self.participants_table.item(row, 1).text().lower()
            if filters['name'] and filters['name'].lower() not in name:
                show_row = False
                
            # Comunidad
            community = self.participants_table.item(row, 2).text()
            if filters['community'] != "Todas las comunidades" and filters['community'] != community:
                show_row = False
                
            # Edad
            birth_date = self.participants_table.item(row, 3).text()
            age = self.calculate_age(birth_date)
            if not self.meets_age_criteria(age, filters['age_range']):
                show_row = False
                
            # Género
            gender = self.participants_table.item(row, 4).text()
            if filters['gender'] != "Todos" and filters['gender'] != gender:
                show_row = False
                
            # Educación
            education = self.participants_table.item(row, 5).text()
            if filters['education'] != "Todos" and filters['education'] != education:
                show_row = False
                
            self.participants_table.setRowHidden(row, not show_row)
            
    def on_selection_changed(self):
        """Manejar cambio en la selección de la tabla"""
        has_selection = len(self.participants_table.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.remove_button.setEnabled(has_selection)
        
        if has_selection:
            row = self.participants_table.currentRow()
            participant_id = self.participants_table.item(row, 0).text()
            self.participant_selected.emit(participant_id)
            
    async def show_add_dialog(self):
        """Mostrar diálogo para añadir participante"""
        dialog = AddParticipantDialog(self)
        dialog.participantAdded.connect(self.handle_participant_added)
        if dialog.exec():
            # La señal participantAdded manejará los datos
            pass
            
    async def show_edit_dialog(self):
        """Mostrar diálogo para editar participante"""
        row = self.participants_table.currentRow()
        if row >= 0:
            participant_id = self.participants_table.item(row, 0).text()
            try:
                participant_data = await self.data_manager.get_participant(participant_id)
                dialog = AddParticipantDialog(self, participant_data)
                dialog.participantAdded.connect(
                    lambda data: self.handle_participant_updated(participant_id, data)
                )
                dialog.exec()
            except Exception as e:
                logger.error(f"Error al cargar datos del participante: {e}")
                QMessageBox.warning(self, "Error", "No se pudo cargar el participante")
                
    async def remove_participant(self):
        """Eliminar participante seleccionado"""
        row = self.participants_table.currentRow()
        if row >= 0:
            participant_id = self.participants_table.item(row, 0).text()
            name = self.participants_table.item(row, 1).text()
            
            reply = QMessageBox.question(
                self,
                "Confirmar eliminación",
                f"¿Está seguro de eliminar a {name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    success = await self.data_manager.delete_participant(participant_id)
                    if success:
                        await self.load_participants(self.current_activity_id)
                    else:
                        raise Exception("No se pudo eliminar el participante")
                except Exception as e:
                    logger.error(f"Error al eliminar participante: {e}")
                    QMessageBox.warning(self, "Error", "No se pudo eliminar el participante")
                    
    async def handle_participant_added(self, participant_data: Dict):
        """Manejar la adición de un nuevo participante"""
        try:
            participant_id = await self.data_manager.add_participant(
                participant_data, 
                self.current_activity_id
            )
            if participant_id:
                await self.load_participants(self.current_activity_id)
                QMessageBox.information(self, "Éxito", "Participante añadido correctamente")
            else:
                raise Exception("No se pudo añadir el participante")
        except Exception as e:
            logger.error(f"Error al añadir participante: {e}")
            QMessageBox.warning(self, "Error", "No se pudo añadir el participante")
            
    async def handle_participant_updated(self, participant_id: str, participant_data: Dict):
        """Manejar la actualización de un participante"""
        try:
            success = await self.data_manager.update_participant(participant_id, participant_data)
            if success:
                await self.load_participants(self.current_activity_id)
                QMessageBox.information(self, "Éxito", "Participante actualizado correctamente")
            else:
                raise Exception("No se pudo actualizar el participante")
        except Exception as e:
            logger.error(f"Error al actualizar participante: {e}")
            QMessageBox.warning(self, "Error", "No se pudo actualizar el participante")

    async def export_to_csv(self):
        """Exportar datos de participantes a CSV"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar CSV",
                "",
                "CSV Files (*.csv)"
            )
            if filename:
                # Obtener datos actuales (no filtrados)
                participants = await self.data_manager.get_activity_participants(
                    self.current_activity_id
                ) if self.current_activity_id else await self.data_manager.get_all_participants()
                
                # Preparar datos para exportación
                export_data = [
                    {
                        "ID": p.get('id', ''),
                        "Nombre": p.get('name', ''),
                        "Comunidad": p.get('community', ''),
                        "Fecha de Nacimiento": p.get('birth_date', ''),
                        "Género": p.get('gender', ''),
                        "Nivel Educativo": p.get('education_level', ''),
                        "Estado": p.get('status', 'Activo'),
                        "Actividades": ", ".join(p.get('activities', []))
                    }
                    for p in participants
                ]
                
                ExportManager.export_to_csv(filename, export_data)
                QMessageBox.information(
                    self,
                    "Éxito",
                    "Datos exportados correctamente"
                )
                
        except Exception as e:
            logger.error(f"Error al exportar a CSV: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudieron exportar los datos: {str(e)}"
            )

    async def export_to_excel(self):
        """Exportar datos de participantes a Excel con estadísticas"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar Excel",
                "",
                "Excel Files (*.xlsx)"
            )
            if filename:
                # Obtener datos y generar estadísticas
                participants = await self.data_manager.get_activity_participants(
                    self.current_activity_id
                ) if self.current_activity_id else await self.data_manager.get_all_participants()
                
                # Generar gráficos
                charts = self._generate_charts(participants)
                
                # Preparar datos para exportación
                export_data = [
                    {
                        "ID": p.get('id', ''),
                        "Nombre": p.get('name', ''),
                        "Comunidad": p.get('community', ''),
                        "Fecha de Nacimiento": p.get('birth_date', ''),
                        "Género": p.get('gender', ''),
                        "Nivel Educativo": p.get('education_level', ''),
                        "Estado": p.get('status', 'Activo'),
                        "Actividades": ", ".join(p.get('activities', []))
                    }
                    for p in participants
                ]
                
                ExportManager.export_to_excel(filename, export_data, charts)
                QMessageBox.information(
                    self,
                    "Éxito",
                    "Datos exportados correctamente"
                )
                
        except Exception as e:
            logger.error(f"Error al exportar a Excel: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudieron exportar los datos: {str(e)}"
            )

    def _generate_charts(self, participants: List[Dict]) -> Dict:
        """Genera gráficos para el reporte"""
        charts = {}
        
        # Distribución por género
        plt.figure(figsize=(8, 6))
        gender_counts = {}
        for p in participants:
            gender = p.get('gender', 'No especificado')
            gender_counts[gender] = gender_counts.get(gender, 0) + 1
        plt.pie(gender_counts.values(), labels=gender_counts.keys(), autopct='%1.1f%%')
        plt.title('Distribución por Género')
        charts['gender_distribution'] = plt.gcf()
        plt.close()
        
        # Distribución por nivel educativo
        plt.figure(figsize=(10, 6))
        education_counts = {}
        for p in participants:
            edu = p.get('education_level', 'No especificado')
            education_counts[edu] = education_counts.get(edu, 0) + 1
        plt.bar(education_counts.keys(), education_counts.values())
        plt.xticks(rotation=45)
        plt.title('Distribución por Nivel Educativo')
        charts['education_distribution'] = plt.gcf()
        plt.close()
        
        return charts
    
    async def show_reports(self):
        """Muestra el diálogo de reportes"""
        dialog = ReportsDialog(self.data_manager, self)
        await dialog.load_initial_data()
        dialog.exec()

    async def export_to_pdf(self):
        """Exportar datos a PDF"""
        try:
            logger.debug("Iniciando exportación a PDF")
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar PDF",
                "",
                "PDF Files (*.pdf)"
            )
            logger.debug(f"Nombre de archivo seleccionado: {filename}")
            
            if filename:
                logger.debug("Obteniendo datos de participantes")
                participants = await self.data_manager.get_activity_participants(
                    self.current_activity_id
                ) if self.current_activity_id else await self.data_manager.get_all_participants()
                
                logger.debug(f"Datos obtenidos: {participants}")
                
                if not participants:
                    raise ValueError("No hay datos para exportar")
                    
                # Transformar los datos al formato que espera ExportManager
                export_data = [
                    {
                        "Participante": p.get('name', ''),
                        "Comunidad": p.get('community', ''),
                        "Actividad": p.get('activities', [''])[0] if p.get('activities') else '',
                        "Fecha": str(datetime.now().strftime("%Y-%m-%d")),  # Convertir a string
                        "Confianza": "100%",  # Añadir campo requerido
                        "Notas": ""  # Añadir campo requerido
                    }
                    for p in participants
                ]
                
                logger.debug(f"Datos formateados para export: {export_data}")
                ExportManager.export_to_pdf(filename, export_data)
                QMessageBox.information(self, "Éxito", "Datos exportados correctamente")
                
        except Exception as e:
            logger.error(f"Error al exportar a PDF: {e}", exc_info=True)  # Añadir exc_info para stack trace
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudieron exportar los datos: {str(e)}"
            )

    async def refresh_filters(self):
        """Actualiza los filtros con datos actuales"""
        if self.current_participants:
            communities = sorted(set(p.get('community', '') for p in self.current_participants))
            self.filter_view.community_filter.clear()
            self.filter_view.community_filter.addItem("Todas las comunidades")
            self.filter_view.community_filter.addItems(communities)

    def calculate_age(self, birth_date_str: str) -> Optional[int]:
        """Calcula edad desde fecha de nacimiento"""
        try:
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
            today = datetime.now()
            return today.year - birth_date.year
        except Exception as e:
            logger.error(f"Error calculando edad: {e}")
            return None

    def meets_age_criteria(self, age: Optional[int], age_range: str) -> bool:
        """Verifica si la edad cumple con el criterio de rango"""
        if age is None or age_range == "Todas las edades":
            return True
            
        ranges = {
            "18-25": (18, 25),
            "26-35": (26, 35),
            "36-50": (36, 50),
            "50+": (50, float('inf'))
        }
        
        if age_range in ranges:
            min_age, max_age = ranges[age_range]
            return min_age <= age <= max_age
        return True