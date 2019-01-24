# coding=utf8

from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QRect, pyqtSignal
from PyQt5.QtMultimedia import *
import sys
from PyQt5.Qt import QVideoWidget, QUrl, Qt
from callx import CallXWidget, State
import os.path

# ================================================================
# Required variables: server IP, user_id (TrueConf ID), password
# ================================================================
SERVER = '' # server.name URL or server IP
USER = '' #'<trueconf id>'
PASSWORD = '' #'<password>'
# Video
PROMO_VIDEO_FILE = '---.avi'  # As example: 'c:\\video\\promo.avi'
# ================================================================

# Title
TITLE = "CallX Python Example: Video Kiosk"


# Main Window
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
        self.showMaximized()
        #self.setGeometry(0, 0, 900, 700)
        # layout
        self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)
        # CallX
        self.callx_widget = CallXWidget(self, SERVER, USER, PASSWORD, debug_mode=True)
        self.layout.addWidget(self.callx_widget.ocx)
        # promo video
        self.video = QVideoWidget(self)
        self.player = QMediaPlayer(self)
        self.player.setVideoOutput(self.video)
        # set media content if exist a video file
        if os.path.isfile(PROMO_VIDEO_FILE):
            self.media_file = QUrl.fromLocalFile(PROMO_VIDEO_FILE)
            self.mediaContent = QMediaContent(self.media_file)
            self.playlist = QMediaPlaylist()
            self.playlist.addMedia(self.mediaContent)
            self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
            self.player.setPlaylist(self.playlist)
        else:
            print('Video file "{}" not exist'.format(PROMO_VIDEO_FILE))
        # init
        self.showPromo(False)
        # connect to signals
        self.callx_widget.stateChanged.connect(self.onStateChanged)
        self.callx_widget.IncomingChatMessage.connect(self.onIncomingChatMessage)

    # ============================================================================================
    # Signals
    # ============================================================================================
    def onStateChanged(self, prev_state, new_state):
        # show/hide promo
        if self.callx_widget.debug_mode:
            print('***Signal onStateChanged: "{}" -> "{}"'.format(prev_state, new_state))
        self.showPromo(new_state in [State.Normal])
        if new_state == State.Normal:
            pass

    def onIncomingChatMessage(self, peerId, peerDn, message, time):
        # show/hide promo
        if self.callx_widget.debug_mode:
            print('***Signal IncomingChatMessage: "{}", "{}"; "{}"; {}'.format(peerId, peerDn, message, time))
    # ============================================================================================

    def showPromo(self, is_show: bool):
        # check a video content first
        if not self.playlist:
            return

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
    # Check required variables
    if (not SERVER) or (not USER) or (not PASSWORD):
        print('Please set variables to connect and authorize. List variables: SERVER, USER, PASSWORD.')
        sys.exit()
    else:
        app = QApplication(sys.argv)
        MainWindow = KioskWidget()
        MainWindow.show()
        sys.exit(app.exec_())
