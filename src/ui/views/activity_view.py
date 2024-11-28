# src/ui/views/activity_view.py

from PyQt6.QtWidgets import (QListWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QListWidget, QLabel, QFrame, QSplitter, QTableWidget,
                           QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from ..dialogs.activity_dialog import ActivityDialog
from ..dialogs.add_participant_dialog import AddParticipantDialog
from ..models.activity import Activity, SurveyTemplate
from ..dialogs.generate_survey_dialog import GenerateSurveyDialog
from ..dialogs.process_surveys_dialog import ProcessSurveysDialog
import asyncio
from typing import Optional, Dict, List, Tuple
import logging
from PyQt6.QtGui import QFont, QColor, QPalette
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QLineEdit, QComboBox, QToolButton, QDateEdit
)
from PyQt6.QtCore import QDate
from PyQt6.QtCore import QTimer
from functools import partial
from PyQt6.QtWidgets import QListWidgetItem, QMenu, QApplication
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction
from datetime import datetime
import logging

import logging
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

logger = logging.getLogger(__name__)

class ActivityView(QWidget):
    activity_selected = pyqtSignal(str)  # Señal cuando se selecciona una actividad

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.current_activity_id: Optional[str] = None
        self._setup_async_handler()
        self.setup_ui()
        self.load_styles()
        
        # Obtener el event loop actual
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self.load_activities())
        except RuntimeError:
            logger.warning("No se pudo obtener el event loop")

    def _setup_async_handler(self):
        """Configura el manejador de eventos asíncronos"""
        self._async_callbacks = {}

    async def _run_async(self, coro, callback=None):
        """Ejecuta una corutina y opcionalmente llama a un callback con el resultado"""
        try:
            result = await coro
            if callback:
                callback(result)
            return result
        except Exception as e:
            logger.error(f"Error en operación asíncrona: {e}")
            QMessageBox.critical(self, "Error", str(e))
        return None
    
    def _create_async_button(self, text: str, coro_func, callback=None, 
                       error_msg="Error en la operación"):
        """Crea un botón que ejecuta una corutina de manera segura"""
        button = QPushButton(text)
        
        async def _handle_click():
            try:
                result = await coro_func()
                if callback:
                    callback(result)
            except Exception as e:
                logger.error(f"{error_msg}: {e}")
                QMessageBox.critical(self, "Error", f"{error_msg}: {str(e)}")
                
        button.clicked.connect(
            lambda: asyncio.create_task(_handle_click())
        )
        return button

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Panel izquierdo: Lista de actividades
        left_panel = QWidget()
        left_panel.setObjectName("leftPanel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Panel de búsqueda y filtros
        search_panel = self.setup_search_panel()
        left_layout.addWidget(search_panel)
        
        # Botones de gestión de actividades
        button_layout = QHBoxLayout()
        # src/ui/views/activity_view.py
        # En el método setup_ui, reemplazar la creación de botones existente con:

        # Botones de actividades
        self.add_activity_btn = self._create_async_button(
            "Nueva Actividad",
            self.show_add_activity_dialog,
            error_msg="Error al crear actividad"
        )

        self.edit_activity_btn = self._create_async_button(
            "Editar",
            self.show_edit_activity_dialog,
            error_msg="Error al editar actividad"
        )

        self.delete_activity_btn = self._create_async_button(
            "Eliminar",
            self.delete_current_activity,
            error_msg="Error al eliminar actividad"
        )

        # Botones de participantes
        self.add_participant_btn = self._create_async_button(
            "Añadir Participante",
            self.show_add_participant_dialog,
            error_msg="Error al añadir participante"
        )

        self.remove_participant_btn = self._create_async_button(
            "Eliminar Participante",
            self.remove_selected_participant,
            error_msg="Error al eliminar participante"
        )

        
        button_layout.addWidget(self.add_activity_btn)
        button_layout.addWidget(self.edit_activity_btn)
        button_layout.addWidget(self.delete_activity_btn)
        left_layout.addLayout(button_layout)
        
        # Lista de actividades
        self.activities_list = QListWidget()
        self.activities_list.setObjectName("activitiesList")
        # En setup_ui() después de crear activities_list
        self.activities_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.activities_list.customContextMenuRequested.connect(self.show_context_menu)
        
        left_layout.addWidget(self.activities_list)
        
        # Panel derecho: Detalles de actividad y participantes
        right_panel = QWidget()
        right_panel.setObjectName("rightPanel")
        right_layout = QVBoxLayout(right_panel)
        
        # Información de la actividad
        self.activity_info = QLabel("Selecciona una actividad")
        self.activity_info.setObjectName("activityTitle")
        right_layout.addWidget(self.activity_info)
        
        # Tabla de participantes
        self.participants_table = QTableWidget()
        self.setup_participants_table()
        right_layout.addWidget(self.participants_table)
        
        # Botones de gestión de participantes
        self.participants_button_layout = QHBoxLayout()
        self.add_participant_btn = QPushButton("Añadir Participante")
        self.remove_participant_btn = QPushButton("Eliminar Participante")
        self.generate_surveys_btn = QPushButton("Generar Encuestas")
        self.process_surveys_btn = QPushButton("Procesar Encuestas")
        
        self.generate_surveys_btn.setEnabled(False)
        self.process_surveys_btn.setEnabled(False)
        
        self.participants_button_layout.addWidget(self.add_participant_btn)
        self.participants_button_layout.addWidget(self.remove_participant_btn)
        self.participants_button_layout.addWidget(self.generate_surveys_btn)
        self.participants_button_layout.addWidget(self.process_surveys_btn)
        right_layout.addLayout(self.participants_button_layout)
        
        # Configurar splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])  # Tamaños iniciales
        main_layout.addWidget(splitter)
        
        # Conectar señales
        self.connect_signals()
        
        # Deshabilitar botones inicialmente
        self.toggle_activity_buttons(False)
        self.toggle_participant_buttons(False)


    async def show_process_surveys_dialog(self):
        """Muestra el diálogo para procesar encuestas"""
        if not self.current_activity_id:
            return

        try:
            # Obtener datos necesarios
            activity = await self.data_manager.get_activity(self.current_activity_id)
            if not activity:
                raise Exception("No se pudo obtener la información de la actividad")

            participants = await self.data_manager.get_activity_participants(self.current_activity_id)
            if not participants:
                QMessageBox.warning(
                    self,
                    "Advertencia",
                    "No hay participantes en esta actividad"
                )
                return

            # Mostrar diálogo
            dialog = ProcessSurveysDialog(self.current_activity_id, self)
            dialog.surveys_processed.connect(self.on_surveys_processed)
            await dialog.exec()

        except Exception as e:
            logger.error(f"Error al preparar generación de encuestas: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al preparar la generación de encuestas: {str(e)}"
            )

    async def on_surveys_processed(self, results):
        """Maneja los resultados del procesamiento de encuestas"""
        try:
            logger.info(f"Procesadas {len(results)} encuestas")
            await self.load_activity_details(self.current_activity_id)
        except Exception as e:
            logger.error(f"Error al manejar resultados OCR: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al guardar resultados: {str(e)}"
            )

    async def on_surveys_processed(self, results: List[Dict]):
        """Maneja los resultados del procesamiento OCR"""
        try:
            # Aquí implementaremos la lógica para guardar los resultados
            logger.info(f"Procesadas {len(results)} encuestas")
            
            # Actualizar la interfaz si es necesario
            await self.load_activity_details(self.current_activity_id)
            
        except Exception as e:
            logger.error(f"Error al manejar resultados OCR: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al guardar resultados: {str(e)}"
            )

    def setup_participants_table(self):
        """Configura la tabla de participantes"""
        self.participants_table.setColumnCount(4)
        self.participants_table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Fecha de Nacimiento", "Estado"
        ])
        header = self.participants_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    def add_participant(self):
        """Método temporal para añadir participantes"""
        logger.info("Añadiendo participante...")
        # Implementación temporal
        pass

    def remove_participant(self):
        """Método temporal para eliminar participantes"""
        logger.info("Eliminando participante...")
        # Implementación temporal
        pass

    def connect_signals(self):
        """Conecta las señales de los widgets"""
        # Conexiones básicas de actividades
        self.add_activity_btn.clicked.connect(self.show_add_activity_dialog)
        self.edit_activity_btn.clicked.connect(self.show_edit_activity_dialog)
        self.delete_activity_btn.clicked.connect(self.delete_current_activity)
        self.activities_list.itemClicked.connect(self.on_activity_selected)

        # Conexiones para participantes y encuestas
        if hasattr(self, 'add_participant_btn'):
            self.add_participant_btn.clicked.connect(self.add_participant)
        if hasattr(self, 'remove_participant_btn'):
            self.remove_participant_btn.clicked.connect(self.remove_participant)
        if hasattr(self, 'generate_surveys_btn'):
            self.generate_surveys_btn.clicked.connect(self.show_generate_surveys_dialog)
        if hasattr(self, 'process_surveys_btn'):
            self.process_surveys_btn.clicked.connect(self.show_process_surveys_dialog)

    async def load_activities(self):
        """Carga las actividades desde la base de datos"""
        try:
            activities = await self.data_manager.get_all_activities()
            self.activities_list.clear()

            # Mostrar mensaje cuando no hay actividades
            if not activities:
                empty_label = QLabel("No hay actividades registradas")
                empty_label.setObjectName("emptyLabel")  # Agregar esta línea
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                empty_item = QListWidgetItem()
                empty_item.setSizeHint(empty_label.sizeHint())
                
                self.activities_list.addItem(empty_item)
                self.activities_list.setItemWidget(empty_item, empty_label)
            else:
                # Ordenar actividades por fecha
                activities.sort(
                    key=lambda x: x.get('start_date', datetime.now()), 
                    reverse=True
                )
                
                for activity in activities:
                    item = ActivityListItem(activity)
                    self.activities_list.addItem(item)
                    
        except Exception as e:
            logger.error(f"Error al cargar actividades: {e}")
            QMessageBox.warning(self, "Error", "No se pudieron cargar las actividades")

    
    async def show_add_participant_dialog(self):
        """Muestra el diálogo para añadir participantes"""
        if not self.current_activity_id:
            return
            
        try:
            dialog = AddParticipantDialog(self)
            if dialog.exec():
                participant_data = dialog.get_participant_data()
                success = await self.data_manager.add_participant(
                    self.current_activity_id,
                    participant_data
                )
                if success:
                    await self.load_activity_details(self.current_activity_id)
                    QMessageBox.information(
                        self,
                        "Éxito",
                        "Participante añadido correctamente"
                    )
                else:
                    raise Exception("No se pudo añadir el participante")
                    
        except Exception as e:
            logger.error(f"Error al añadir participante: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al añadir participante: {str(e)}"
            )

    async def remove_selected_participant(self):
        """Elimina el participante seleccionado"""
        if not self.current_activity_id:
            return
            
        selected_items = self.participants_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "Advertencia",
                "Por favor, selecciona un participante"
            )
            return
            
        try:
            participant_id = selected_items[0].text()
            confirm = QMessageBox.question(
                self,
                "Confirmar eliminación",
                "¿Estás seguro de eliminar este participante?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.Yes:
                success = await self.data_manager.remove_participant(
                    self.current_activity_id,
                    participant_id
                )
                if success:
                    await self.load_activity_details(self.current_activity_id)
                    QMessageBox.information(
                        self,
                        "Éxito",
                        "Participante eliminado correctamente"
                    )
                else:
                    raise Exception("No se pudo eliminar el participante")
                    
        except Exception as e:
            logger.error(f"Error al eliminar participante: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al eliminar participante: {str(e)}"
            )


    def _update_interface_state(self, has_activity: bool):
        """Actualiza el estado de la interfaz según si hay una actividad seleccionada"""
        self.edit_activity_btn.setEnabled(has_activity)
        self.delete_activity_btn.setEnabled(has_activity)
        self.add_participant_btn.setEnabled(has_activity)
        self.remove_participant_btn.setEnabled(has_activity)
        self.generate_surveys_btn.setEnabled(has_activity)
        self.process_surveys_btn.setEnabled(has_activity)

    async def show_add_activity_dialog(self):
        """Muestra el diálogo para añadir una nueva actividad"""
        dialog = ActivityDialog(self)
        if dialog.exec():
            try:
                activity_data = dialog.get_activity_data()
                activity_id = await self.data_manager.insert_activity(activity_data.to_dict())
                if activity_id:
                    await self.load_activities()
                    QMessageBox.information(self, "Éxito", "Actividad creada correctamente")
                else:
                    raise Exception("No se pudo crear la actividad")
            except Exception as e:
                logger.error(f"Error al crear actividad: {e}")
                QMessageBox.warning(self, "Error", "No se pudo crear la actividad")

    async def show_edit_activity_dialog(self):
        """Muestra el diálogo para editar una actividad existente"""
        if not self.current_activity_id:
            return

        try:
            activity_data = await self.data_manager.get_activity(self.current_activity_id)
            if not activity_data:
                raise Exception("No se encontró la actividad")

            activity = Activity.from_dict(activity_data)
            dialog = ActivityDialog(self, activity)
            
            if dialog.exec():
                updated_activity = dialog.get_activity_data()
                success = await self.data_manager.update_activity(
                    self.current_activity_id, 
                    updated_activity.to_dict()
                )
                if success:
                    await self.load_activities()
                    await self.load_activity_details(self.current_activity_id)
                    QMessageBox.information(self, "Éxito", "Actividad actualizada correctamente")
                else:
                    raise Exception("No se pudo actualizar la actividad")
        except Exception as e:
            logger.error(f"Error al editar actividad: {e}")
            QMessageBox.warning(self, "Error", "No se pudo editar la actividad")

    async def delete_current_activity(self):
        """Elimina la actividad actual"""
        if not self.current_activity_id:
            return

        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            "¿Estás seguro de que quieres eliminar esta actividad?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = await self.data_manager.delete_activity(self.current_activity_id)
                if success:
                    self.current_activity_id = None
                    await self.load_activities()
                    self.clear_activity_details()
                    QMessageBox.information(self, "Éxito", "Actividad eliminada correctamente")
                else:
                    raise Exception("No se pudo eliminar la actividad")
            except Exception as e:
                logger.error(f"Error al eliminar actividad: {e}")
                QMessageBox.warning(self, "Error", "No se pudo eliminar la actividad")

    async def on_activity_selected(self, item):
        """Maneja la selección de una actividad"""
        try:
            if not item:
                return
                
            activities = await self.data_manager.get_all_activities()
            selected_idx = self.activities_list.row(item)
            
            if 0 <= selected_idx < len(activities):
                activity_id = str(activities[selected_idx].get("_id", ""))
                self.current_activity_id = activity_id
                
                # Cargar detalles y actualizar UI
                activity_data = await self.data_manager.get_activity(activity_id)
                participants = await self.data_manager.get_activity_participants(activity_id)
                
                if activity_data:
                    self.activity_info.setText(
                        f"Actividad: {activity_data.get('name', 'Sin nombre')}\n"
                        f"Ubicación: {activity_data.get('location', 'Sin ubicación')}\n"
                        f"Fecha inicio: {activity_data.get('start_date', datetime.now()).strftime('%d/%m/%Y')}"
                    )
                    await self.update_participants_table(participants)
                    self._update_interface_state(True)
                else:
                    raise ValueError("No se pudieron cargar los detalles de la actividad")
                    
        except Exception as e:
            logger.error(f"Error al seleccionar actividad: {e}")
            QMessageBox.warning(self, "Error", "No se pudo cargar los detalles de la actividad")
            self._update_interface_state(False)

    async def load_activity_details(self, activity_id: str):
        """Carga los detalles de una actividad"""
        try:
            activity_data = await self.data_manager.get_activity(activity_id)
            if not activity_data:
                raise Exception("No se encontró la actividad")

            # Actualizar información de la actividad
            activity = Activity.from_dict(activity_data)
            self.activity_info.setText(
                f"Actividad: {activity.name}\n"
                f"Ubicación: {activity.location}\n"
                f"Fecha inicio: {activity.start_date.strftime('%d/%m/%Y')}"
            )

            # Cargar participantes
            participants = await self.data_manager.get_activity_participants(activity_id)
            self.update_participants_table(participants)
        except Exception as e:
            logger.error(f"Error al cargar detalles de actividad: {e}")
            self.clear_activity_details()

    def clear_activity_details(self):
        """Limpia los detalles de la actividad"""
        self.activity_info.setText("Selecciona una actividad")
        self.participants_table.setRowCount(0)
        self.toggle_activity_buttons(False)
        self.toggle_participant_buttons(False)

    def toggle_activity_buttons(self, enabled: bool):
        """Habilita/deshabilita los botones de gestión de actividades"""
        self.edit_activity_btn.setEnabled(enabled)
        self.delete_activity_btn.setEnabled(enabled)

    def toggle_participant_buttons(self, enabled: bool):
        """Habilita/deshabilita los botones de gestión de participantes"""
        self.add_participant_btn.setEnabled(enabled)
        self.remove_participant_btn.setEnabled(enabled)

    async def update_participants_table(self, participants: List[Dict]):
        """Actualiza la tabla de participantes"""
        self.participants_table.setRowCount(len(participants))
        for i, participant in enumerate(participants):
            try:
                self.participants_table.setItem(i, 0, QTableWidgetItem(str(participant.get("_id", ""))))
                self.participants_table.setItem(i, 1, QTableWidgetItem(participant.get("name", "")))
                self.participants_table.setItem(i, 2, QTableWidgetItem(
                    participant.get("birth_date", datetime.now()).strftime("%d/%m/%Y") 
                    if participant.get("birth_date") else "N/A"
                ))
                self.participants_table.setItem(i, 3, QTableWidgetItem(participant.get("status", "Activo")))
            except Exception as e:
                logger.error(f"Error al actualizar fila {i}: {e}")
                continue

    def show_generate_surveys_dialog(self):
        """Muestra el diálogo para generar encuestas"""
        if not self.current_activity_id:
            return

        try:
            # Obtener datos necesarios
            activity = self.data_manager.get_activity(self.current_activity_id)
            if not activity:
                raise Exception("No se pudo obtener la información de la actividad")

            participants = self.data_manager.get_activity_participants(self.current_activity_id)
            if not participants:
                QMessageBox.warning(
                    self,
                    "Advertencia",
                    "No hay participantes en esta actividad"
                )
                return

            # Mostrar diálogo
            dialog = GenerateSurveyDialog(activity, participants, self)
            dialog.surveys_generated.connect(self.on_surveys_generated)
            dialog.exec()

        except Exception as e:
            logger.error(f"Error al preparar generación de encuestas: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al preparar la generación de encuestas: {str(e)}"
            )

    def setup_search_panel(self):
        """Configura el panel de búsqueda y filtros"""
        search_panel = QWidget()
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(8, 8, 8, 8)
        
        # Barra de búsqueda con delay
        self.search_bar = SearchBar()
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(lambda: asyncio.create_task(self.filter_activities()))
        self.search_bar.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_bar)
        
        # Filtros
        filter_layout = QHBoxLayout()
        
        # Filtro de estado
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "Todas",
            "Activas",
            "Pendientes",
            "Completadas"
        ])
        self.status_filter.currentTextChanged.connect(
            lambda: asyncio.create_task(self.filter_activities())
        )
        
        # Filtro de fecha
        self.date_filter = QComboBox()
        self.date_filter.addItems([
            "Todas las fechas",
            "Hoy",
            "Esta semana",
            "Este mes",
            "Personalizado..."
        ])
        self.date_filter.currentTextChanged.connect(self.on_date_filter_changed)
        
        # Fechas personalizadas
        self.date_from = QDateEdit()
        self.date_to = QDateEdit()
        self.date_from.setDate(QDate.currentDate())
        self.date_to.setDate(QDate.currentDate())
        self.date_from.dateChanged.connect(
            lambda: asyncio.create_task(self.filter_activities())
        )
        self.date_to.dateChanged.connect(
            lambda: asyncio.create_task(self.filter_activities())
        )
        self.date_from.hide()
        self.date_to.hide()
        
        filter_layout.addWidget(QLabel("Estado:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(QLabel("Fecha:"))
        filter_layout.addWidget(self.date_filter)
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(self.date_to)
        
        search_layout.addLayout(filter_layout)
        
        return search_panel
    
    def on_search_changed(self):
        """Maneja los cambios en la búsqueda con delay"""
        self.search_timer.stop()
        self.search_timer.start(300)  # 300ms delay



    def on_surveys_generated(self, output_dir: str):
        """Manejador para cuando se generan las encuestas exitosamente"""
        logger.info(f"Encuestas generadas en: {output_dir}")
        # Aquí puedes añadir lógica adicional si es necesario

    # activity_view.py

    def on_activity_selected(self, item):
        """Maneja la selección de una actividad de forma no asíncrona"""
        if not item:
            return
        # Usar un método separado para la lógica asíncrona
        asyncio.create_task(self._handle_activity_selection(item))

    async def _handle_activity_selection(self, item):
        """Maneja la lógica asíncrona de la selección de actividad"""
        try:
            activities = await self.data_manager.get_all_activities()
            selected_idx = self.activities_list.row(item)
            
            if 0 <= selected_idx < len(activities):
                activity_id = str(activities[selected_idx].get("_id", ""))
                self.current_activity_id = activity_id
                
                activity_data = await self.data_manager.get_activity(activity_id)
                participants = await self.data_manager.get_activity_participants(activity_id)
                
                if activity_data:
                    self.activity_info.setText(
                        f"Actividad: {activity_data.get('name', 'Sin nombre')}\n"
                        f"Ubicación: {activity_data.get('location', 'Sin ubicación')}\n"
                        f"Fecha inicio: {activity_data.get('start_date', datetime.now()).strftime('%d/%m/%Y')}"
                    )
                    await self.update_participants_table(participants)
                    self._update_interface_state(True)
                else:
                    raise ValueError("No se pudieron cargar los detalles de la actividad")
                    
        except Exception as e:
            logger.error(f"Error al seleccionar actividad: {e}")
            QMessageBox.warning(self, "Error", "No se pudo cargar los detalles de la actividad")
            self._update_interface_state(False)

    def clear_activity_details(self):
        """(Actualizar método existente)"""
        # (Mantener código existente)
        self.generate_surveys_btn.setEnabled(False)  # Deshabilitar botón

    
    async def filter_activities(self):
        """Filtra las actividades según los criterios actuales"""
        try:
            search_text = self.search_bar.text().lower()
            status = self.status_filter.currentText()
            
            # Construir filtros
            filters = {}
            
            # Filtro de estado
            if status != "Todas":
                filters["status"] = status[:-1].lower()  # Remover 's' final
                
            # Filtro de fecha
            date_filter = self.check_date_filter()
            if date_filter:
                filters["date_range"] = date_filter
            
            # Obtener y filtrar actividades
            activities = await self.data_manager.get_all_activities()
            filtered_activities = []
            
            for activity in activities:
                # Filtro de texto
                if search_text:
                    name_match = search_text in activity['name'].lower()
                    location_match = search_text in activity.get('location', '').lower()
                    if not (name_match or location_match):
                        continue
                
                # Filtro de estado
                if "status" in filters and activity.get('status') != filters["status"]:
                    continue
                    
                # Filtro de fecha
                if "date_range" in filters:
                    start_date, end_date = filters["date_range"]
                    activity_date = activity.get('start_date')
                    if not (start_date <= activity_date <= end_date):
                        continue
                
                filtered_activities.append(activity)
            
            # Actualizar lista
            self.activities_list.clear()
            for activity in filtered_activities:
                item = ActivityListItem(activity)
                self.activities_list.addItem(item)
                
        except Exception as e:
            logger.error(f"Error al filtrar actividades: {e}")

    def check_date_filter(self) -> Optional[Tuple[datetime, datetime]]:
        """Obtiene el rango de fechas según el filtro seleccionado"""
        filter_text = self.date_filter.currentText()
        
        if filter_text == "Todas las fechas":
            return None
            
        now = datetime.now()
        
        if filter_text == "Hoy":
            start = now.replace(hour=0, minute=0, second=0)
            end = now.replace(hour=23, minute=59, second=59)
            return (start, end)
            
        if filter_text == "Esta semana":
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0)
            return (start, now)
            
        if filter_text == "Este mes":
            start = now.replace(day=1, hour=0, minute=0, second=0)
            return (start, now)
            
        if filter_text == "Personalizado...":
            start = self.date_from.date().toPyDate()
            end = self.date_to.date().toPyDate()
            return (
                datetime.combine(start, datetime.min.time()),
                datetime.combine(end, datetime.max.time())
            )
        
        return None

    def sort_activities_list(self, activities: List[Dict]):
        """Ordena la lista de actividades según el criterio seleccionado"""
        sort_option = self.sort_combo.currentText()
        
        if sort_option == "Más recientes":
            activities.sort(key=lambda x: x.get('start_date', datetime.now()), reverse=True)
        elif sort_option == "Más antiguos":
            activities.sort(key=lambda x: x.get('start_date', datetime.now()))
        elif sort_option == "Nombre A-Z":
            activities.sort(key=lambda x: x['name'].lower())
        elif sort_option == "Nombre Z-A":
            activities.sort(key=lambda x: x['name'].lower(), reverse=True)
        elif sort_option == "Más participantes":
            activities.sort(key=lambda x: len(x.get('participant_ids', [])), reverse=True)
        elif sort_option == "Menos participantes":
            activities.sort(key=lambda x: len(x.get('participant_ids', [])))

    def on_date_filter_changed(self, filter_text: str):
        """Maneja cambios en el filtro de fecha"""
        show_custom = filter_text == "Personalizado..."
        self.date_from.setVisible(show_custom)
        self.date_to.setVisible(show_custom)
        asyncio.create_task(self.filter_activities())

    def load_styles(self):
        """Carga los estilos QSS"""
        try:
            style_path = "src/ui/styles/activity_view.qss"
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            logger.error(f"Error al cargar estilos: {e}")

    def show_context_menu(self, position):
        """Muestra el menú contextual para el item seleccionado"""
        try:
            item = self.activities_list.itemAt(position)
            if isinstance(item, ActivityListItem):
                menu = item.get_context_menu(self)
                if menu:
                    # Mapear la posición al widget
                    global_pos = self.activities_list.mapToGlobal(position)
                    selected_action = menu.exec(global_pos)
                    
                    # Manejar la acción seleccionada
                    if selected_action:
                        action_text = selected_action.text()
                        if "Editar" in action_text:
                            asyncio.create_task(self.show_edit_activity_dialog())
                        elif "Eliminar" in action_text:
                            asyncio.create_task(self.delete_current_activity())
                        elif "Generar encuestas" in action_text:
                            self.show_generate_surveys_dialog()
                        elif "Procesar encuestas" in action_text:
                            asyncio.create_task(self.show_process_surveys_dialog())
                        # ... manejar otras acciones según sea necesario
                        
        except Exception as e:
            logger.error(f"Error al mostrar menú contextual: {e}")


# Agregar después de los imports existentes en activity_view.py
class ActivityListItem(QListWidgetItem):
    """Elemento personalizado para la lista de actividades"""
    def __init__(self, activity: dict, parent=None):
        super().__init__()
        self.activity = activity
        self.setup_item()
        self.setup_tooltip()
        
    def setup_item(self):
        """Configura la apariencia del item"""
        try:
            # Formatear fecha y hora
            start_date = self.activity.get('start_date', datetime.now())
            date_str = start_date.strftime("%d/%m/%Y")
            time_str = start_date.strftime("%H:%M")
            
            # Determinar estado y su color
            status = self.activity.get('status', 'pending')
            status_colors = {
                'active': '#25d366',    # Verde WhatsApp
                'pending': '#ffc107',    # Amarillo
                'completed': '#128c7e',  # Verde oscuro WhatsApp
                'cancelled': '#dc3545'   # Rojo
            }
            status_color = status_colors.get(status, '#6c757d')
            
            # Formatear participantes
            participant_count = len(self.activity.get('participant_ids', []))
            max_participants = self.activity.get('max_participants', 0)
            participants_text = (f"{participant_count}/{max_participants}" 
                               if max_participants else str(participant_count))
            
            # Indicador de encuestas y última actualización
            has_pending_surveys = not self.activity.get('surveys_ready', False)
            survey_indicator = "🔴" if has_pending_surveys else "✅"
            updated_at = self.activity.get('updated_at', start_date)
            last_update = updated_at.strftime("%d/%m/%Y %H:%M")
            
            # Crear HTML con mejor formato
            display_text = f"""
                <div style='padding: 12px; display: flex; flex-direction: column;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <span style='font-size: 15px; font-weight: bold; color: #075e54;'>
                            {self.activity.get('name', 'Sin nombre')}
                        </span>
                        <div style='display: flex; align-items: center; gap: 8px;'>
                            <span style='
                                background-color: {status_color};
                                color: white;
                                padding: 2px 8px;
                                border-radius: 10px;
                                font-size: 11px;'>
                                {status.capitalize()}
                            </span>
                            {survey_indicator}
                        </div>
                    </div>
                    <div style='margin-top: 4px; color: #666; font-size: 13px;'>
                        <span>📍 {self.activity.get('location', 'Sin ubicación')}</span>
                    </div>
                    <div style='
                        display: flex;
                        justify-content: space-between;
                        margin-top: 4px;
                        color: #666;
                        font-size: 12px;'>
                        <span>🗓️ {date_str} {time_str}</span>
                        <span>👥 {participants_text}</span>
                    </div>
                </div>
            """
            
            self.setText(display_text)
            self.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.setSizeHint(QSize(0, 90))
            
        except Exception as e:
            logger.error(f"Error al configurar item de actividad: {e}")
            self.setText("Error al cargar actividad")

    def setup_tooltip(self):
        """Configura el tooltip informativo"""
        try:
            start_date = self.activity.get('start_date', datetime.now())
            updated_at = self.activity.get('updated_at', start_date)
            participant_count = len(self.activity.get('participant_ids', []))
            max_participants = self.activity.get('max_participants', 0)
            
            tooltip = f"""
                <div style='font-size: 12px;'>
                    <p><b>Actividad:</b> {self.activity.get('name', 'Sin nombre')}</p>
                    <p><b>Estado:</b> {self.activity.get('status', 'pending').capitalize()}</p>
                    <p><b>Ubicación:</b> {self.activity.get('location', 'Sin ubicación')}</p>
                    <p><b>Fecha:</b> {start_date.strftime("%d/%m/%Y %H:%M")}</p>
                    <p><b>Participantes:</b> {participant_count}"""
            
            if max_participants:
                tooltip += f" de {max_participants}"
                
            tooltip += f"""</p>
                    <p><b>Última actualización:</b> {updated_at.strftime("%d/%m/%Y %H:%M")}</p>
                    <p><b>Encuestas:</b> {'Pendientes' if not self.activity.get('surveys_ready', False) else 'Completadas'}</p>
                </div>
            """
            
            self.setToolTip(tooltip)
            
        except Exception as e:
            logger.error(f"Error al configurar tooltip: {e}")

    def get_context_menu(self, parent=None) -> QMenu:
        """Crea un menú contextual para el item"""
        try:
            menu = QMenu(parent)
            
            # Acciones básicas
            edit_action = menu.addAction("✏️ Editar")
            delete_action = menu.addAction("🗑️ Eliminar")
            menu.addSeparator()
            
            # Acciones de estado
            status = self.activity.get('status', 'pending')
            if status == 'active':
                menu.addAction("✅ Marcar como completada")
            elif status == 'pending':
                menu.addAction("▶️ Activar")
            
            # Acciones de encuestas
            menu.addSeparator()
            if not self.activity.get('surveys_ready', False):
                menu.addAction("📝 Generar encuestas")
            else:
                menu.addAction("📊 Procesar encuestas")
                
            return menu
                
        except Exception as e:
            logger.error(f"Error al crear menú contextual: {e}")
            return QMenu()  # Retornar un menú vacío en caso de error
        

class SearchBar(QLineEdit):
    """Barra de búsqueda personalizada"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("🔍 Buscar actividad...")

    