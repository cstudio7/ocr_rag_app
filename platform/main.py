import sys
import os
import signal
import subprocess
import time
import logging
import socket
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QMovie  # For GIF animation

# -----------------------------
# Configure logging
# -----------------------------
downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
os.makedirs(downloads_dir, exist_ok=True)
log_file = os.path.join(downloads_dir, "KnowledgeNet.log")
logging.basicConfig(
    filename=log_file,
    filemode='a',
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF OCR Desktop App")
        self.resize(800, 600)

        logging.info("Starting GUI application.")

        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)

        self.loading_label = QLabel(self)
        self.movie = QMovie("focus.gif")
        self.loading_label.setMovie(self.movie)
        self.movie.start()
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.resize(100, 100)
        self.loading_label.move(
            (self.width() - self.loading_label.width()) // 2,
            (self.height() - self.loading_label.height()) // 2
        )

        self.flask_process = self.start_flask_server()

        url = "http://127.0.0.1:9123"
        logging.info(f"Loading URL: {url}")
        self.view.load(QUrl(url))
        self.loading_label.show()
        self.view.loadFinished.connect(self.on_load_finished)

    def start_flask_server(self):
        this_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(this_dir, 'KnowledgeNetBackend'))
        if not os.path.exists(backend_dir):
            logging.error(f"Backend directory {backend_dir} does not exist!")
            sys.exit(1)

        logging.info(f"Starting Flask server in: {backend_dir}")
        process = subprocess.Popen(
            [sys.executable, 'app.py'],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )

        def log_flask_output(pipe):
            for line in iter(pipe.readline, b""):
                logging.info("Flask: %s", line.decode(errors="ignore").rstrip())
        threading.Thread(target=log_flask_output, args=(process.stdout,), daemon=True).start()

        # Wait for the port to open
        start = time.time()
        while time.time() - start < 15:
            try:
                with socket.create_connection(('127.0.0.1', 9123), timeout=1):
                    logging.info("Flask server port is open.")
                    break
            except Exception:
                time.sleep(0.5)
        else:
            logging.error("Flask server never opened port 9123")
            sys.exit(1)

        logging.info("Flask server process started.")
        return process

    def on_load_finished(self, ok):
        if ok:
            logging.info("Page loaded successfully in QWebEngineView.")
            self.loading_label.hide()
        else:
            logging.error("Failed to load the page in QWebEngineView.")

    def closeEvent(self, event):
        if self.flask_process:
            logging.info("Shutting down Flask server.")
            os.killpg(os.getpgid(self.flask_process.pid), signal.SIGTERM)
        event.accept()

if __name__ == '__main__':
    logging.info("Application launch initiated.")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    exit_code = app.exec_()
    logging.info(f"Application exited with code {exit_code}.")
    sys.exit(exit_code)
