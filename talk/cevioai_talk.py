import configparser
import clr
import os
import threading
from talk.talker import Talker
from config.names import Confignames
from other.process_find import now_ps_find

class CeVIOAIEditor():
    def __init__(self) -> None:
        config = configparser.ConfigParser()
        config.read(Confignames.SETTING, encoding="UTF-8")
        cevioai_path = config["USER"]["cevioaiPath"]
        # pythonnet DLLの読み込み
        clr.AddReference(cevioai_path + "CeVIO.Talk.RemoteService2.dll")
        import CeVIO.Talk.RemoteService2

        # // 【CeVIO AI】起動
        # 起動されてない時だけ
        if not now_ps_find("cevio ai"):
            CeVIO.Talk.RemoteService2.ServiceControl2.StartHost(False)

        # // Talkerインスタンス生成
        self.talker = CeVIO.Talk.RemoteService2.Talker2()

        # // （例）音量設定
        self.talker.Volume = 100

        # // （例）抑揚設定
        self.talker.ToneScale = 100

class CeVIOAITalk(Talker):
    @staticmethod
    def exist() -> bool:
        config = configparser.ConfigParser()
        config.read(Confignames.SETTING, encoding="UTF-8")
        cevioai_path = config["USER"]["cevioaiPath"]
        if os.path.exists(cevioai_path + "CeVIO.Talk.RemoteService2.dll"):
            return True
        return False
    @staticmethod
    def initialize():
        CeVIOAIEditor()
    @staticmethod
    def launch() -> bool:
        th = threading.Thread(target=CeVIOAITalk.initialize)
        th.start()
        return CeVIOAITalk.exist()
    @staticmethod
    def speak(text : str, speaker : str = ""):
        cevio = CeVIOAIEditor()
        # キャスト設定
        cevio.talker.Cast = speaker
        # 再生
        state = cevio.talker.Speak(text)