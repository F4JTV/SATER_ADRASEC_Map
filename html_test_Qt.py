from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtWebEngineWidgets
from pathlib import Path
import sys
import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Feelings App Prototype")

        view = QtWebEngineWidgets.QWebEngineView()
        html = Path('./map.html').read_text(encoding="utf8")
        view.setHtml(html)
        self.setCentralWidget(view)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()