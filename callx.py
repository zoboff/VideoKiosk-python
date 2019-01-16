# coding=utf8

from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QRect, pyqtSignal
from PyQt5.QtMultimedia import *
import sys
from PyQt5.Qt import QVideoWidget, QUrl
from enum import Enum

# GUID ActiveX компонента
TrueConfCallX_Class = '{27EF4BA2-4500-4839-B88A-F2F4744FE56A}'


class State(Enum):
    Unknown = 0
    Connect = 1
    Login = 2
    Normal = 3
    Wait = 4
    Conference = 5
    Close = 6
# end of class State(Enum)

# cut a long string
def cut80symbols(data: str):
    s = data
    if len(s) > 80:
        s = s[0:76] + '...'
    return s

# класс контейнер для ActiveX
class CallXWidget(QObject):
    stateChanged = pyqtSignal(object, object)

    def __init__(self, view, server: str, user: str, password: str, camera_index: int = 0):
        super().__init__()

        self.view = view
        # connection & authorization
        self.server = server
        self.user = user
        self.password = password
        self.camera_index = camera_index

        # текущее состояние
        self.state = State.Unknown
        self.prev_state = State.Unknown
        # Создаем компонент "TrueConf SDK for Windows" aka CallX
        self.ocx = QAxWidget(TrueConfCallX_Class)

        # =====================================================================
        # подключаем некоторые события ActiveX компонента CallX
        # =====================================================================
        # Нотификация о различных событиях
        self.ocx.OnXNotify[str].connect(self._OnXNotify)
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
        #   эмит сигнала stateChanged 
        self.ocx.OnXChangeState[int, int].connect(self._OnXChangeState)
        # Завершение работы
        self.ocx.OnXTerminate.connect(self._OnXTerminate)
        # Ошибка загрузки
        self.ocx.OnXStartFail.connect(self._OnXStartFail)
        # Обновление списка адресной книги
        self.ocx.OnAbookUpdate[str].connect(self._OnAbookUpdate)
        # 
        self.ocx.OnAppUpdateAvailable[str].connect(self._OnAppUpdateAvailable)
        # Изменение раскладки
        self.ocx.OnChangeVideoMatrixReport[str].connect(self._OnChangeVideoMatrixReport)
        # Создание конференции
        self.ocx.OnConferenceCreated[str].connect(self._OnConferenceCreated)
        # Окончание конференции
        self.ocx.OnConferenceDeleted[str].connect(self._OnConferenceDeleted)
        # ---
        self.ocx.OnContactBlocked[str].connect(self._OnContactBlocked)
        # Удаление контакта из адресной книги
        self.ocx.OnContactDeleted[str].connect(self._OnContactDeleted)
        # ---
        self.ocx.OnContactUnblocked[str].connect(self._OnContactUnblocked)
        # ---
        self.ocx.OnHardwareChanged[str].connect(self._OnHardwareChanged)
        # Получение детальной информации о пользователе
        self.ocx.OnDetailInfo[str].connect(self._OnDetailInfo)
        # Получение детальной информации о пользователе
        self.ocx.OnDeviceModesDone[str].connect(self._OnDeviceModesDone)    

    def __del__(self):
        print('delete CallXWidget.')
        self.ocx.shutdown()

    # =====================================================================
    # Events
    # =====================================================================
    def _OnXNotify(self, data):
        #print("**OnXNotify")
        #print(cut80symbols(data))
        pass
        
    def _OnXAfterStart(self):
        print("**OnXAfterStart")
        # Выбор устройств: просто выбираем первые в списке оборудования
        self.ocx.XSetCameraByIndex(0)
        self.ocx.XSelectMicByIndex(0)
        self.ocx.XSelectSpeakerByIndex(0)
        # соединение с сервером
        self.ocx.connectToServer(self.server)

    def _OnServerConnected(self, eventDetails):
        print("**OnServerConnected")
        print(eventDetails)
        # Авторизация
        self.ocx.login(self.user, self.password)

    def _OnLogin(self, eventDetails):
        print("**OnLogin")
        print(eventDetails)

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

    def _OnXChangeState(self, prevState, newState):
        try:
            print("**OnXChangeState {} -> {}".format(State(prevState), State(newState)))
            self.state = State(newState)
            self.prev_state = State(prevState)
            self.stateChanged.emit(State(prevState), State(newState))
            if State(newState) == State.Normal:
                self.ocx.getContactDetails(self.user) 
        except ValueError:
            pass

    def _OnXTerminate(self):
        print("**OnXTerminate")

    def _OnXStartFail(self):
        print("**OnXStartFail")

    def _OnAbookUpdate(self, eventDetails):
        print("**OnAbookUpdate")
        print(cut80symbols(eventDetails))

    def _OnAppUpdateAvailable(self, eventDetails):
        print("**OnAppUpdateAvailable")
        print(cut80symbols(eventDetails))

    def _OnChangeVideoMatrixReport(self, eventDetails):
        print("**OnChangeVideoMatrixReport")
        print(cut80symbols(eventDetails))

    def _OnConferenceCreated(self, eventDetails):
        print("**OnConferenceCreated")
        print(cut80symbols(eventDetails))

    def _OnConferenceDeleted(self, eventDetails):
        print("**OnConferenceDeleted")
        print(cut80symbols(eventDetails))

    def _OnContactBlocked(self, eventDetails):
        print("**OnContactBlocked")
        print(cut80symbols(eventDetails))

    def _OnContactDeleted(self, eventDetails):
        print("**OnContactDeleted")
        print(cut80symbols(eventDetails))

    def _OnContactUnblocked(self, eventDetails):
        print("**OnContactUnblocked")
        print(cut80symbols(eventDetails))

    def _OnHardwareChanged(self, eventDetails):
        print("**OnHardwareChanged")
        print(cut80symbols(eventDetails))

    def _OnDetailInfo(self, eventDetails):
        print("**OnDetailInfo")
        print(cut80symbols(eventDetails))

    def _OnDeviceModesDone(self, eventDetails):
        print("**OnDeviceModesDone")
        print(eventDetails)

    # =====================================================================
    # Functions
    # =====================================================================
    def getCameraList(self) -> list:
        lst = self.ocx.XGetCameraList()
        return lst.splitlines()
# end of class ActiveXExtend(QObject)
