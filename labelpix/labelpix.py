from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPen
from PyQt5.QtWidgets import (QMainWindow, QApplication, QDesktopWidget, QAction, QStatusBar, QHBoxLayout,
                             QVBoxLayout, QWidget, QLabel, QListWidget, QFileDialog, QFrame,
                             QLineEdit, QListWidgetItem, QDockWidget, QMessageBox)
from PyQt5.QtCore import Qt, QPoint, QRect
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree
from lxml import etree
from settings import *
import numpy as np
import pandas as pd
import imagesize
import cv2
import sys
import os


class RegularImageArea(QLabel):
    """
    Display only area within the main interface.
    """
    def __init__(self, current_image, main_window):
        """
        Initialize current image for display.
        Args:
            current_image: Path to target image.
            main_window: ImageLabeler instance.
        """
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel)
        self.current_image = current_image
        self.main_window = main_window

    def get_image_names(self):
        """
        Return:
            Directory of the current image and the image name.
        """
        full_name = self.current_image.split('/')
        return '/'.join(full_name[:-1]), full_name[-1].replace('temp-', '')

    def paintEvent(self, event):
        """
        Adjust image size to current window.
        Args:
            event: QPaintEvent object.

        Return:
            None
        """
        painter = QPainter(self)
        current_size = self.size()
        origin = QPoint(0, 0)
        if self.current_image:
            scaled_image = QPixmap(self.current_image).scaled(
                current_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation) 
            painter.drawPixmap(origin, scaled_image)

    def switch_image(self, img):
        """
        Switch the current image displayed in the main window with the new one.
        Args:
            img: Path to new image to display.

        Return:
            None
        """
        self.current_image = img
        self.repaint()

    @staticmethod
    def calculate_ratios(x1, y1, x2, y2, width, height):
        """
        Calculate relative object ratios in the labeled image.
        Args:
            x1: Start x coordinate.
            y1: Start y coordinate.
            x2: End x coordinate.
            y2: End y coordinate.
            width: Bounding box width.
            height: Bounding box height.

        Return:
            bx: Relative center x coordinate.
            by: Relative center y coordinate.
            bw: Relative box width.
            bh: Relative box height.
        """
        box_width = abs(x2 - x1)
        box_height = abs(y2 - y1)
        bx = 1 - ((width - min(x1, x2) + (box_width / 2)) / width)
        by = 1 - ((height - min(y1, y2) + (box_height / 2)) / height)
        bw = box_width / width
        bh = box_height / height
        return bx, by, bw, bh

    @staticmethod
    def ratios_to_coordinates(bx, by, bw, bh, width, height):
        """
        Convert relative coordinates to actual coordinates.
        Args:
            bx: Relative center x coordinate.
            by: Relative center y coordinate.
            bw: Relative box width.
            bh: Relative box height.
            width: Current image display space width.
            height: Current image display space height.

        Return:
            x: x coordinate.
            y: y coordinate.
            w: Bounding box width.
            h: Bounding box height.
        """
        w, h = bw * width, bh * height
        x, y = bx * width + (w / 2), by * height + (h / 2)
        return x, y, w, h

    def draw_boxes(self, ratios):
        """
        Draw boxes over the current image using given ratios.
        Args:
            ratios: A list of [[bx, by, bw, bh], ...]

        Return:
            None
        """
        img_dir, img_name = self.get_image_names()
        to_label = cv2.imread(self.current_image)
        to_label = cv2.resize(to_label, (self.width(), self.height()))
        for bx, by, bw, bh in ratios:
            x, y, w, h = self.ratios_to_coordinates(bx, by, bw, bh, self.width(), self.height())
            to_label = cv2.rectangle(to_label, (int(x), int(y)), (int(x + w), int(y + h)), (255, 0, 0), 2)
        temp = f'{img_dir}/temp-{img_name}'
        cv2.imwrite(f'{img_dir}/temp-{img_name}', to_label)
        self.switch_image(temp)


class ImageEditorArea(RegularImageArea):
    """
    Edit and display area within the main interface.
    """
    def __init__(self, current_image, main_window):
        """
        Initialize current image for display.
        Args:
            current_image: Path to target image.
            main_window: ImageLabeler instance.
        """
        super().__init__(current_image, main_window)
        self.main_window = main_window
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.begin = QPoint()
        self.end = QPoint()

    def paintEvent(self, event):
        """
        Adjust image size to current window and draw bounding box.
        Args:
            event: QPaintEvent object.

        Return:
            None
        """
        super().paintEvent(event)
        qp = QPainter(self)
        pen = QPen(Qt.blue)
        pen.setWidth(2)
        qp.setPen(pen)
        qp.drawRect(QRect(self.begin, self.end))

    def mousePressEvent(self, event):
        """
        Start drawing the box.
        Args:
            event: QMouseEvent object.

        Return:
            None
        """
        self.start_point = event.pos()
        self.begin = event.pos()
        self.end = event.pos()
        self.update()

    def mouseMoveEvent(self, event):
        """
        Update size with mouse move.
        Args:
            event: QMouseEvent object.

        Return:
            None
        """
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        """
        Calculate coordinates of the bounding box, display a message, update session data.
        Args:
            event: QMouseEvent object.

        Return:
            None
        """
        self.begin = event.pos()
        self.end = event.pos()
        self.end_point = event.pos()
        x1, y1, x2, y2 = (self.start_point.x(), self.start_point.y(),
                          self.end_point.x(), self.end_point.y())
        self.main_window.statusBar().showMessage(f'Start: {x1}, {y1}, End: {x2}, {y2}')
        self.update()
        if self.current_image:
            bx, by, bw, bh = self.calculate_ratios(x1, y1, x2, y2, self.width(), self.height())
            self.update_session_data(x1, y1, x2, y2)
            current_label_index = self.main_window.get_current_selection('slabels')
            if current_label_index is None or current_label_index < 0:
                return
            self.draw_boxes([[bx, by, bw, bh]])

    def update_session_data(self, x1, y1, x2, y2):
        """
        Add a row to session_data containing calculated ratios.
        Args:
            x1: Start x coordinate.
            y1: Start y coordinate.
            x2: End x coordinate.
            y2: End y coordinate.

        Return:
            None
        """
        current_label_index = self.main_window.get_current_selection('slabels')
        if current_label_index is None or current_label_index < 0:
            return
        window_width, window_height = self.width(), self.height()
        object_name = self.main_window.right_widgets['Session Labels'].item(current_label_index).text()
        bx, by, bw, bh = self.calculate_ratios(x1, y1, x2, y2, window_width, window_height)
        data = [[self.get_image_names()[1], object_name, current_label_index, bx, by, bw, bh]]
        to_add = pd.DataFrame(data, columns=self.main_window.session_data.columns)
        self.main_window.session_data = pd.concat([self.main_window.session_data, to_add], ignore_index=True)
        self.main_window.add_to_list(f'{data}', self.main_window.right_widgets['Image Label List'])


class ImageLabeler(QMainWindow):
    """
    Image labeling main interface.
    """
    def __init__(self, window_title='labelpix', current_image_area=RegularImageArea):
        """
        Initialize main interface and display.
        Args:
            window_title: Title of the window.
            current_image_area: RegularImageArea or ImageEditorArea object.
        """
        super().__init__()
        self.current_image = None
        self.label_file = None
        self.current_image_area = current_image_area
        self.images = []
        self.image_paths = {}
        self.session_data = pd.DataFrame(
            columns=['Image', 'Object Name', 'Object Index', 'bx', 'by', 'bw', 'bh'])
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
        """
        Adjust the top tool bar and setup buttons/icons.

        Return:
            None
        """
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
        """
        Adjust window layouts.

        Return:
            None
        """
        self.main_layout.addLayout(self.left_layout)
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

    def adjust_widgets(self):
        """
        Adjust window widgets.

        Return:
            None
        """
        self.left_layout.addWidget(self.left_widgets['Image'])
        for text, (widget, widget_method) in self.top_right_widgets.items():
            dock_widget = QDockWidget(text)
            dock_widget.setFeatures(QDockWidget.NoDockWidgetFeatures)
            dock_widget.setWidget(widget)
            self.addDockWidget(Qt.RightDockWidgetArea, dock_widget)
            if widget_method:
                widget.editingFinished.connect(widget_method)
        self.top_right_widgets['Add Label'][0].setPlaceholderText('Add Label')
        self.right_widgets['Photo List'].selectionModel().currentChanged.connect(
            self.display_selection)
        for text, widget in self.right_widgets.items():
            dock_widget = QDockWidget(text)
            dock_widget.setFeatures(QDockWidget.NoDockWidgetFeatures)
            dock_widget.setWidget(widget)
            self.addDockWidget(Qt.RightDockWidgetArea, dock_widget)

    def get_current_selection(self, display_list):
        """
        Get current selected item data.
        Args:
            display_list: One of the right QWidgetList(s).

        Return:
            Image path or current row.
        """
        if display_list == 'photo':
            current_selection = self.right_widgets['Photo List'].currentRow()
            if current_selection >= 0:
                return self.images[current_selection]
            self.right_widgets['Photo List'].selectionModel().clear()
        if display_list == 'slabels':
            current_selection = self.right_widgets['Session Labels'].currentRow()
            if current_selection >= 0:
                return current_selection

    @staticmethod
    def add_to_list(item, widget_list):
        """
        Add item to one of the right QWidgetList(s).
        Args:
            item: str : Item to add.
            widget_list: One of the right QWidgetList(s).

        Return:
            None
        """
        item = QListWidgetItem(item)
        item.setFlags(item.flags() | Qt.ItemIsSelectable |
                      Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
        item.setCheckState(Qt.Unchecked)
        widget_list.addItem(item)
        widget_list.selectionModel().clear()

    def display_selection(self):
        """
        Display image that is selected in the right Photo list.

        Return:
            None
        """
        ratios = []
        self.right_widgets['Image Label List'].clear()
        self.current_image = self.get_current_selection('photo')
        if not self.current_image:
            return
        self.left_widgets['Image'].switch_image(self.current_image)
        image_dir, img_name = self.left_widgets['Image'].get_image_names()
        for item in self.session_data.loc[self.session_data['Image'] == img_name].values:
            self.add_to_list(f'{[[x for x in item]]}', self.right_widgets['Image Label List'])
            ratios.append([x for x in item][3:])
        self.left_widgets['Image'].draw_boxes(ratios)

    def upload_photos(self):
        """
        Add image(s) to the right photo list.

        Return:
            None
        """
        file_dialog = QFileDialog()
        file_names, _ = file_dialog.getOpenFileNames(self, 'Upload Photos')
        for file_name in file_names:
            image_dir, photo_name = '/'.join(file_name.split('/')[:-1]), file_name.split('/')[-1]
            self.add_to_list(photo_name, self.right_widgets['Photo List'])
            self.images.append(file_name)
            self.image_paths[photo_name] = image_dir

    def upload_vid(self):
        pass

    def upload_folder(self):
        """
        Add images of a folder to the right photo list.

        Return:
            None
        """
        file_dialog = QFileDialog()
        folder_name = file_dialog.getExistingDirectory()
        if folder_name:
            for file_name in os.listdir(folder_name):
                if not file_name.startswith('.'):
                    photo_name = file_name.split('/')[-1]
                    self.add_to_list(photo_name, self.right_widgets['Photo List'])
                    self.images.append(f'{folder_name}/{file_name}')
                    self.image_paths[file_name] = folder_name

    def switch_editor(self, image_area):
        """
        Switch between the display/edit interfaces.
        Args:
            image_area: RegularImageArea or ImageEditorArea object.

        Return:
            None
        """
        self.left_layout.removeWidget(self.left_widgets['Image'])
        self.left_widgets['Image'] = image_area(self.current_image, self)
        self.left_layout.addWidget(self.left_widgets['Image'])

    def edit_mode(self):
        """
        Switch between the display/edit interfaces.

        Return:
            None
        """
        if self.windowTitle() == 'labelpix':
            self.setWindowTitle('labelpix(Editor Mode)')
            self.switch_editor(ImageEditorArea)
        else:
            self.setWindowTitle('labelpix')
            self.switch_editor(RegularImageArea)
        self.display_selection()

    def save_session_data(self, location):
        """
        Save session data to csv/hdf.
        Args:
            location: Path to save session data file.

        Return:
            None
        """
        if location.endswith('.csv'):
            self.session_data.to_csv(location, index=False)
        if location.endswith('h5'):
            self.session_data.to_hdf(location, key='session_data', index=False)

    def read_session_data(self, location):
        """
        Read session data from csv/hdf
        Args:
            location: Path to session data file.

        Return:
            data.
        """
        data = self.session_data
        if location.endswith('.csv'):
            data = pd.read_csv(location)
        if location.endswith('.h5'):
            data = pd.read_hdf(location, 'session_data')
        return data

    def save_changes_table(self):
        """
        Save the data in self.session_data to new/existing csv/hdf format.

        Return:
            None
        """
        dialog = QFileDialog()
        location, _ = dialog.getSaveFileName(self, 'Save as')
        self.label_file = location
        self.save_session_data(location)
        self.statusBar().showMessage(f'Labels Saved to {location}')

    def clear_yolo_txt(self):
        """
        Delete txt files in working directories.

        Return:
            None
        """
        working_directories = set(['/'.join(item.split('/')[:-1]) for item in self.images])
        for working_directory in working_directories:
            for file_name in os.listdir(working_directory):
                if file_name.endswith('.txt'):
                    os.remove(f'{working_directory}/{file_name}')

    def save_changes_yolo(self):
        """
        Save session data to txt files in yolo format.

        Return:
            None
        """
        if self.session_data.empty:
            return
        self.clear_yolo_txt()
        txt_file_names = set()
        for index, data in self.session_data.iterrows():
            image_name, object_name, object_index, bx, by, bw, bh = data
            image_path = self.image_paths[image_name]
            txt_file_name = f'{image_path}/{image_name.split(".")[0]}.txt'
            txt_file_names.add(txt_file_name)
            with open(txt_file_name, 'a') as txt:
                txt.write(f'{object_index!s} {bx!s} {by!s} {bw!s} {bh!s}\n')
            self.statusBar().showMessage(f'Saved {len(txt_file_names)} txt files')

    @staticmethod
    def generate_xml_file(full_path, image_size, obj_data, out_file):
        """
        Generate XML label file.
        Args:
            full_path: Path to image.
            image_size: Size of the image.
            obj_data: object coordinates and object name
            out_file: output xml file.

        Return:
            None
        """
        path_contents = os.path.split(full_path)
        folder_name, file_name = path_contents[-2], path_contents[-1]
        w, h = image_size
        top = Element('annotation')
        folder = SubElement(top, 'folder')
        folder.text = folder_name
        image_name = SubElement(top, 'filename')
        image_name.text = file_name
        path_item = SubElement(top, 'path')
        path_item.text = full_path
        size = SubElement(top, 'size')
        width = SubElement(size, 'width')
        width.text = f'{w}'
        height = SubElement(size, 'height')
        height.text = f'{h}'
        depth = SubElement(size, 'depth')
        depth.text = f'{3}'
        for item in obj_data:
            x_min, y_min, x_max, y_max, object_name = item
            object_item = SubElement(top, 'object')
            name = SubElement(object_item, 'name')
            name.text = object_name
            box = SubElement(object_item, 'bndbox')
            x0 = SubElement(box, 'xmin')
            x0.text = f'{x_min}'
            y0 = SubElement(box, 'ymin')
            y0.text = f'{y_min}'
            x1 = SubElement(box, 'xmax')
            x1.text = f'{x_max}'
            y1 = SubElement(box, 'ymax')
            y1.text = f'{y_max}'
        rough_string = ElementTree.tostring(top, 'utf8')
        root = etree.fromstring(rough_string)
        pretty = etree.tostring(
            root, pretty_print=True, encoding='utf-8').replace("  ".encode(), "\t".encode())
        with open(out_file, 'wb') as output:
            output.write(pretty)

    def save_changes_voc(self):
        """
        Save session data to xml voc format.

        Return:
            None
        """
        groups = self.session_data.groupby('Image').apply(np.array)
        for image, objects in groups.iteritems():
            image_path = self.image_paths[image]
            image_size = imagesize.get(os.path.join(image_path, image))
            obj_data = []
            for box in objects:
                img, object_name, object_index, bx, by, bw, bh = box
                x, y, w, h = self.left_widgets['Image'].ratios_to_coordinates(bx, by, bw, bh, *image_size)
                obj_data.append([x, y, x + w, y + h, object_name])
            out = os.path.join(image_path, f'{image.split(".")[0]}.xml')
            full_path = os.path.join(image_path, image)
            self.generate_xml_file(full_path, image_size, obj_data, out)
            obj_data.clear()

    @staticmethod
    def get_list_selections(widget_list):
        """
        Get in-list index of checked items in the given QWidgetList.
        Args:
            widget_list: One of the right QWidgetList(s).

        Return:
            A list of checked indexes.
        """
        items = [widget_list.item(i) for i in range(widget_list.count())]
        checked_indexes = [checked_index for checked_index, item in enumerate(items)
                           if item.checkState() == Qt.Checked]
        return checked_indexes

    def delete_list_selections(self, checked_indexes, widget_list):
        """
        Delete checked indexes in the given QWidgetList.
        Args:
            checked_indexes: A list of checked indexes.
            widget_list: One of the right QWidgetList(s).

        Return:
            None
        """
        if checked_indexes:
            for q_list_index in reversed(checked_indexes):
                if widget_list is self.right_widgets['Photo List']:
                    image_name = self.images[q_list_index].split('/')[-1]
                    del self.images[q_list_index]
                    del self.image_paths[image_name]
                if widget_list is self.right_widgets['Image Label List']:
                    current_row = eval(f'{self.right_widgets["Image Label List"].item(q_list_index).text()}')[0]
                    row_items = dict(zip(self.session_data.columns, current_row))
                    current_boxes = self.session_data.loc[self.session_data['Image'] == current_row[0]]
                    for index, box in current_boxes[['bx', 'by', 'bw', 'bh']].iterrows():
                        if box['bx'] == row_items['bx'] and box['by'] == row_items['by']:
                            self.session_data = self.session_data.drop(index)
                            break
                widget_list.takeItem(q_list_index)

    def delete_selections(self):
        """
        Delete all checked items in all 3 right QWidgetList(s).

        Return:
            None
        """
        checked_session_labels = self.get_list_selections(self.right_widgets['Session Labels'])
        checked_image_labels = self.get_list_selections(self.right_widgets['Image Label List'])
        checked_photos = self.get_list_selections(self.right_widgets['Photo List'])
        self.delete_list_selections(checked_session_labels, self.right_widgets['Session Labels'])
        self.delete_list_selections(checked_image_labels, self.right_widgets['Image Label List'])
        self.delete_list_selections(checked_photos, self.right_widgets['Photo List'])

    def upload_labels(self):
        """
        Upload labels from csv or hdf.

        Return:
            None
        """
        dialog = QFileDialog()
        file_name, _ = dialog.getOpenFileName(self, 'Load labels')
        self.label_file = file_name
        new_data = self.read_session_data(file_name)
        labels_to_add = new_data[['Object Name', 'Object Index']].drop_duplicates().sort_values(
            by='Object Index').values
        self.right_widgets['Session Labels'].clear()
        for label, index in labels_to_add:
            self.add_session_label(label)
        self.session_data = pd.concat([self.session_data, new_data], ignore_index=True).drop_duplicates()
        if file_name:
            self.statusBar().showMessage(f'Labels loaded from {file_name}')

    def reset_labels(self):
        """
        Delete all labels in the current session_data.

        Return:
            None
        """
        message = QMessageBox()
        answer = message.question(
            self, 'Question', 'Are you sure, do you want to delete all current session labels?')
        if answer == message.Yes:
            self.session_data.drop(self.session_data.index, inplace=True)
            self.statusBar().showMessage(f'Session labels deleted successfully')

    def display_settings(self):
        pass

    def display_help(self):
        pass

    def add_session_label(self, label=None):
        """
        Add label entered to the session labels list.

        Return:
            None
        """
        labels = self.right_widgets['Session Labels']
        new_label = label or self.top_right_widgets['Add Label'][0].text()
        session_labels = [str(labels.item(i).text()) for i in range(labels.count())]
        if new_label and new_label not in session_labels:
            self.add_to_list(new_label, labels)
            self.top_right_widgets['Add Label'][0].clear()

    def remove_temps(self):
        """
        Remove temporary image files from working directories.

        Return:
            None
        """
        working_dirs = set(['/'.join(item.split('/')[:-1]) for item in self.images])
        for working_dir in working_dirs:
            for file_name in os.listdir(working_dir):
                if 'temp-' in file_name:
                    os.remove(f'{working_dir}/{file_name}')

    def closeEvent(self, event):
        """
        Save session data, clear cache, and close with or without saving.
        Args:
            event: QCloseEvent object.

        Return:
            None
        """
        self.remove_temps()
        event.accept()


if __name__ == '__main__':
    test = QApplication(sys.argv)
    test_window = ImageLabeler()
    sys.exit(test.exec_())
