from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt

class LoadingIndicator(QWidget):
    def __init__(self, parent=None, message="Cargando..."):
        super().__init__(parent)
        self.setup_ui(message)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def setup_ui(self, message):
        layout = QVBoxLayout(self)
        
        # Label con mensaje
        self.message_label = QLabel(message)
        self.message_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 180);
                padding: 10px;
                border-radius: 5px;
            }
        """)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Modo indeterminado
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #05B8CC;
                width: 20px;
            }
        """)
        
        layout.addWidget(self.message_label)
        layout.addWidget(self.progress_bar)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_message(self, message):
        """Actualiza el mensaje mostrado."""
        self.message_label.setText(message)