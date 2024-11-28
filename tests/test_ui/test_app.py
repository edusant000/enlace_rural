# tests/test_ui/test_app.py

import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.ui.data_manager import UIDataManager

def main():
    app = QApplication(sys.argv)
    
    # Crear el data manager
    data_manager = UIDataManager()
    
    # Crear y mostrar la ventana principal
    window = MainWindow()
    window.show()
    
    # Añadir algunos datos de prueba
    test_activity = {
        'id': 'test_act_1',
        'name': 'Actividad de Prueba',
        'description': 'Esta es una actividad de prueba'
    }
    window.activity_list.addItem(test_activity['name'])
    
    return app.exec()

if __name__ == '__main__':
    main()