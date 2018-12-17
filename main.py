# coding=utf8

from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QRect, pyqtSignal
from PyQt5.QtMultimedia import *
import sys
from PyQt5.Qt import QVideoWidget, QUrl, Qt
from callx import CallXWidget, State

# заголовок окна
TITLE = "CallX Python Example: Video Kiosk"
# Промо
PROMO_VIDEO_FILE = '---.avi'

# параметры подключения: сервер, user_id (TrueConf ID), пароль
SERVER = '---'
USER = '---'
PASSWORD = '---'

# класс главного окна
class KioskWidget(QWidget):

    def __init__(self):
        self.layout = None
        self.callx_widget = None
        self.video = None
        self.player = None
        self.playlist = None
        
        QAxWidget.__init__(self)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(TITLE)
        #self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        #rc = QRect(100, 100, 640, 480)
        #self.setGeometry(rc)
        self.showMaximized()
        # layout
        self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)
        # CallX
        self.callx_widget = CallXWidget(self, SERVER, USER, PASSWORD)
        self.layout.addWidget(self.callx_widget.ocx)
        # promo video
        self.video = QVideoWidget(self)
        self.player = QMediaPlayer(self)
        self.player.setVideoOutput(self.video)
        # set media content
        self.media_file = QUrl.fromLocalFile(PROMO_VIDEO_FILE)
        self.mediaContent = QMediaContent(self.media_file)
        self.playlist = QMediaPlaylist()
        self.playlist.addMedia(self.mediaContent)
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop);
        self.player.setPlaylist(self.playlist)
        # init
        self.showPromo(False)
        # connect to signals
        self.callx_widget.stateChanged.connect(self.onStateChanged)

    def onStateChanged(self, prev_state, new_state):
        # show/hide promo
        self.showPromo(new_state in [State.Normal])

    def showPromo(self, is_show: bool):
        if is_show:
            self.layout.removeWidget(self.callx_widget.ocx)
            self.callx_widget.ocx.hide()
            self.layout.addWidget(self.video)
            self.video.show()
            self.player.play()
        else:
            self.player.pause()
            self.video.hide()
            self.layout.removeWidget(self.video)
            self.layout.addWidget(self.callx_widget.ocx)
            self.callx_widget.ocx.show()
# end of class CallXWindow(QWidget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = KioskWidget()
    MainWindow.show()
    sys.exit(app.exec_())
