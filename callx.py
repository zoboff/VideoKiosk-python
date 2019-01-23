# coding=utf8

from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QRect, pyqtSignal
from PyQt5.QtMultimedia import *
import sys, time
from PyQt5.Qt import QVideoWidget, QUrl
from enum import Enum
from functools import wraps
import callx_events_debug
from pprint import pprint

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
    if type(s) is str:
        if (len(s) > 80):
            s = s[0:76] + '...'
    return s

def eventMarked(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.debug_mode:
            print('**{}'.format(func.__name__))
            for arg in args:
                print('  {}'.format(cut80symbols(arg)))
            # marking
            self.debug_events_marked[func.__name__] += 1

        return func(self, *args, **kwargs)

    return wrapper

# класс контейнер для ActiveX
class CallXWidget(QObject):
    # Signals
    stateChanged = pyqtSignal(object, object)
    IncomingChatMessage = pyqtSignal(object, object, object, object)

    def __init__(self, view, server: str, user: str, password: str, camera_index: int = 0, 
                 debug_mode=False):
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
        
        #debug mode
        self.debug_mode = debug_mode
        self.debug_events_marked = {}
        for event in callx_events_debug.EVENTS:
            self.debug_events_marked.setdefault(event, 0)
        
        # Создаем компонент "TrueConf SDK for Windows" aka CallX
        self.ocx = QAxWidget(TrueConfCallX_Class)

        # =====================================================================
        # подключаем некоторые события ActiveX компонента CallX
        # =====================================================================
        # Нотификация о различных событиях
        # здесь же проверим, установлен ли в системе CallX
        try:
            self.ocx.OnXNotify[str].connect(self.OnXNotify)
        except AttributeError as attrError:
            print("\nTrueConf SDK for Windows not installed.\n")
            raise 
        # Событие № 1 по очередности обработки: сигнализирует об окончании инициализации компонента
        # это событие говорит о готовности CallX к работе
        self.ocx.OnXAfterStart.connect(self.OnXAfterStart)
        # Подключились к серверу
        self.ocx.OnServerConnected[str].connect(self.OnServerConnected)
        # Авторизовались по login и password
        self.ocx.OnLogin[str].connect(self.OnLogin)
        # Пришло оповещение о звонке
        # В обработчике этого события располагается логика
        #  принятия/отклонения входящего звонка или приглашения в конференцию
        self.ocx.OnInviteReceived[str].connect(self.OnInviteReceived)
        # Сообщение об ошибке
        self.ocx.OnXError[int, str].connect(self.OnXError)
        # Ошибка авторизации
        self.ocx.OnXLoginError[int].connect(self.OnXLoginError)
        # Получили входящее собщение в Чат
        self.ocx.OnIncomingChatMessage[str, str, str, 'qulonglong'].connect(self.OnIncomingChatMessage)
        # Изменение состояния
        # Важное событие, в котором определяется текущее состояние:
        #   залогинен, в конференции и пр.
        #   эмит сигнала stateChanged 
        self.ocx.OnXChangeState[int, int].connect(self.OnXChangeState)
        # Завершение работы
        self.ocx.OnXTerminate.connect(self.OnXTerminate)
        # Ошибка загрузки
        self.ocx.OnXStartFail.connect(self.OnXStartFail)
        # Обновление списка адресной книги
        self.ocx.OnAbookUpdate[str].connect(self.OnAbookUpdate)
        # 
        self.ocx.OnAppUpdateAvailable[str].connect(self.OnAppUpdateAvailable)
        # Изменение раскладки
        self.ocx.OnChangeVideoMatrixReport[str].connect(self.OnChangeVideoMatrixReport)
        # Создание конференции
        self.ocx.OnConferenceCreated[str].connect(self.OnConferenceCreated)
        # Окончание конференции
        self.ocx.OnConferenceDeleted[str].connect(self.OnConferenceDeleted)
        # ---
        self.ocx.OnContactBlocked[str].connect(self.OnContactBlocked)
        # Удаление контакта из адресной книги
        self.ocx.OnContactDeleted[str].connect(self.OnContactDeleted)
        # ---
        self.ocx.OnContactUnblocked[str].connect(self.OnContactUnblocked)
        # ---
        self.ocx.OnHardwareChanged[str].connect(self.OnHardwareChanged)
        # Получение детальной информации о пользователе
        self.ocx.OnDetailInfo[str].connect(self.OnDetailInfo)
        # Получение детальной информации о пользователе
        self.ocx.OnDeviceModesDone[str].connect(self.OnDeviceModesDone)    
        
        self.ocx.OnIncomingRequestToPodiumAnswered[str].connect(self.OnIncomingRequestToPodiumAnswered)
        self.ocx.OnInviteRequestSent[str].connect(self.OnInviteRequestSent)
        self.ocx.OnInviteSent[str].connect(self.OnInviteSent)
        self.ocx.OnLogout[str].connect(self.OnLogout)
        self.ocx.OnReceiversInfoUpdated[str].connect(self.OnReceiversInfoUpdated)
        self.ocx.OnRecordRequest[str].connect(self.OnRecordRequest)
        self.ocx.OnRecordRequestReply[str].connect(self.OnRecordRequestReply)
        self.ocx.OnRejectReceived[str].connect(self.OnRejectReceived)
        self.ocx.OnRejectSent[str].connect(self.OnRejectSent)
        self.ocx.OnRemarkCountDown[str].connect(self.OnRemarkCountDown)
        self.ocx.OnRequestInviteReceived[str].connect(self.OnRequestInviteReceived)
        self.ocx.OnRoleChanged[str].connect(self.OnRoleChanged)
        self.ocx.OnSelfSSInfoUpdate[str].connect(self.OnSelfSSInfoUpdate)
        self.ocx.OnServerConnected[str].connect(self.OnServerConnected)
        self.ocx.OnServerDisconnected[str].connect(self.OnServerDisconnected)
        self.ocx.OnSettingsChanged[str].connect(self.OnSettingsChanged)
        self.ocx.OnSlideShowStart[str].connect(self.OnSlideShowStart)
        self.ocx.OnSlideShowStop[str].connect(self.OnSlideShowStop)
        self.ocx.OnStopCalling[str].connect(self.OnStopCalling)
        self.ocx.OnUpdateAvatar[str].connect(self.OnUpdateAvatar)
        self.ocx.OnUpdateCameraInfo[str].connect(self.OnUpdateCameraInfo)
        self.ocx.OnUpdateParticipantList[str].connect(self.OnUpdateParticipantList)
        self.ocx.OnRestrictionsChanged[str].connect(self.OnRestrictionsChanged)
        self.ocx.OnVideoMatrixChanged[str].connect(self.OnVideoMatrixChanged)
        self.ocx.OnOffHookPressed[str].connect(self.OnOffHookPressed)
        self.ocx.OnHangUpPressed[str].connect(self.OnHangUpPressed)
        self.ocx.OnJabraHookOffPressed.connect(self.OnJabraHookOffPressed)
        self.ocx.OnJabraHangUpPressed.connect(self.OnJabraHangUpPressed)
        self.ocx.OnXCommandExecution[str, str].connect(self.OnXCommandExecution)
        self.ocx.OnSlideShowInfoUpdate[str].connect(self.OnSlideShowInfoUpdate)
        self.ocx.OnStart.connect(self.OnStart)
        self.ocx.OnXLogin.connect(self.OnXLogin)
        self.ocx.OnXFileStatusChange[int, int, int].connect(self.OnXFileStatusChange)
        self.ocx.OnXFileSendError[int, int, str, str].connect(self.OnXFileSendError)
        self.ocx.OnXFileReceiveProgress[int, int, str, str].connect(self.OnXFileReceiveProgress)
        self.ocx.OnXFileReceive[str, int, str, str].connect(self.OnXFileReceive)
        self.ocx.OnXFileSend[int, str, str].connect(self.OnXFileSend)
        self.ocx.OnCommandReceived[str, str].connect(self.OnCommandReceived)
        self.ocx.OnBroadcastPictureStateChanged[str].connect(self.OnBroadcastPictureStateChanged)
        self.ocx.OnCallHistoryUpdated[str].connect(self.OnCallHistoryUpdated)
        self.ocx.OnCmdAddToAbook[str, str].connect(self.OnCmdAddToAbook)
        self.ocx.OnCmdAddToGroup[int, str].connect(self.OnCmdAddToGroup)
        self.ocx.OnCmdBlock[str].connect(self.OnCmdBlock)
        self.ocx.OnCmdChatClear[str].connect(self.OnCmdChatClear)
        self.ocx.OnCmdCreateGroup[str].connect(self.OnCmdCreateGroup)
        self.ocx.OnCmdRemoveFromAbook[str].connect(self.OnCmdRemoveFromAbook)
        self.ocx.OnCmdRemoveFromGroup[int, str].connect(self.OnCmdRemoveFromGroup)
        self.ocx.OnCmdRemoveGroup[int].connect(self.OnCmdRemoveGroup)
        self.ocx.OnCmdRenameGroup[int, str].connect(self.OnCmdRenameGroup)
        self.ocx.OnCmdRenameInAbook[str, str].connect(self.OnCmdRenameInAbook)
        self.ocx.OnCmdUnblock[str].connect(self.OnCmdUnblock)
        self.ocx.OnCommandSent[str, str].connect(self.OnCommandSent)
        self.ocx.OnFileAccepted[int].connect(self.OnFileAccepted)
        self.ocx.OnFileConferenceSent[int, str].connect(self.OnFileConferenceSent)
        self.ocx.OnFileRejected[int].connect(self.OnFileRejected)
        self.ocx.OnFileSent[int, str, str].connect(self.OnFileSent)
        self.ocx.OnFileTransferAvailable[bool].connect(self.OnFileTransferAvailable)
        self.ocx.OnGroupsUpdate[str].connect(self.OnGroupsUpdate)
        self.ocx.OnIncomingGroupChatMessage[str, str, str, 'qulonglong'].connect(self.OnIncomingGroupChatMessage)
        self.ocx.OnGroupChatMessageSent[str].connect(self.OnGroupChatMessageSent)
        self.ocx.OnChatMessageSent[str, str].connect(self.OnChatMessageSent)
        self.ocx.OnTestAudioCapturerStateUpdated[bool].connect(self.OnTestAudioCapturerStateUpdated)
        self.ocx.OnAudioCapturerRmsLevelUpdated[float].connect(self.OnAudioCapturerRmsLevelUpdated)
        self.ocx.OnToneDial[str].connect(self.OnToneDial)
        # =====================================================================

    def __del__(self):
        print('delete CallXWidget.')
        self.ocx.shutdown()

    def debug_result(self):
        file_name = 'debug_events_{}.txt'.format(time.time())
        dict_events = {k: v for k, v in self.debug_events_marked.items() if v > 0}
        with open(file_name, "a") as dbg_file_events:
            dbg_file_events.write('Was called events ++++++++++++++++++++++++++++++++\n')
            pprint(dict_events, stream=dbg_file_events)
            dict_events = {}
            dict_events = {k: v for k, v in self.debug_events_marked.items() if v == 0}
            dbg_file_events.write("Wasn't called events -----------------------------\n")
            pprint(dict_events, stream=dbg_file_events)
            print('See used/unused events info in "{}"'.format(file_name))

    # =====================================================================
    # Events
    # =====================================================================
    #@eventMarked
    def OnXNotify(self, data):
        pass
    
    @eventMarked    
    def OnXAfterStart(self):
        # Выбор устройств: просто выбираем первые в списке оборудования
        self.ocx.XSetCameraByIndex(0)
        self.ocx.XSelectMicByIndex(0)
        self.ocx.XSelectSpeakerByIndex(0)
        # соединение с сервером
        self.ocx.connectToServer(self.server)

    @eventMarked    
    def OnServerConnected(self, eventDetails):
        # Авторизация
        self.ocx.login(self.user, self.password)

    @eventMarked    
    def OnLogin(self, eventDetails):
        pass

    @eventMarked    
    def OnInviteReceived(self, eventDetails):
        # Принимаем звонок
        self.ocx.accept()

    @eventMarked    
    def OnXError(self, errorCode, errorMsg):
        pass

    @eventMarked    
    def OnXLoginError(self, errorCode):
        if errorCode == 8:
            print('Support for SDK Applications is not enabled on this server')
        else:
            print('Login error. Code: {}'.format(errorCode))

    @eventMarked    
    def OnIncomingChatMessage(self, peerId, peerDn, message, time):
        #print('From userID "{}" Display name "{}": "{}"'.format(peerId, peerDn, message))
        self.IncomingChatMessage.emit(peerId, peerDn, message, time)

    @eventMarked
    def OnXChangeState(self, prevState, newState):
        try:
            self.state = State(newState)
            self.prev_state = State(prevState)
            self.stateChanged.emit(State(prevState), State(newState))
            if State(newState) == State.Normal:
                self.ocx.getContactDetails(self.user) 
        except ValueError:
            pass

    @eventMarked
    def OnXTerminate(self):
        if self.debug_mode:
            self.debug_result()

    @eventMarked
    def OnXStartFail(self):
        pass

    @eventMarked
    def OnAbookUpdate(self, eventDetails):
        pass

    @eventMarked
    def OnAppUpdateAvailable(self, eventDetails):
        pass

    @eventMarked
    def OnChangeVideoMatrixReport(self, eventDetails):
        pass

    @eventMarked
    def OnConferenceCreated(self, eventDetails):
        pass

    @eventMarked
    def OnConferenceDeleted(self, eventDetails):
        pass

    @eventMarked
    def OnContactBlocked(self, eventDetails):
        pass

    @eventMarked
    def OnContactDeleted(self, eventDetails):
        pass

    @eventMarked
    def OnContactUnblocked(self, eventDetails):
        pass

    @eventMarked
    def OnHardwareChanged(self, eventDetails):
        pass

    @eventMarked
    def OnDetailInfo(self, eventDetails):
        pass

    @eventMarked
    def OnDeviceModesDone(self, eventDetails):
        pass

    @eventMarked
    def OnIncomingRequestToPodiumAnswered(self, eventDetails):
        pass

    @eventMarked
    def OnInviteRequestSent(self, eventDetails):
        pass

    @eventMarked
    def OnInviteSent(self, eventDetails):
        pass

    @eventMarked
    def OnLogout(self, eventDetails):
        pass

    @eventMarked
    def OnReceiversInfoUpdated(self, eventDetails):
        pass

    @eventMarked
    def OnRecordRequest(self, eventDetails):
        pass

    @eventMarked
    def OnRecordRequestReply(self, eventDetails):
        pass

    @eventMarked
    def OnRejectReceived(self, eventDetails):
        pass

    @eventMarked
    def OnRejectSent(self, eventDetails):
        pass

    @eventMarked
    def OnRemarkCountDown(self, eventDetails):
        pass

    @eventMarked
    def OnRequestInviteReceived(self, eventDetails):
        pass

    @eventMarked
    def OnRoleChanged(self, eventDetails):
        pass

    @eventMarked
    def OnSelfSSInfoUpdate(self, eventDetails):
        pass

    @eventMarked
    def OnServerDisconnected(self, eventDetails):
        pass

    @eventMarked
    def OnSettingsChanged(self, eventDetails):
        pass

    @eventMarked
    def OnSlideShowStart(self, eventDetails):
        pass

    @eventMarked
    def OnSlideShowStop(self, eventDetails):
        pass

    @eventMarked
    def OnStopCalling(self, eventDetails):
        pass

    @eventMarked
    def OnUpdateAvatar(self, eventDetails):
        pass

    @eventMarked
    def OnUpdateCameraInfo(self, eventDetails):
        pass

    @eventMarked
    def OnUpdateParticipantList(self, eventDetails):
        pass

    @eventMarked
    def OnRestrictionsChanged(self, eventDetails):
        pass

    @eventMarked
    def OnVideoMatrixChanged(self, eventDetails):
        pass

    @eventMarked
    def OnOffHookPressed(self, eventDetails):
        pass

    @eventMarked
    def OnHangUpPressed(self, eventDetails):
        pass
    
    @eventMarked
    def OnJabraHookOffPressed(self):
        pass

    @eventMarked
    def OnJabraHangUpPressed(self):
        pass

    @eventMarked
    def OnXCommandExecution(self, cmdName: str, allData: str):
        pass

    @eventMarked
    def OnSlideShowInfoUpdate(self, eventDetails: str):
        pass

    @eventMarked
    def OnStart(self):
        pass

    @eventMarked
    def OnXLogin(self):
        pass

    @eventMarked
    def OnXFileStatusChange(self, fileId: int, fileStatus: int, directionType: int):
        pass
    
    @eventMarked
    def OnXFileSendError(self, error_code, fileId: int, filePath: str, fileCaption: str):
        pass
    
    @eventMarked
    def OnXFileReceiveProgress(self, percent: int, fileId: int, fileName: str, fileCaption: str):
        pass
    
    @eventMarked
    def OnXFileReceive(self, peerId: str, fileId: int, fileName: str, fileCaption: str):
        pass
    
    @eventMarked
    def OnXFileSend(self, fileId, filePath: str, fileCaption: str):
        pass
    
    @eventMarked
    def OnCommandReceived(self, peerId: str, command: str):
        pass
    
    @eventMarked
    def OnBroadcastPictureStateChanged(self, filename: str):
        pass
    
    @eventMarked
    def OnCallHistoryUpdated(self, jsonCallHistory: str):
        pass
    
    @eventMarked
    def OnCmdAddToAbook(self, peerId: str, peerDn: str):
        pass
    
    @eventMarked
    def OnCmdAddToGroup(self, groupId: int, peerId: str):
        pass
    
    @eventMarked
    def OnCmdBlock(self, peerId: str):
        pass
    
    @eventMarked
    def OnCmdChatClear(self, chatId: str):
        pass
    
    @eventMarked
    def OnCmdCreateGroup(self, groupName: str):
        pass
    
    @eventMarked
    def OnCmdRemoveFromAbook(self, peerId: str):
        pass
    
    @eventMarked
    def OnCmdRemoveFromGroup(self, groupId: int, peerId: str):
        pass
    
    @eventMarked
    def OnCmdRemoveGroup(self, groupId: int):
        pass
    
    @eventMarked
    def OnCmdRenameGroup(self, groupId: int, groupName: str):
        pass
    
    @eventMarked
    def OnCmdRenameInAbook(self, peerId: str, peerDn: str):
        pass
    
    @eventMarked
    def OnCmdUnblock(self, peerId: str):
        pass
    
    @eventMarked
    def OnCommandSent(self, peerId: str, command: str):
        pass
    
    @eventMarked
    def OnFileAccepted(self, fileId: int):
        pass
    
    @eventMarked
    def OnFileConferenceSent(self, fileId: int, fileName: int):
        pass
    
    @eventMarked
    def OnFileRejected(self, fileId: int):
        pass
    
    @eventMarked
    def OnFileSent(self, fileId: int, fileName: str, peerId: str):
        pass
    
    @eventMarked
    def OnFileTransferAvailable(self, available: bool):
        pass
    
    @eventMarked
    def OnGroupsUpdate(self, jsonGroupList: str):
        pass
    
    @eventMarked
    def OnIncomingGroupChatMessage(self, peerId: str, peerDn: str, message: str, time: 'qulonglong'):
        pass
    
    @eventMarked
    def OnGroupChatMessageSent(self, message: str):
        pass
    
    @eventMarked
    def OnChatMessageSent(self, peerId: str, message: str):
        pass
    
    @eventMarked
    def OnTestAudioCapturerStateUpdated(self, started: bool):
        pass
    
    @eventMarked
    def OnAudioCapturerRmsLevelUpdated(self, lvl: float):
        pass
    
    @eventMarked
    def OnToneDial(self, symbol: str):
        pass

    # =====================================================================
    # Functions
    # =====================================================================
    def getCameraList(self) -> list:
        lst = self.ocx.XGetCameraList()
        return lst.splitlines()
# end of class ActiveXExtend(QObject)
