from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)

class NotificationManager:
    @staticmethod
    def show_error(parent, title: str, message: str):
        """Muestra un mensaje de error."""
        logger.error(f"Error: {message}")
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def show_info(parent, title: str, message: str):
        """Muestra un mensaje informativo."""
        logger.info(message)
        QMessageBox.information(parent, title, message)

    @staticmethod
    def show_warning(parent, title: str, message: str):
        """Muestra un mensaje de advertencia."""
        logger.warning(message)
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def show_question(parent, title: str, message: str) -> bool:
        """
        Muestra una pregunta que requiere confirmación.
        Retorna True si el usuario confirma, False en caso contrario.
        """
        reply = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes