from PyQt5.QtWidgets import *
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class Label(QLabel):
    def __init__(self, img):
        super(Label, self).__init__()
        self.setFrameStyle(QFrame.StyledPanel)
        self.pixmap = QPixmap(img)
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.begin = QPoint()
        self.end = QPoint()

    def paintEvent(self, event):
        super().paintEvent(event)
        qp = QPainter(self)
        size = self.size()
        point = QPoint(0,0)
        scaledPix = self.pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        point.setX((size.width() - scaledPix.width())/2)
        point.setY((size.height() - scaledPix.height())/2)
        qp.drawPixmap(point, scaledPix)
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


class Main(QWidget):
    def __init__(self):
        super(Main, self).__init__()
        layout = QH
        label = Label(r'test.jpg')
        layout.addWidget(label)
        layout.setRowStretch(0,1)
        layout.setColumnStretch(0,1)

        self.setLayout(layout)
        self.show()


if __name__ =="__main__":
    test = QApplication(sys.argv)
    test_window = Main()
    sys.exit(test.exec_())