import requests
import configparser
import subprocess
import simpleaudio
import time
import os
from talk.talker import Talker
from config.names import Confignames
from config.configcontrol import ConfigController
from datetime import datetime
import re

class CoeiroinkTalk(Talker):
    @staticmethod
    def exist() -> bool:
        config = configparser.ConfigParser()
        config.read(Confignames.SETTING, encoding="UTF-8")
        if not os.path.isfile(config["USER"]["coeiroinkPath"]):
            print("COEIROINKが見つかりませんでした")
            return False
        return True
    @staticmethod
    def launch() -> bool:
        if not CoeiroinkTalk.exist():
            return False
        try:
            boot = requests.get("http://localhost:50032/")
        except requests.exceptions.ConnectionError:
            # iniファイル読み込み
            config = configparser.ConfigParser()
            config.read(Confignames.SETTING, encoding="UTF-8")
            subprocess.Popen(config["USER"]["coeiroinkPath"])
        return True
    @staticmethod
    def speakers() -> requests.Response:
        return requests.get("http://localhost:50032/v1/speakers")
    # style_idは各キャラのメタ情報に記載されている他、model内のフォルダ名と関連している
    # speaker_uuidはキャラごとのユニークなIDで、各キャラのメタ情報に記載されている他、speaker_info内のフォルダ名と関連している
    @staticmethod
    def speak(text : str, style_id : int, speaker_uuid : str | None = None, speaker_name = "noname", framerate = 24000, param_dict : dict | None = None):
        configc = ConfigController()
        def save(wave_data):
            # パス整形
            voice_out_dir = os.path.dirname(configc.read("voiceOutputDirectory"))
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            sliced_text = text[:10]
            sliced_text = re.sub(r'[\\/:*?"<>|]+', '' , sliced_text)
            path = f"{voice_out_dir}\\{timestamp}_{speaker_name}_{sliced_text}"
            # 保存
            try:
                wr = open(f"{path}.wav", "wb")
                wr.write(wave_data)
                wr.close()
                # with wave.open(f"{path}.wav", "wb") as f:
                #     f.setnchannels(2)   # チャンネル数
                #     f.setframerate(framerate)   # サンプリングレート
                #     f.setsampwidth(1)
                #     f.close()
                with open(f"{path}.txt", mode="w", encoding="UTF-8", newline="") as f:
                    f.write(text)
            except Exception as e:
                print(e)

        if not CoeiroinkTalk.exist():
            return
        # UUIDが渡されなかった
        if speaker_uuid == None:
            # speakerのメタ情報(COEIROINK speaker_infoのmeta.jsonを取得)
            speaker_meta = requests.post(f"http://localhost:50032/v1/style_id_to_speaker_meta?styleId={style_id}")
            # pprint.pprint(speaker_meta.json())
            speaker_uuid = speaker_meta.json()["speakerUuid"]
        # 音素情報の取得
        prosody_dict = {"text" : text}
        # まだ起動が終わっていない場合を考えて複数回試行する
        i = 0
        while i < 10:
            try:
                prosody = requests.post("http://localhost:50032/v1/estimate_prosody", json=prosody_dict)
                break
            except requests.exceptions.ConnectionError:
                i = i + 1
                time.sleep(1)
            if i == 9:
                # 接続に失敗したためspeak処理終了
                return
        
        # pprint.pprint(prosody.json())
        prosody_detail = prosody.json()["detail"]
        # 合成に必要なパラメータの設定
        synthesis_data = {
            "speakerUuid": speaker_uuid,
            "styleId": str(style_id),
            "text": text,
            "prosodyDetail": prosody_detail,
            "speedScale": param_dict["speed"],
            "volumeScale": param_dict["volume"],
            "pitchScale": param_dict["pitch"],
            "intonationScale": param_dict["intonation"],
            "prePhonemeLength": param_dict["prePhoneme"],
            "postPhonemeLength": param_dict["postPhoneme"],
            "outputSamplingRate": framerate
        }
        # wavをバイナリで受け取る
        resp_wav : requests.Response = requests.post("http://localhost:50032/v1/synthesis", json=synthesis_data)
        data_binary : bytes = resp_wav.content
        save(data_binary)
        wav_obj = simpleaudio.WaveObject(data_binary, 1, 2, framerate)
        wav_obj.play()