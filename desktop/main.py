import sys
import os
import subprocess
import time
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QMovie

# --- Setup Logging ---
log_path = os.path.join(os.path.dirname(__file__), 'app.log')
logging.basicConfig(
    filename=log_path,
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Paths ---
# When bundled with PyInstaller, data files live under sys._MEIPASS.
BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = (
    os.path.join(BASE_DIR, "backend")
    if hasattr(sys, "_MEIPASS")
    else os.path.abspath(os.path.join(BASE_DIR, "..", "backend"))
)
GIF_PATH = os.path.join(BASE_DIR, "assets", "focus.gif")
APP_URL = f"http://127.0.0.1:{os.environ.get('FLASK_PORT', '9123')}"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Initializing MainWindow")
        self.setWindowTitle("PDF OCR Desktop App")
        self.resize(800, 600)

        # Set up QWebEngineView
        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)

        # Set up loading label with focus.gif
        self.loading_label = QLabel(self)
        gif_path = GIF_PATH
        self.movie = QMovie(gif_path)

        if not self.movie.isValid():
            logger.warning("Failed to load GIF from: %s", gif_path)
        else:
            self.loading_label.setMovie(self.movie)
            self.movie.start()
            logger.info("Started loading GIF: %s", gif_path)

        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.resize(100, 100)
        self.loading_label.move((self.width() - self.loading_label.width()) // 2,
                                (self.height() - self.loading_label.height()) // 2)
        self.loading_label.show()

        # Load the app URL and hide loading icon when done
        self.view.load(QUrl(APP_URL))
        self.view.loadFinished.connect(self.on_load_finished)

        # Start Flask server
        self.flask_process = self.start_flask_server()

    def start_flask_server(self):
        backend_dir = BACKEND_DIR
        logger.info(f"Starting Flask in directory: {backend_dir}")

        try:
            self.flask_process = subprocess.Popen(
                [sys.executable, 'app.py'],
                cwd=backend_dir,
                start_new_session=True
            )
            logger.info("Flask process started with PID: %s", self.flask_process.pid)
        except Exception as e:
            logger.exception("Failed to start Flask server: %s", e)
            self.flask_process = None
            return None

        # Wait for Flask to be ready
        time.sleep(8)
        return self.flask_process

    def on_load_finished(self, ok):
        if ok:
            logger.info("Page loaded successfully in QWebEngineView")
            self.loading_label.hide()
        else:
            logger.error("Failed to load the page in QWebEngineView")

    def closeEvent(self, event):
        logger.info("Closing application...")
        if self.flask_process:
            try:
                self.flask_process.terminate()
                self.flask_process.wait(timeout=5)
                logger.info("Flask process terminated gracefully.")
            except subprocess.TimeoutExpired:
                self.flask_process.kill()
                logger.warning("Flask process killed after timeout.")
            finally:
                self.flask_process = None
        event.accept()

if __name__ == '__main__':
    logger.info("Application starting...")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    exit_code = app.exec_()
    logger.info("Application exited with code: %d", exit_code)
    sys.exit(exit_code)
