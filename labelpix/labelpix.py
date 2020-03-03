from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPen
from PyQt5.QtWidgets import (QMainWindow, QApplication, QDesktopWidget, QAction, QStatusBar, QHBoxLayout,
                             QVBoxLayout, QWidget, QLabel, QListWidget, QFileDialog, QFrame)
from PyQt5.QtCore import Qt, QPoint, QRect
from settings import *
import sys
import os


class RegularImageArea(QLabel):
    def __init__(self, current_image, main_window):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel)
        self.current_image = current_image
        self.main_window = main_window

    def paintEvent(self, event):
        painter = QPainter(self)
        current_size = self.size()
        origin = QPoint(0, 0)
        if self.current_image:
            scaled_image = QPixmap(self.current_image).scaled(
                current_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(origin, scaled_image)

    def switch_image(self, img):
        self.current_image = img
        self.repaint()


class ImageEditorArea(RegularImageArea):
    def __init__(self, current_image, main_window):
        super().__init__(current_image, main_window)
        self.main_window = main_window
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
        x1, y1, x2, y2 = (self.start_point.x(), self.start_point.y(),
                          self.end_point.x(), self.end_point.y())
        if self.main_window:
            self.main_window.statusBar().showMessage(f'Start: {x1}, {y1}, End: {x2}, {y2}')
        self.update()

    def update_labels(self, label, image_labels):
        image_labels.append((label, self.start_point, self.end_point))


class ImageLabelerBase(QMainWindow):
    def __init__(self, left_ratio, right_ratio, window_title='Image Labeler', current_image_area=RegularImageArea):
        super().__init__()
        self.left_ratio = left_ratio
        self.right_ratio = right_ratio
        self.current_image = None
        self.current_image_area = current_image_area
        self.image_paths = {}
        self.window_title = window_title
        self.setWindowTitle(self.window_title)
        win_rectangle = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        win_rectangle.moveCenter(center_point)
        self.move(win_rectangle.topLeft())
        self.setStyleSheet('QPushButton:!hover {color: red}')
        self.tools = self.addToolBar('Tools')
        self.tool_items = setup_toolbar(self)
        self.left_widgets = {'Image': self.current_image_area('', self)}
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
        if sys.platform == 'darwin':
            self.setUnifiedTitleAndToolBarOnMac(True)
        for label, icon_file, widget_method, status_tip, key, check in self.tool_items.values():
            action = QAction(QIcon(f'../Icons/{icon_file}'), label, self)
            action.setStatusTip(status_tip)
            action.setShortcut(key)
            if check:
                action.setCheckable(True)
            if label == 'Delete':
                action.setShortcut('Backspace')
            action.triggered.connect(widget_method)
            self.tools.addAction(action)
            self.tools.addSeparator()

    def adjust_layouts(self):
        self.main_layout.addLayout(self.left_layout, self.left_ratio)
        self.main_layout.addLayout(self.right_layout, self.right_ratio)
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

    def adjust_widgets(self):
        self.left_layout.addWidget(self.left_widgets['Image'])
        for widget in self.right_widgets.values():
            self.right_layout.addWidget(widget)
        self.right_widgets['Photo List'].clicked.connect(self.display_selection)
        self.right_widgets['Photo List'].selectionModel().currentChanged.connect(self.display_selection)

    def get_current_selection(self):
        current_selection = self.right_widgets['Photo List'].currentRow()
        if current_selection >= 0:
            return [path for path in self.image_paths.values()][current_selection]

    def display_selection(self):
        self.current_image = self.get_current_selection()
        self.left_widgets['Image'].switch_image(self.current_image)

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
        if folder_name:
            for file_name in os.listdir(folder_name):
                if not file_name.startswith('.'):
                    photo_name = file_name.split('/')[-1]
                    self.right_widgets['Photo List'].addItem(photo_name)
                    self.image_paths[photo_name] = f'{folder_name}/{file_name}'

    def switch_editor(self, image_area):
        self.left_layout.removeWidget(self.left_widgets['Image'])
        self.left_widgets['Image'] = image_area(self.current_image, self)
        self.left_layout.addWidget(self.left_widgets['Image'])

    def edit_mode(self):
        if self.windowTitle() == 'Image Labeler':
            self.setWindowTitle('Image Labeler(Editor Mode)')
            self.switch_editor(ImageEditorArea)
        else:
            self.setWindowTitle('Image Labeler')
            self.switch_editor(RegularImageArea)
        self.display_selection()

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
    test_window = ImageLabelerBase(6, 4)
    sys.exit(test.exec_())
