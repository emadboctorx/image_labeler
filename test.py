import sys
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow)


class MouseTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.label = QLabel(self)
        self.setMouseTracking(True)

    def initUI(self):
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('Mouse Tracker')
        self.show()

    def mouseMoveEvent(self, event):
        self.statusBar().showMessage('Mouse coords: ( %d : %d )' % (event.x(), event.y()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MouseTracker()
    sys.exit(app.exec_())

