# src/main.py
import sys
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

async def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    await window.activity_view.load_activities()
    
    # Cambiado .exec() por .run_forever()
    await qasync.QEventLoop(app).run_forever()

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)