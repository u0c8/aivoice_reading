from collections.abc import Callable, Iterable, Mapping
from typing import Any
from pystray import Icon, MenuItem, Menu
from PIL import Image
import time
import threading
from ctypes import *          # windll 使用のため
from ctypes.wintypes import * # handle取得のため
import ctypes
import win32api,win32gui,win32con # win32のAPI使用のため
import pyperclip
from talk.talker import Talker
from talk.aivoice_talk import AIVoiceTalk
import sys
import argparse
import base64
from io import BytesIO
import traceback

# 参考にした記事
# タスクトレイ常駐部分
# https://qiita.com/bassan/items/3025eeb6fd2afa03081b
# ホットキー部分
# https://niyanmemo.com/1973/

class RaiseableThread(threading.Thread):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._run = self.run
        self.run = self.set_id_and_run

    def set_id_and_run(self):
        self.id = threading.get_native_id()
        self._run()

    def get_id(self):
        return self.id
        
    def raise_exception(self):
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.get_id()), 
            ctypes.py_object(SystemExit)
        )
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(self.get_id()), 
                0
            )
            print('Failure in raising exception')

class taskTray:
    def __init__(self, image, argv):
        self.status = False

        aparser = argparse.ArgumentParser(description="You can set preset.\nプリセット指定をしない場合、引数はつけないでください。")
        # aparser.add_argument('--voicetype', '-t', help='Input voice type. AIVOICE, AQUESTALK, VOICEVOX, COEIROINK')
        aparser.add_argument('--aivoicedir', help='Please input A.I.Voice Editor directory', required=True)
        aparser.add_argument('--auto', '-a', help='If true, watchdog monitors clipboard and speaks', default=False)
        aparser.add_argument('--preset', '-p', help='Input preset name', default=None)

        args = aparser.parse_args(args=argv)
        self.auto_speak_flag = args.auto.encode("utf-8").decode().lower() == "true"
        self.aivoice_path = args.aivoicedir.encode("utf-8").decode()
        self.preset = args.preset
        if args.preset is not None:
            self.preset = args.preset.encode("utf-8").decode()

        ## アイコンの画像
        if type(image) == str:
            image = Image.open(image)
        ## 右クリックで表示されるメニュー
        menu = self.generate_menu()
        self.icon = Icon(name='aivoice_reading', title='アイボスリーディング', icon=image, menu=menu)

        self.talker : Talker = AIVoiceTalk(aivoice_path=self.aivoice_path)

        #ホットキーIDは このプログラムで使用するための物なので適当な値を設定する
        #0x0000-0xBFFFの間で設定
        self.HOTKEY_ID_1 = 0x0001
        self.exit_flg = False

        # ホットキー入力受付スレッド
        self.hotkey_thread = RaiseableThread(target=self.Regist_selfhotkey)

    def stopProgram(self, icon):
        self.status = False
        ## 停止
        self.icon.stop()
        self.hotkey_thread.raise_exception()
        # self.hotkey_thread.join()

    def runProgram(self):
        self.status = True
        self.hotkey_thread.start()
        ## 実行
        self.icon.run()

    def switch_auto_speak(self):
        self.auto_speak_flag = not self.auto_speak_flag
        self.icon.menu = self.generate_menu()

    def generate_menu(self) -> Menu:
        return Menu(
            MenuItem('読み上げ', self.run_hotkey),
            MenuItem('自動読み上げ / オン', self.switch_auto_speak, visible=self.auto_speak_flag),
            MenuItem('自動読み上げ / オフ', self.switch_auto_speak, visible=not self.auto_speak_flag),
            MenuItem('Exit', self.stopProgram),
        )

    def Regist_selfhotkey(self):
        try:
            hInstance  = win32api.GetModuleHandle(None)
            CLASS_NAME   = "aivoiceReading"
            lpWindowName = CLASS_NAME
            
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self.WindowProc
            wc.hInstance = hInstance
            wc.lpszClassName = CLASS_NAME
            win32gui.RegisterClass(wc)
            
            hwnd = win32gui.CreateWindowEx(0,CLASS_NAME,lpWindowName,win32con.WS_OVERLAPPEDWINDOW,
                                        win32con.CW_USEDEFAULT,win32con.CW_USEDEFAULT,win32con.CW_USEDEFAULT,
                                        win32con.CW_USEDEFAULT,None,None,hInstance,None)
            
            if hwnd != None:
                mod_key = win32con.MOD_SHIFT + win32con.MOD_ALT + win32con.MOD_CONTROL
                windll.user32.RegisterHotKey(hwnd,self.HOTKEY_ID_1, mod_key,0x43)

            msg = MSG()
            recent_value = pyperclip.paste()
            while True:
                # クリップボードを監視
                tmp_value = pyperclip.paste()
                if self.auto_speak_flag and tmp_value != recent_value:
                    recent_value = tmp_value
                    try:
                        # 連投するとホストがビジーとかでSystem.InvalidOperationExceptionが返ってきて止まる対策
                        self.talker.speak(recent_value, self.preset)
                    except Exception as e:
                        traceback.print_exc()
                # Peekでメッセージが来ているときのみ処理(メインスレッドと同期するため)
                if windll.user32.PeekMessageW(pointer(msg), None, 0,0,win32con.PM_NOREMOVE):
                    windll.user32.GetMessageW(pointer(msg),0,0,0)
                    windll.user32.TranslateMessage(pointer(msg))
                    windll.user32.DispatchMessageW(pointer(msg))
                if self.status == False:
                    break
                time.sleep(0.2)
        finally:
            windll.user32.UnregisterHotKey(None,self.HOTKEY_ID_1)    
        
    def WindowProc(self, hwnd,uMsg,wParam,lPram):
        if self.status == False:
            raise Exception("Thread not finish")
        if uMsg == win32con.WM_HOTKEY:
            if wParam == self.HOTKEY_ID_1:
                self.run_hotkey()
        return windll.user32.DefWindowProcW(hwnd,uMsg,wParam,lPram)

    def run_hotkey(self):
        text = pyperclip.paste()
        try:
            # 連投するとホストがビジーとかでSystem.InvalidOperationExceptionが返ってきて止まる対策
            self.talker.speak(text, self.preset)
        except Exception as e:
            traceback.print_exc()

def base64_to_pil(img_str):
    if "base64," in img_str:
        # DARA URI の場合、data:[<mediatype>][;base64], を除く
        img_str = img_str.split(",")[1]
    img_raw = base64.b64decode(img_str)
    img = Image.open(BytesIO(img_raw))

    return img

def icon_base64():
    return "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"

def main():
    # sys.stdout = open('./tmp.txt', 'w')
    # sys.stderr = open('./error.txt', 'w')
    win32api.SetConsoleTitle("aivoice_reading")
    system_tray = taskTray(image=base64_to_pil(icon_base64()), argv=sys.argv[1:])
    system_tray.runProgram()

if __name__ == '__main__':
    main()
    print("終了")