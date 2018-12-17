# coding=utf8

from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QRect
from PyQt5.QtMultimedia import *
import sys
from PyQt5.Qt import QVideoWidget, QUrl
from enum import Enum

# GUID ActiveX компонента
TrueConfCallX_Class = '{27EF4BA2-4500-4839-B88A-F2F4744FE56A}'

# параметры подключения: сервер, user_id (TrueConf ID), пароль
SERVER = 'ru11.trueconf.net'
USER = '125001'
PASSWORD = '125001'

class State(Enum):
    Unknown = 0
    Connect = 1
    Login = 2
    Normal = 3
    Wait = 4
    Conference = 5
    Close = 6
# end of class State(Enum)


# класс контейнер для ActiveX
class CallXWidget(QObject):

    def __init__(self, view):
        self.view = view
        super().__init__()
        # self.view = view
        # текущее состояние
        self.state = State.Unknown;
        self.prev_state = State.Unknown;
        # Создаем компонент "TrueConf SDK for Windows" aka CallX
        self.ocx = QAxWidget(TrueConfCallX_Class)

        # =====================================================================
        # подключаем некоторые события ActiveX компонента CallX
        # =====================================================================
        # Событие № 1: сигнализирует об окончании инициализации компонента
        # это событие говорит о готовности CallX к работе
        self.ocx.OnXAfterStart.connect(self._OnXAfterStart)
        # Подключились к серверу
        self.ocx.OnServerConnected[str].connect(self._OnServerConnected)
        # Авторизовались по login и password
        self.ocx.OnLogin[str].connect(self._OnLogin)
        # Пришло оповещение о звонке
        # В обработчике этого события располагается логика
        #  принятия/отклонения входящего звонка или приглашения в конференцию
        self.ocx.OnInviteReceived[str].connect(self._OnInviteReceived)
        # Сообщение об ошибке
        self.ocx.OnXError[int, str].connect(self._OnXError)
        # Ошибка авторизации
        self.ocx.OnXLoginError[int].connect(self._OnXLoginError)
        # Получили входящее собщение в Чат
        self.ocx.OnIncomingChatMessage[str, str, str, 'qulonglong'].connect(self._OnIncomingChatMessage)
        # Изменение состояния
        # Важное событие, в котором определяется текущее состояние:
        #   залогинен, в конференции и пр.
        self.ocx.OnXChangeState[int, int].connect(self._OnXChangeState)

    def checkState(self):
        self.view.setShowPromo(self.state in [State.Normal])
        
    # Events
    def _OnXAfterStart(self):
        print("**OnXAfterStart")
        # Выбор устройств: просто выбираем первые в списке оборудования
        self.ocx.XSetCameraByIndex(0)
        self.ocx.XSelectMicByIndex(0)
        self.ocx.XSelectSpeakerByIndex(0)
        # соединение с сервером
        self.ocx.connectToServer(SERVER)

    def _OnServerConnected(self, eventDetails):
        print("**OnServerConnected")
        print(eventDetails)
        # Авторизация
        self.ocx.login(USER, PASSWORD)

    def _OnLogin(self, eventDetails):
        print("**OnLogin")

    def _OnInviteReceived(self, eventDetails):
        print("**OnInviteReceived")
        print(eventDetails)
        # Принимаем звонок
        self.ocx.accept()

    def _OnXError(self, errorCode, errorMsg):
        print("**OnXError")
        print('{}. Code: {}'.format(errorMsg, errorCode))

    def _OnXLoginError(self, errorCode):
        print("**OnXLoginError")
        if errorCode == 8:
            print('Support for SDK Applications is not enabled on this server')
        else:
            print('Login error. Code: {}'.format(errorCode))

    def _OnIncomingChatMessage(self, peerId, peerDn, message, time):
        print("**OnIncomingChatMessage")
        print('From userID "{}" Display name "{}": "{}"'.format(peerId, peerDn, message))
        
    def _OnXChangeState (self, prevState, newState):
        try:
            print("**OnXChangeState {} -> {}".format(State(prevState), State(newState)))
            self.state = State(newState)
            self.prev_state = State(prevState)
            # check
            self.checkState()
        except ValueError: 
            pass
# end of class ActiveXExtend(QObject)
