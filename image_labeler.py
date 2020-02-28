import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QApplication, QDesktopWidget, QAction, QStatusBar

from settings import *


class ImageLabeler(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(50, 50, 1000, 600)
        self.setWindowTitle('Image Labeler')
        win_rectangle = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        win_rectangle.moveCenter(center_point)
        self.move(win_rectangle.topLeft())
        self.setStyleSheet('QPushButton:!hover {color: red}')
        self.tools = self.addToolBar('Tools')
        self.tool_items = setup_toolbar(self)
        self.adjust_tool_bar()
        self.setStatusBar(QStatusBar(self))
        self.show()

    def adjust_tool_bar(self):
        self.tools.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        for label, icon_file, widget_method, status_tip, key in self.tool_items.values():
            action = QAction(QIcon(f'Icons/{icon_file}'), label, self)
            action.setStatusTip(status_tip)
            action.setShortcut(key)
            if label == 'Delete':
                action.setShortcut('Backspace')
            action.triggered.connect(widget_method)
            self.tools.addAction(action)
            self.tools.addSeparator()

    def upload_photo(self):
        pass

    def upload_vid(self):
        pass

    def upload_folder(self):
        pass

    def draw_rectangle(self):
        pass

    def save_changes(self):
        pass

    def delete_selected(self):
        pass

    def reset_labels(self):
        pass

    def display_settings(self):
        pass

    def display_help(self):
        pass


if __name__ == '__main__':
    test = QApplication(sys.argv)
    test_window = ImageLabeler()
    sys.exit(test.exec_())
