# coding=utf8

from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QRect
from PyQt5.QtMultimedia import *
import sys
from PyQt5.Qt import QVideoWidget, QUrl
from callx import CallXWidget, State

# заголовок окна
TITLE = "CallX Python Example: Video Kiosk"
# Промо
PROMO_FILE = 'c:\\work\\WIN-SDK\\TrueConf Kiosk Markup\\video\\Video Conferencing Server Software Works via Internet, LAN -.avi'

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
        rc = QRect(100, 100, 640, 480)
        self.setGeometry(rc)
        # layout
        self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)
        # CallX
        self.callx_widget = CallXWidget(self)
        self.layout.addWidget(self.callx_widget.ocx)
        # promo video
        self.video = QVideoWidget(self)
        self.player = QMediaPlayer(self)
        self.player.setVideoOutput(self.video)
        # set media content
        self.media_file = QUrl.fromLocalFile(PROMO_FILE)
        self.mediaContent = QMediaContent(self.media_file)
        self.playlist = QMediaPlaylist()
        self.playlist.addMedia(self.mediaContent)
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop);
        self.player.setPlaylist(self.playlist)
        # init
        self.setShowPromo(False)
        
    def setShowPromo(self, is_show: bool):
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
