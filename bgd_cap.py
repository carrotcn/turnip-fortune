import win32gui,win32con
import win32ui
from ctypes import windll
from PIL import Image
import time

class cl_bgd_cap:
    def __init__(self):
        # Tested with Elgato 4k capture utility 1.7.6
        self.hwnd = win32gui.FindWindow(None, '4k capture utility')
        win32gui.ShowWindow(self.hwnd,win32con.SW_RESTORE)
        time.sleep(0.2)
        left, top, right, bot = win32gui.GetWindowRect(self.hwnd)
        win32gui.MoveWindow(self.hwnd, left, top, 1280, 808, True)
        left, top, right, bot = win32gui.GetWindowRect(self.hwnd)
        w = right - left
        h = bot - top

        self.hwndDC = win32gui.GetWindowDC(self.hwnd)
        self.mfcDC  = win32ui.CreateDCFromHandle(self.hwndDC)
        self.saveDC = self.mfcDC.CreateCompatibleDC()

        self.saveBitMap = win32ui.CreateBitmap()
        self.saveBitMap.CreateCompatibleBitmap(self.mfcDC, w, h)

        self.saveDC.SelectObject(self.saveBitMap)

    def close(self):
        win32gui.DeleteObject(self.saveBitMap.GetHandle())
        self.saveDC.DeleteDC()
        self.mfcDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, self.hwndDC)

    def getIM(self):
        result = windll.user32.PrintWindow(self.hwnd, self.saveDC.GetSafeHdc(), 0)
        #print(result)

        bmpinfo = self.saveBitMap.GetInfo()
        bmpstr = self.saveBitMap.GetBitmapBits(True)

        im = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)

        if result == 1:
            return im
        else:
            return None
    
    def showWindow(self):
        win32gui.ShowWindow(self.hwnd,win32con.SW_RESTORE)
        time.sleep(0.2)
