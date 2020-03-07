from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPen
from PyQt5.QtWidgets import (QMainWindow, QApplication, QDesktopWidget, QAction, QStatusBar, QHBoxLayout,
                             QVBoxLayout, QWidget, QLabel, QListWidget, QFileDialog, QFrame,
                             QLineEdit, QListWidgetItem, QDockWidget)
from PyQt5.QtCore import Qt, QPoint, QRect
from settings import *
import cv2
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

    @staticmethod
    def calculate_ratios(x1, y1, x2, y2, width, height):
        box_width = abs(x2 - x1)
        box_height = abs(y2 - y1)
        b_x = 1 - ((width - min(x1, x2) + (box_width / 2)) / width)
        b_y = 1 - ((height - min(y1, y2) + (box_height / 2)) / height)
        b_w = box_width / width
        b_h = box_height / height
        return b_x, b_y, b_w, b_h

    def mouseReleaseEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        self.end_point = event.pos()
        x1, y1, x2, y2 = (self.start_point.x(), self.start_point.y(),
                          self.end_point.x(), self.end_point.y())
        self.main_window.statusBar().showMessage(f'Start: {x1}, {y1}, End: {x2}, {y2}')
        self.update()
        if self.current_image:
            img_name, img_dir = self.current_image.split('/')[-1], '/'.join(self.current_image.split('/')[:-1])
            # labeled = cv2.imread(self.current_image)
            # labeled = cv2.resize(labeled, (self.width(), self.height()))
            # xx, yy, ww, hh = self.calculate_ratios(x1, y1, x2, y2, self.width(), self.height())
            # w, h = ww * self.width(), hh * self.height()
            # x, y = xx * self.width() + (w / 2), yy * self.height() + (h / 2)
            # labeled = cv2.rectangle(labeled, (int(x), int(y)), (int(x + w), int(y + h)), (0, 0, 255), 1)
            # cv2.imshow('x', labeled)
            # cv2.waitKey(0)
            # img_name = (f'{img_dir}/labeled-{img_name}'
            #             if 'labeled' not in self.current_image else self.current_image)
            # cv2.imwrite(img_name, labeled)
            # self.current_image = img_name
            self.update_session_data(img_name, x1, y1, x2, y2)

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
    def __init__(self, window_title='Image Labeler', current_image_area=RegularImageArea):
        super().__init__()
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
        self.top_right_widgets = {'Add Label': (QLineEdit(), self.add_session_label)}
        self.right_widgets = {'Session Labels': QListWidget(),
                              'Image Label List': QListWidget(),
                              'Photo List': QListWidget()}
        self.left_widgets = {'Image': self.current_image_area('', self)}
        self.setStatusBar(QStatusBar(self))
        self.adjust_tool_bar()
        self.central_widget = QWidget(self)
        self.main_layout = QHBoxLayout()
        self.left_layout = QVBoxLayout()
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
        self.main_layout.addLayout(self.left_layout)
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
        new_label = self.top_right_widgets['Add Label'][0].text()
        session_labels = [str(labels.item(i).text()) for i in range(labels.count())]
        if new_label and new_label not in session_labels:
            item = QListWidgetItem(new_label)
            item.setFlags(item.flags() | Qt.ItemIsSelectable |
                          Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
            item.setCheckState(Qt.Unchecked)
            labels.addItem(item)
            self.right_widgets['Session Labels'].selectionModel().clear()
            self.top_right_widgets['Add Label'][0].clear()


if __name__ == '__main__':
    test = QApplication(sys.argv)
    test_window = ImageLabelerBase()
    sys.exit(test.exec_())
