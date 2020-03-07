from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPen
from PyQt5.QtWidgets import (QMainWindow, QApplication, QDesktopWidget, QAction, QStatusBar, QHBoxLayout,
                             QVBoxLayout, QWidget, QLabel, QListWidget, QFileDialog, QFrame, QPushButton,
                             QLineEdit, QMessageBox, QListWidgetItem, QSizePolicy, QDockWidget)
from PyQt5.QtCore import Qt, QPoint, QRect, QSize
from settings import *
import cv2
import sys
import os
from labelpix_test import *


class TestWindow(QMainWindow):
    def __init__(self, left_ratio, right_ratio, window_title):
        super().__init__()
        self.current_image = None
        self.left_ratio = left_ratio
        self.right_ratio = right_ratio
        self.left_widgets = {'Image': RegularImageArea('test.jpg', self)}
        self.top_right_widgets = {'Add Label': (QLineEdit(), self.add_session_label)}
        self.right_widgets = {'Session Labels': QListWidget(),
                              'Image Label List': QListWidget(),
                              'Photo List': QListWidget()}
        self.central_widget = QWidget(self)
        self.main_layout = QHBoxLayout()
        self.left_layout = QVBoxLayout()
        self.adjust_widgets()
        self.adjust_layouts()
        self.show()

    def adjust_layouts(self):
        self.main_layout.addLayout(self.left_layout, self.left_ratio)
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

    def adjust_widgets(self):
        self.left_layout.addWidget(self.left_widgets['Image'])
        for text, (widget, widget_method) in self.top_right_widgets.items():
            dock_widget = QDockWidget(text)
            dock_widget.setFeatures(QDockWidget.NoDockWidgetFeatures)
            dock_widget.setWidget(widget)
            self.addDockWidget(Qt.RightDockWidgetArea, dock_widget)
            if widget_method:
                widget.editingFinished.connect(widget_method)
        self.top_right_widgets['Add Label'][0].setPlaceholderText('Add Label')
        self.right_widgets['Photo List'].clicked.connect(self.display_selection)
        self.right_widgets['Photo List'].selectionModel().currentChanged.connect(
            self.display_selection)
        for text, widget in self.right_widgets.items():
            dock_widget = QDockWidget(text)
            dock_widget.setFeatures(QDockWidget.NoDockWidgetFeatures)
            dock_widget.setWidget(widget)
            self.addDockWidget(Qt.RightDockWidgetArea, dock_widget)

    def add_session_label(self):
        labels = self.right_widgets['Session Labels']
        new_label = self.top_right_widgets['Add Label'][0].text()
        session_labels = [str(labels.item(i).text()) for i in range(labels.count())]
        if new_label in session_labels:
            message = QMessageBox()
            message.information(self, 'Information', f'{new_label} already in the session labels')
        if new_label and new_label not in session_labels:
            item = QListWidgetItem(new_label)
            item.setFlags(item.flags() | Qt.ItemIsSelectable |
                          Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
            item.setCheckState(Qt.Unchecked)
            labels.addItem(item)
            self.right_widgets['Session Labels'].selectionModel().clear()
            self.top_right_widgets['Add Label'][0].clear()

    def display_selection(self):
        self.current_image = self.get_current_selection('photo')
        self.left_widgets['Image'].switch_image(self.current_image)


if __name__ == '__main__':
    test = QApplication(sys.argv)
    test_window = TestWindow(6, 4, 'kos')
    sys.exit(test.exec_())

