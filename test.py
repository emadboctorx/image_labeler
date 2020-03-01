from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter, QPen
from PyQt5.QtWidgets import (QMainWindow, QApplication, QDesktopWidget, QAction, QStatusBar, QHBoxLayout,
                             QVBoxLayout, QWidget, QLabel, QListWidget, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QPoint, QRect
from settings import *
import sys
import cv2
import os


class ImageArea(QLabel):
    def __init__(self):
        super().__init__()
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.begin = QPoint()
        self.end = QPoint()

    def paintEvent(self, event):
        super().paintEvent(event)
        qp = QPainter(self)
        pen = QPen(Qt.red)
        qp.setPen(pen)
        qp.drawRect(QRect(self.begin, self.end))

    def mousePressEvent(self, event):
        self.start_point = event.pos()
        self.begin = event.pos()
        self.end = event.pos()
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        self.end_point = event.pos()
        self.update()

    def get_square(self, label, image_labels):
        image_labels.append((label, self.start_point, self.end_point))


class ImageLabelerBase(QMainWindow):
    def __init__(self, left_ratio, right_ratio, image_display_size, window_title='Image Labeler',
                 current_image_area=QLabel):
        super().__init__()
        self.left_ratio = left_ratio
        self.right_ratio = right_ratio
        self.image_display_size = image_display_size
        self.current_image = None
        self.current_window = None
        self.image_paths = {}
        self.setGeometry(50, 50, 1000, 600)
        self.setWindowTitle(window_title)
        win_rectangle = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        win_rectangle.moveCenter(center_point)
        self.move(win_rectangle.topLeft())
        self.setStyleSheet('QPushButton:!hover {color: red}')
        self.tools = self.addToolBar('Tools')
        self.tool_items = setup_toolbar(self)
        self.left_widgets = {'Image': current_image_area()}
        self.right_widgets = {'Label Title': QLabel('Label List'), 'Label List': QListWidget(),
                              'Photo Title': QLabel('Photo List'), 'Photo List': QListWidget()}
        self.setStatusBar(QStatusBar(self))
        self.adjust_tool_bar()
        self.central_widget = QWidget(self)
        self.main_layout = QHBoxLayout()
        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()
        self.adjust_widgets()
        self.adjust_layouts()
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
        self.tools.addSeparator()

    def adjust_layouts(self):
        self.main_layout.addLayout(self.left_layout, self.left_ratio)
        self.main_layout.addLayout(self.right_layout, self.right_ratio)
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

    def adjust_widgets(self):
        self.left_layout.addWidget(self.left_widgets['Image'])
        self.left_widgets['Image'].setPixmap(QPixmap(self.current_image))
        for widget in self.right_widgets.values():
            self.right_layout.addWidget(widget)
        self.right_widgets['Photo List'].clicked.connect(self.display_selection)
        self.right_widgets['Photo List'].selectionModel().currentChanged.connect(self.display_selection)

    def display_selection(self):
        current_selection = self.right_widgets['Photo List'].currentRow()
        image_path = [path for path in self.image_paths.values()][current_selection]
        self.set_current_display(image_path)

    def set_current_display(self, image_path):
        try:
            uploaded = cv2.imread(image_path)
            resized = cv2.resize(uploaded, self.image_display_size)
            height, width = self.image_display_size
            self.current_image = QImage(resized, height, width, QImage.Format_RGB888)
            self.left_widgets['Image'].setPixmap(QPixmap(self.current_image))
        except (cv2.error, FileNotFoundError) as e:
            print(f'Image {image_path} could not be loaded: {e}')

    def upload_photos(self):
        file_dialog = QFileDialog()
        file_names, _ = file_dialog.getOpenFileNames(self, 'Upload Photos')
        for file_name in file_names:
            photo_name = file_name.split('/')[-1]
            self.right_widgets['Photo List'].addItem(photo_name)
            self.image_paths[photo_name] = file_name

    def upload_vid(self):
        pass

    def upload_folder(self):
        file_dialog = QFileDialog()
        folder_name = file_dialog.getExistingDirectory()
        for file_name in os.listdir(folder_name):
            if not file_name.startswith('.'):
                photo_name = file_name.split('/')[-1]
                self.right_widgets['Photo List'].addItem(photo_name)
                self.image_paths[photo_name] = f'{folder_name}/{file_name}'

    def edit_mode(self):
        if self.right_widgets['Photo List'].count() <= 0:
            message = QMessageBox()
            message.information(self, 'Information', 'You must select a photo first')
        current_selection = self.right_widgets['Photo List'].currentRow()
        self.current_window = ImageEditor(self.image_paths, current_selection, self.left_ratio, self.right_ratio,
                                          self.image_display_size)
        self.close()

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


class ImageEditor(ImageLabelerBase):
    def __init__(self, image_paths, selection, left_ratio, right_ratio, image_display_size,
                 current_image_area=ImageArea, window_title='Image Labeler(Editor Mode)'):
        ImageLabelerBase.__init__(self, left_ratio, right_ratio, image_display_size,
                                  window_title, current_image_area)
        self.image_paths = image_paths
        for image_name, image_path in image_paths.items():
            self.right_widgets['Photo List'].addItem(image_name)
        try:
            self.right_widgets['Photo List'].item(selection).setSelected(True)
        except AttributeError:
            pass
        current_path = [path for path in image_paths.values()][selection]
        self.set_current_display(current_path)

    def edit_mode(self):
        pass


if __name__ == '__main__':
    test = QApplication(sys.argv)
    test_window = ImageLabelerBase(6, 4, (700, 500))
    sys.exit(test.exec_())
