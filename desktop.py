import sys
import subprocess
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

# Start Flask in the background
flask_process = subprocess.Popen(
    [sys.executable, 'KnowledgeNewBackend/app.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Give Flask time to start
time.sleep(1.5)

# Launch Qt app
app = QApplication(sys.argv)
browser = QWebEngineView()
browser.load(QUrl('http://127.0.0.1:5000'))
browser.setWindowTitle("Flask + Qt App")
browser.resize(1024, 768)
browser.show()

exit_code = app.exec_()

# Kill Flask process on exit
flask_process.terminate()
sys.exit(exit_code)
