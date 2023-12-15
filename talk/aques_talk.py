import subprocess
import configparser
import os
from talk.talker import Talker
from config.names import Confignames

class AquesTalk(Talker):
    @staticmethod
    def exist() -> bool:
        config = configparser.ConfigParser()
        config.read(Confignames.SETTING, encoding="UTF-8")
        if not os.path.isfile(config["USER"]["aquestalkPath"]):
            print("AquesTalkPlayerが見つかりませんでした")
            return False
        return True
    @staticmethod
    def launch() -> bool:
        # AquesTalkPlayerは起動不要
        if not AquesTalk.exist():
            return False
        return True
    @staticmethod
    def speak(text : str, preset : str) -> None:
        if not AquesTalk.exist():
            return
        config = configparser.ConfigParser()
        config.read(Confignames.SETTING, encoding="UTF-8")
        aquestalkPath = config["USER"]["aquestalkPath"]
        cmd = ["start", aquestalkPath, "/T", text, "/P", preset]
        subprocess.run(" ".join(cmd), shell=True)

AquesTalk.exist()