import requests
import subprocess
import configparser
import simpleaudio
import os
from talk.talker import Talker
from config.names import Confignames
from config.configcontrol import ConfigController
import json
from datetime import datetime
import re
import wave

class VoicevoxTalk(Talker):
    @staticmethod
    def exist() -> bool:
        config = configparser.ConfigParser()
        config.read(Confignames.SETTING, encoding="UTF-8")
        if not os.path.isfile(config["VOICEVOX"]["voicevoxPath"]):
            print("VOICEVOXが見つかりませんでした")
            return False
        return True
    @staticmethod
    def launch() -> bool:
        # VoicevoxTalk.speakers()
        if not VoicevoxTalk.exist():
            return False
        try:
            boot = requests.get("http://127.0.0.1:50021/version")
        except requests.exceptions.ConnectionError:
            # iniファイル読み込み
            config = configparser.ConfigParser()
            config.read(Confignames.SETTING, encoding="UTF-8")
            subprocess.Popen(config["VOICEVOX"]["voicevoxPath"])
        return True
    @staticmethod
    def speak(text : str, speaker : int, speaker_name = "noname", framerate = 24000, param_dict : dict | None = None):
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
        # もしVOICEVOXが見つからないなら処理終了
        if not VoicevoxTalk.exist():
            return
        response : requests.Response = requests.post(f"http://127.0.0.1:50021/audio_query?text={text}&speaker={speaker}")
        response_dict = response.json()
        response_dict["speedScale"] = param_dict["speed"]
        response_dict["pitchScale"] = param_dict["pitch"]
        response_dict["intonationScale"] = param_dict["intonation"]
        response_dict["volumeScale"] = param_dict["volume"]
        response_dict["prePhonemeLength"] = param_dict["prePhoneme"]
        response_dict["postPhonemeLength"] = param_dict["postPhoneme"]
        # response_dict["outputStereo"] = param_dict["stereo"]
        response_dict["outputSamplingRate"] = framerate
        resp_wav : requests.Response = requests.post(f"http://127.0.0.1:50021/synthesis?speaker={speaker}", json=response_dict)
        data_binary : bytes = resp_wav.content
        if configc.read("writeVoice").lower() == "True".lower():
            save(data_binary)
        wav_obj = simpleaudio.WaveObject(data_binary, 2, 2, framerate)
        wav_obj.play()

    def speakers_write():
        response = requests.get("http://127.0.0.1:50021/speakers")
        # with open("voicevoxspeakers.json", "w", encoding="UTF-8") as f:
        #     json.dump(response.json(), f, ensure_ascii=False, indent=4)
        json_dict = response.json()
        lines = []
        for d in json_dict:
            line = [d["name"], d["styles"]]
            lines.append(line)
        with open("voicevox_speakers.txt", "w", encoding="UTF-8") as f:
            for line in lines:
                for l in line:
                    f.write(str(l))
                f.write("\n")