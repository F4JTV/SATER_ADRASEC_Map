#!/usr/bin/python3
# coding=utf8
"""
Script visant à afficher sur un carte les azimuts que les
OM ont relevés dans le cadre d'un plan SATER
"""
# TODO: Peupler About

from sys import argv
from pathlib import Path
from math import cos, sin, radians

from folium import Map, Marker, LatLngPopup, Icon, PolyLine, CustomIcon
from PyQt5.QtCore import Qt, QRegExp, QTimer, QUrl, QSize
from PyQt5.QtGui import QRegExpValidator, QIcon
from PyQt5 import QtWebEngineWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget,
                             QVBoxLayout, QHBoxLayout, QHeaderView,
                             QTableWidget, QPushButton, QSpinBox,
                             QComboBox, QLineEdit, QStyle, QMenuBar,
                             QMenu, QAction, QFileDialog, QDialog)

ICON = "./img/logo.jpg"


def dms_to_dd(de, mi, se, di):
    dd = de + (mi / 60) + (se / 3600)
    if di in ['W', 'S']:
        dd = -dd
    return round(dd, 4)


def dd_to_dms(dd, lo_or_la):
    di = str()
    if lo_or_la == "lat":
        if str(dd).startswith("-"):
            di = "S"
        else:
            di = "N"
    elif lo_or_la == "long":
        if str(dd).startswith("-"):
            di = "W"
        else:
            di = "E"

    is_positive = dd >= 0
    dd = abs(dd)
    minutes, seconds = divmod(dd * 3600, 60)
    degrees, minutes = divmod(minutes, 60)
    degrees = degrees if is_positive else -degrees
    return int(degrees), int(minutes), int(seconds), di


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ############ Window Config ############
        self.setWindowTitle("SATER ADRASEC Map")
        self.setWindowIcon(QIcon(ICON))

        # ############ Attributes ############
        self.rows = 0
        self.actual_tiles = "OpenStreetMap.Mapnik"
        self.m = Map()
        self.about_win = None
        self.start_loc = (46.6796, 3.0761)

        # ############ Menu ############
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        self.file_menu = QMenu("&File")
        self.edit_menu = QMenu("&Edit")
        # self.about_action = QAction("&About")
        # self.about_action.triggered.connect(self.display_about_window)
        self.menu_bar.addMenu(self.file_menu)
        self.menu_bar.addMenu(self.edit_menu)
        # self.menu_bar.addAction(self.about_action)

        # Edit Menu
        self.change_tiles_menu = QMenu("Select tiles")
        self.openstreetmap_default_action = QAction("OpenstreetMap")
        self.openstreetmap_fr_action = QAction("OpenstreetMap France")
        self.opentopomap_action = QAction("OpenTopoMap")
        self.geoportail_plan_action = QAction("Geoportail Plan")
        self.edit_menu.addMenu(self.change_tiles_menu)
        self.change_tiles_menu.addAction(self.openstreetmap_default_action)
        self.change_tiles_menu.addAction(self.openstreetmap_fr_action)
        self.change_tiles_menu.addAction(self.opentopomap_action)
        self.change_tiles_menu.addAction(self.geoportail_plan_action)
        self.openstreetmap_default_action.triggered.connect(self.set_openstreetmap_default)
        self.openstreetmap_fr_action.triggered.connect(self.set_openstreetmap_fr)
        self.opentopomap_action.triggered.connect(self.set_opentopomap)
        self.geoportail_plan_action.triggered.connect(self.set_geoportail_plan)

        # Menu Actions
        self.save_map_action = QAction("&Save map")
        self.file_menu.addAction(self.save_map_action)
        self.save_map_action.triggered.connect(self.save_map)

        self.file_menu.addSeparator()

        self.exit_action = QAction("Exit")
        self.file_menu.addAction(self.exit_action)
        self.exit_action.triggered.connect(self.close)

        # ############ Widgets ############
        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        self.left_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_layout, 5)

        self.add_btn = QPushButton("Add")
        # noinspection PyUnresolvedReferences
        self.add_btn.clicked.connect(self.add_row)
        self.left_layout.addWidget(self.add_btn)

        # ############ Table ############
        self.table = QTableWidget()
        self.table.setMinimumWidth(600)
        self.table.setColumnCount(11)
        self.table.setSortingEnabled(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(True)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(10, QHeaderView.Stretch)
        self.table.setHorizontalHeaderLabels(["Callsign", "Deg", "Min",
                                              "Sec", "Dir", "Deg", "Min",
                                              "Sec", "Dir", "Az", "Supp"])
        self.left_layout.addWidget(self.table)
        self.table.horizontalHeader().adjustSize()

        # ############ HTML View ############
        self.view = QtWebEngineWidgets.QWebEngineView()
        self.view.setMinimumWidth(400)
        self.html = Path('./basemap.html').read_text(encoding="utf8")
        self.view.setHtml(self.html)
        self.main_layout.addWidget(self.view, 6)

        self.enter_btn = QPushButton("Ok")
        # noinspection PyUnresolvedReferences
        self.enter_btn.clicked.connect(self.validate_data)
        self.left_layout.addWidget(self.enter_btn)

        QTimer.singleShot(500, self.showMaximized)

    def display_about_window(self):
        """Display the about Window"""
        if self.about_win is not None:
            self.about_win.close()
        self.about_win = AboutWindow(self)
        self.about_win.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.about_win.show()

    def set_tiles(self):
        if self.rows > 0:
            self.validate_data()
        else:
            self.m = Map(location=self.start_loc, zoom_start=6, tiles=self.actual_tiles)
            self.m.add_child(LatLngPopup())
            self.m.save("./map.html")
            self.html = Path('./map.html').read_text(encoding="utf8")
            self.view.load(QUrl.fromLocalFile(self.html))
            self.view.setHtml(self.html)

    def set_openstreetmap_default(self):
        self.actual_tiles = "OpenStreetMap.Mapnik"
        self.set_tiles()

    def set_openstreetmap_fr(self):
        self.actual_tiles = "OpenStreetMap.France"
        self.set_tiles()

    def set_opentopomap(self):
        self.actual_tiles = "OpenTopoMap"
        self.set_tiles()

    def set_geoportail_plan(self):
        self.actual_tiles = "GeoportailFrance.plan"
        self.set_tiles()

    def save_map(self):
        file_name = QFileDialog.getSaveFileName(self, "Save HTML Map",
                                                ".", "HTML file (*.html)")[0]

        if file_name == "":
            return

        if not file_name.endswith(".html"):
            file_name += ".html"

        self.m.save(file_name)

    def validate_data(self):
        """ Parse data, construct map and display it """
        self.m = Map(location=self.start_loc, zoom_start=6, tiles=self.actual_tiles)
        self.m.add_child(LatLngPopup())

        try:
            for row in range(0, self.table.rowCount()):
                callsign = self.table.cellWidget(row, 0).text()
                lat_degre = int(self.table.cellWidget(row, 1).text().strip())
                lat_minute = int(self.table.cellWidget(row, 2).text().strip())
                lat_second = int(self.table.cellWidget(row, 3).text().strip())
                lat_dir = self.table.cellWidget(row, 4).currentText()
                long_degre = int(self.table.cellWidget(row, 5).text().strip())
                long_minute = int(self.table.cellWidget(row, 6).text().strip())
                long_second = int(self.table.cellWidget(row, 7).text().strip())
                long_dir = self.table.cellWidget(row, 8).currentText()
                azimut = int(self.table.cellWidget(row, 9).text().replace(" °", ""))

                origin_point = [dms_to_dd(lat_degre, lat_minute, lat_second, lat_dir),
                                dms_to_dd(long_degre, long_minute, long_second, long_dir)]
                tooltip = callsign
                angle = azimut

                Marker(location=origin_point,
                       popup=f"DMS:\n"
                             f"Latitude:{lat_degre}°{lat_minute}'{lat_second}\"{lat_dir}\n"
                             f"Longitude:{long_degre}°{long_minute}'{long_second}\"{long_dir}\n"
                             f"DD:\n"
                             f"Latitude:{round(origin_point[0], 4)}\n"
                             f"Longitude:{round(origin_point[1], 4)}",
                       tooltip=tooltip,
                       # icon=CustomIcon("./img/logo.jpg", (48,48))).add_to(self.m)
                       icon=Icon(color='red', icon='male', prefix="fa")).add_to(self.m)

                end_lat = origin_point[0] + cos(radians(angle))
                end_lon = origin_point[1] + sin(radians(angle))

                PolyLine([origin_point, [end_lat, end_lon]]).add_to(self.m)
        except ValueError:
            pass

        self.m.save("./map.html")

        self.html = Path('./map.html').read_text(encoding="utf8")
        self.view.load(QUrl.fromLocalFile(self.html))
        self.view.setHtml(self.html)

    def add_row(self):
        """ Add a row to the table """
        self.rows += 1
        self.table.setRowCount(self.rows)
        col_1 = QLineEdit()
        col_1.setAlignment(Qt.AlignCenter)
        col_2 = QLineEdit()
        col_2.setValidator(QRegExpValidator(QRegExp(r"^[0-9%]{1,3}$")))
        col_2.setAlignment(Qt.AlignCenter)
        col_3 = QLineEdit()
        col_3.setValidator(QRegExpValidator(QRegExp(r"^[0-9%]{1,2}$")))
        col_3.setAlignment(Qt.AlignCenter)
        col_4 = QLineEdit()
        col_4.setValidator(QRegExpValidator(QRegExp(r"^[0-9%]{1,2}$")))
        col_4.setAlignment(Qt.AlignCenter)
        col_5 = QComboBox()
        col_5.setEditable(True)
        col_5.lineEdit().setReadOnly(True)
        col_5.lineEdit().setAlignment(Qt.AlignCenter)
        col_5.addItems(["N", "S"])
        col_6 = QLineEdit()
        col_6.setValidator(QRegExpValidator(QRegExp(r"^[0-9%]{1,3}$")))
        col_6.setAlignment(Qt.AlignCenter)
        col_7 = QLineEdit()
        col_7.setValidator(QRegExpValidator(QRegExp(r"^[0-9%]{1,2}$")))
        col_7.setAlignment(Qt.AlignCenter)
        col_8 = QLineEdit()
        col_8.setValidator(QRegExpValidator(QRegExp(r"^[0-9%]{1,2}$")))
        col_8.setAlignment(Qt.AlignCenter)
        col_9 = QComboBox()
        col_9.setEditable(True)
        col_9.lineEdit().setReadOnly(True)
        col_9.lineEdit().setAlignment(Qt.AlignCenter)
        col_9.addItems(["E", "W"])
        col_10 = QSpinBox()
        col_10.setAlignment(Qt.AlignCenter)
        col_10.setMaximum(359)
        col_10.setMinimum(0)
        col_10.setSingleStep(1)
        col_10.setSuffix(" °")
        trash_btn = QPushButton()
        trash_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        # noinspection PyUnresolvedReferences
        trash_btn.clicked.connect(self.remove_row)

        self.table.setCellWidget(self.rows - 1, 0, col_1)
        self.table.setCellWidget(self.rows - 1, 1, col_2)
        self.table.setCellWidget(self.rows - 1, 2, col_3)
        self.table.setCellWidget(self.rows - 1, 3, col_4)
        self.table.setCellWidget(self.rows - 1, 4, col_5)
        self.table.setCellWidget(self.rows - 1, 5, col_6)
        self.table.setCellWidget(self.rows - 1, 6, col_7)
        self.table.setCellWidget(self.rows - 1, 7, col_8)
        self.table.setCellWidget(self.rows - 1, 8, col_9)
        self.table.setCellWidget(self.rows - 1, 9, col_10)
        self.table.setCellWidget(self.rows - 1, 10, trash_btn)

        self.table.horizontalHeader().adjustSize()

    def remove_row(self):
        self.table.removeRow(self.table.currentRow())
        self.rows -= 1


class AboutWindow(QDialog):
    def __init__(self, m):
        super().__init__()

        self.master = m

        self.setWindowTitle(f"About SATER ADRASEC Map")
        self.setModal(True)
        self.setWindowIcon(QIcon(ICON))
        self.setFixedSize(QSize(300, 300))
        self.setWindowFlags(Qt.WindowCloseButtonHint)
        x = self.master.geometry().x() + self.master.width() // 2 - self.width() // 2
        y = self.master.geometry().y() + self.master.height() // 2 - self.height() // 2
        self.setGeometry(x, y, 300, 300)
        self.setContentsMargins(0, 0, 0, 0)


if __name__ == '__main__':
    app = QApplication(argv)
    window = MainWindow()
    window.show()
    app.exec()
