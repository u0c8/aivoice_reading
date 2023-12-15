import configparser
import pythonnet
import clr
import os
import threading
from talk.talker import Talker
from datetime import datetime
import re

# このファイル内でのみ使用される
class aivoiceEditor():
    def __init__(self, aivoice_path : str | None = None) -> None:
        _editor_dir = ""
        if aivoice_path is None:
            # iniファイル読み込み
            # config = configparser.ConfigParser()
            # config.read(Confignames.SETTING, encoding="UTF-8")
            # _editor_dir = config["USER"]["aivoiceEditorPath"]
            pass
        else:
            _editor_dir = os.path.dirname(aivoice_path) + "\\"

        if not os.path.isfile(_editor_dir + 'AI.Talk.Editor.Api.dll'):
            print("A.I.VOICE Editor (v1.3.0以降) がインストールされていません。")
            return

        # pythonnet DLLの読み込み
        clr.AddReference(_editor_dir + "AI.Talk.Editor.Api")
        from AI.Talk.Editor.Api import TtsControl, HostStatus

        self.tts_control = TtsControl()

        # A.I.VOICE Editor APIの初期化
        host_name = self.tts_control.GetAvailableHostNames()[0]
        self.tts_control.Initialize(host_name)

        # A.I.VOICE Editorの起動
        if self.tts_control.Status == HostStatus.NotRunning:
            self.tts_control.StartHost()

class AIVoiceTalk(Talker):
    def __init__(self, aivoice_path : str | None = None, output_path : str | None = None, write_flag : bool = False) -> None:
        super().__init__()
        self.aivoice_path = aivoice_path
        self.output_path = output_path
        self.write_flag = write_flag

    def exist(self) -> bool:
        if self.aivoice_path is None:
            return False
        _editor_dir = self.aivoice_path
        if not os.path.isfile(_editor_dir + 'AI.Talk.Editor.Api.dll'):
            print("A.I.VOICE Editorが見つかりませんでした")
            return False
        return True

    def initialize(self) -> aivoiceEditor:
        return aivoiceEditor(aivoice_path=self.aivoice_path)

    def launch(self) -> bool:
        th = threading.Thread(target=self.initialize)
        th.start()
        return self.exist()

    def speak(self, text : str, speaker : str | None = None, speaker_name = "noname"):
        # speakの途中で呼ばれる
        def save():
            if self.output_path is None:
                return
            # パス整形
            voice_out_dir = os.path.dirname(self.output_path)
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            sliced_text = text[:10]
            sliced_text = re.sub(r'[\\/:*?"<>|]+', '' , sliced_text)
            path = f"{voice_out_dir}\\{timestamp}_{speaker_name}_{sliced_text}"
            # 保存
            try:
                # 合成結果をファイルに保存する
                aivoice.tts_control.SaveAudioToFile(f"{path}.wav")
                with open(f"{path}.txt", mode="w", encoding="UTF-8", newline="") as f:
                    f.write(text)
            except Exception as e:
                print(e)
        if speaker == "":
            pass
        aivoice = aivoiceEditor(self.aivoice_path)
        # 接続
        aivoice.tts_control.Connect()
        if speaker is not None:
            # プリセット上書き
            aivoice.tts_control.CurrentVoicePresetName = speaker
        # テキスト設定
        aivoice.tts_control.Text = text
        aivoice.tts_control.TextSelectionStart = 0
        # パラメータ取得
        # JSON形式でVolume, Speed, Pitch, PitchRange, MiddlePause, LongPause, SentencePauseを実数値で指定 最小値最大値はエディター準拠 PitchRangeは抑揚
        master_param = aivoice.tts_control.MasterControl
        # print(master_param)
        # パラメータ設定
        if self.write_flag:
            save()
        # 再生
        aivoice.tts_control.Play()
        # time.sleep((aivoice.tts_control.GetPlayTime() + 500) / 1000)
        # 切断
        aivoice.tts_control.Disconnect()

# aivoice = AIVoiceTalk()
# aivoice.speak("こんにちは")