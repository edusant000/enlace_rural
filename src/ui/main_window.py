# src/ui/main_window.py

from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QMessageBox
from .views.activity_view import ActivityView
from .views.activity_detail_view import ActivityDetailView
from .views.image_management_view import ImageManagementView
from .data_manager import UIDataManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enlace Rural")
        self.setMinimumSize(1200, 700)
        
        self.data_manager = UIDataManager()
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Crear tabs
        self.tab_widget = QTabWidget()
        
        # Tab de actividades
        self.activity_view = ActivityView(self.data_manager, self)
        self.tab_widget.addTab(self.activity_view, "Actividades")
        
        # Tab de gestión de imágenes
        self.image_view = ImageManagementView(data_manager=self.data_manager)
        self.tab_widget.addTab(self.image_view, "Procesar Encuestas")
        
        layout.addWidget(self.tab_widget)
        
        # Conectar señales
        self.activity_view.activity_selected.connect(self.on_activity_selected)
        self.image_view.processing_complete.connect(self.on_surveys_processed)

    async def on_activity_selected(self, activity_id: str):
        """Cuando se selecciona una actividad, mostrar su vista detallada"""
        try:
            # Obtener datos de la actividad
            activity_data = await self.data_manager.get_activity(activity_id)
            if activity_data:
                # Crear y mostrar la vista de detalle
                detail_view = ActivityDetailView(activity_data, self)
                # Conectar señales para actualización/eliminación
                detail_view.activity_updated.connect(self.on_activity_updated)
                detail_view.activity_deleted.connect(self.on_activity_deleted)
                detail_view.show()
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Error al cargar detalles de la actividad: {str(e)}"
            )

    async def on_activity_updated(self, activity):
        """Cuando se actualiza una actividad, recargar la lista"""
        await self.activity_view.load_activities()

    async def on_activity_deleted(self, activity_id):
        """Cuando se elimina una actividad, recargar la lista"""
        await self.activity_view.load_activities()

    async def on_surveys_processed(self, results: dict):
        """
        Maneja el evento cuando las encuestas han sido procesadas.
        
        Args:
            results: Diccionario con los resultados del procesamiento OCR
        """
        try:
            # Actualizar la lista de actividades para reflejar nuevas encuestas
            await self.activity_view.load_activities()
            
            # Contar resultados exitosos y fallidos
            successful = sum(1 for r in results.values() if 'error' not in r)
            failed = len(results) - successful
            
            message = f"Procesamiento completado:\n"
            message += f"- Encuestas exitosas: {successful}\n"
            if failed > 0:
                message += f"- Encuestas fallidas: {failed}"
            
            QMessageBox.information(self, "Resultado del Procesamiento", message)
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Error al actualizar después del procesamiento: {str(e)}"
            )