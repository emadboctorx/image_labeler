from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPen
from PyQt5.QtWidgets import (QMainWindow, QApplication, QDesktopWidget, QAction, QStatusBar, QHBoxLayout,
                             QVBoxLayout, QWidget, QLabel, QListWidget, QFileDialog, QFrame, QPushButton,
                             QLineEdit, QMessageBox, QListWidgetItem)
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
        self.main_window.statusBar().showMessage(f'Start: {x1}, {y1}, End: {x2}, {y2}')
        self.update()
        if self.current_image:
            img_name = self.current_image.split('/')[-1]
            self.update_session_data(img_name, x1, y1, x2, y2)
        print(self.main_window.session_data)

    def update_session_data(self, image_name, x1, y1, x2, y2):
        current_label_index = self.main_window.get_current_selection('slabels')
        if current_label_index is None or current_label_index < 0:
            return
        if image_name not in self.main_window.session_data:
            self.main_window.session_data[image_name] = []
        current_image_size = self.width(), self.height()
        object_name = self.main_window.right_widgets['Session Labels'].item(current_label_index).text()
        self.main_window.session_data[image_name].append(
            [current_image_size, (current_label_index, object_name), (x1, y1, x2, y2)])


class ImageLabelerBase(QMainWindow):
    def __init__(self, left_ratio, right_ratio, window_title='Image Labeler',
                 current_image_area=RegularImageArea):
        super().__init__()
        self.left_ratio = left_ratio
        self.right_ratio = right_ratio
        self.current_image = None
        self.current_image_area = current_image_area
        self.image_paths = []
        self.session_data = {}
        self.window_title = window_title
        self.setWindowTitle(self.window_title)
        win_rectangle = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        win_rectangle.moveCenter(center_point)
        self.move(win_rectangle.topLeft())
        self.setStyleSheet('QPushButton:!hover {color: orange} QLineEdit:!hover {color: orange}')
        self.tools = self.addToolBar('Tools')
        self.tool_items = setup_toolbar(self)
        self.top_right_widgets = {'Edit Line': (QLineEdit(), None),
                                  'Add': (QPushButton('Add'), self.add_session_label)}
        self.right_widgets = {'Session Labels': QListWidget(),
                              'Label Title': QLabel('Image labels'), 'Image Label List': QListWidget(),
                              'Photo Title': QLabel('Photo List'), 'Photo List': QListWidget()}
        self.left_widgets = {'Image': self.current_image_area('', self)}
        self.setStatusBar(QStatusBar(self))
        self.adjust_tool_bar()
        self.central_widget = QWidget(self)
        self.main_layout = QHBoxLayout()
        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()
        self.right_top_layout = QHBoxLayout()
        self.right_lower_layout = QVBoxLayout()
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
        self.right_layout.addLayout(self.right_top_layout)
        self.right_layout.addLayout(self.right_lower_layout)
        self.main_layout.addLayout(self.left_layout, self.left_ratio)
        self.main_layout.addLayout(self.right_layout, self.right_ratio)
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

    def adjust_widgets(self):
        self.left_layout.addWidget(self.left_widgets['Image'])
        for widget, widget_method in self.top_right_widgets.values():
            self.right_top_layout.addWidget(widget)
            if widget_method:
                widget.clicked.connect(widget_method)
        self.top_right_widgets['Edit Line'][0].setPlaceholderText('Add Label')
        self.top_right_widgets['Add'][0].setShortcut('Return')
        for widget in self.right_widgets.values():
            self.right_lower_layout.addWidget(widget)
        self.right_widgets['Photo List'].clicked.connect(self.display_selection)
        self.right_widgets['Photo List'].selectionModel().currentChanged.connect(
            self.display_selection)

    def get_current_selection(self, display_list):
        if display_list == 'photo':
            current_selection = self.right_widgets['Photo List'].currentRow()
            if current_selection >= 0:
                return self.image_paths[current_selection]
            self.right_widgets['Photo List'].selectionModel().clear()
        if display_list == 'slabels':
            current_selection = self.right_widgets['Session Labels'].currentRow()
            if current_selection >= 0:
                return current_selection

    def display_selection(self):
        self.current_image = self.get_current_selection('photo')
        self.left_widgets['Image'].switch_image(self.current_image)

    def upload_photos(self):
        file_dialog = QFileDialog()
        file_names, _ = file_dialog.getOpenFileNames(self, 'Upload Photos')
        for file_name in file_names:
            photo_name = file_name.split('/')[-1]
            item = QListWidgetItem(photo_name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.right_widgets['Photo List'].addItem(item)
            self.image_paths.append(file_name)

    def upload_vid(self):
        pass

    def upload_folder(self):
        file_dialog = QFileDialog()
        folder_name = file_dialog.getExistingDirectory()
        if folder_name:
            for file_name in os.listdir(folder_name):
                if not file_name.startswith('.'):
                    photo_name = file_name.split('/')[-1]
                    item = QListWidgetItem(photo_name)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(Qt.Unchecked)
                    self.right_widgets['Photo List'].addItem(item)
                    self.image_paths.append(f'{folder_name}/{file_name}')

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

    @staticmethod
    def get_list_selections(widget_list):
        items = [widget_list.item(i) for i in range(widget_list.count())]
        checked_indexes = [checked_index for checked_index, item in enumerate(items)
                           if item.checkState() == Qt.Checked]
        return checked_indexes

    def delete_list_selections(self, checked_indexes, widget_list):
        if checked_indexes:
            for item in reversed(checked_indexes):
                try:
                    widget_list.takeItem(item)
                    if widget_list is self.right_widgets['Photo List']:
                        del self.image_paths[item]
                except IndexError:
                    print(f'Failed to delete {widget_list.item(item)}')

    def delete_selections(self):
        checked_session_labels = self.get_list_selections(self.right_widgets['Session Labels'])
        checked_image_labels = self.get_list_selections(self.right_widgets['Image Label List'])
        checked_photos = self.get_list_selections(self.right_widgets['Photo List'])
        self.delete_list_selections(checked_session_labels, self.right_widgets['Session Labels'])
        self.delete_list_selections(checked_image_labels, self.right_widgets['Image Label List'])
        self.delete_list_selections(checked_photos, self.right_widgets['Photo List'])

    def reset_labels(self):
        pass

    def display_settings(self):
        pass

    def display_help(self):
        pass

    def add_session_label(self):
        labels = self.right_widgets['Session Labels']
        new_label = self.top_right_widgets['Edit Line'][0].text()
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
            self.top_right_widgets['Edit Line'][0].clear()


if __name__ == '__main__':
    test = QApplication(sys.argv)
    test_window = ImageLabelerBase(6, 4)
    sys.exit(test.exec_())
