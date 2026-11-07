import sys
import os
import subprocess
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QMovie

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF OCR Desktop App")
        self.resize(800, 600)

        # Set up QWebEngineView
        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)

        # Set up loading label with focus.gif
        self.loading_label = QLabel(self)
        gif_path = os.path.join(os.path.dirname(__file__), "./focus.gif")
        self.movie = QMovie(gif_path)
        self.loading_label.setMovie(self.movie)
        self.movie.start()
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.resize(100, 100)  # Adjust size to fit GIF
        self.loading_label.move((self.width() - self.loading_label.width()) // 2,
                              (self.height() - self.loading_label.height()) // 2)
        self.loading_label.show()

        # Load the URL and hide loading icon when done
        self.view.load(QUrl("http://127.0.0.1:9123"))
        self.view.loadFinished.connect(self.on_load_finished)

        # Start Flask server
        self.flask_process = self.start_flask_server()

    def start_flask_server(self):
        this_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(this_dir, 'KnowledgeNetBackend'))
        print(f"Starting Flask in: {backend_dir}")
        self.flask_process = subprocess.Popen(
            ['python', 'app.py'],
            cwd=backend_dir,
            start_new_session=True
        )
        # Wait for Flask to start
        time.sleep(8)
        return self.flask_process

    def on_load_finished(self, ok):
        if ok:
            print("Page loaded successfully in QWebEngineView")
            self.loading_label.hide()
        else:
            print("Failed to load the page in QWebEngineView")

    def closeEvent(self, event):
        # Terminate the Flask process
        if self.flask_process:
            try:
                self.flask_process.terminate()
                self.flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.flask_process.kill()
            finally:
                self.flask_process = None
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())