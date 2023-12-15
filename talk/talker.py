from abc import ABCMeta, abstractmethod
class Talker(metaclass = ABCMeta):
    @abstractmethod
    def exist() -> bool:
        pass
    @abstractmethod
    def launch() -> bool:
        pass
    @abstractmethod
    def speak(text : str, speaker : int | str = 0, speaker_name = "noname"):
        # speakerはAquesTalkのみ文字列指定
        # 最低構成でしゃべらせる
        pass