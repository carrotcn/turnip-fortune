import time
import pytesseract
import traceback
from PIL import Image
import winsound

from PIL import ImageGrab
import win32gui, win32con
import win32com.client
import win32ui
from ctypes import windll
import sys

from signal import signal, SIGINT

import datetime,calendar
import clipboard
import requests
import json
import base64
import pyautogui
import serial
import logging
import os
import multiprocessing
import re
import cv2
import numpy
from skimage.metrics import structural_similarity as ssim

from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

import easyocr

#from matplotlib import pyplot as plt

import platform
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import configparser

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from bgd_cap import cl_bgd_cap
from dodoapp_api import DODOApp_API
from dodoapp_logger import dodoapp_island_queue_logger

class cl_xcx_cap:
    def __init__(self):
        self.hwnd = None
        self.shell = win32com.client.Dispatch("WScript.Shell")

    def getIM(self):
        left, top, right, bot = win32gui.GetWindowRect(self.hwnd)
        return pyautogui.screenshot(region=(left, top, right-left, bot-top))

    def showWindow(self):
        #to prevent this exception in SetAsForegroundWindow: 'No error message is available'
        self.shell.SendKeys('%')
        win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(self.hwnd)
        time.sleep(0.2)

    def getPos(self):
        left, top, right, bot = win32gui.GetWindowRect(self.hwnd)
        return (left, top)

    def getRefPos(self, ref_img_path):
        img = cv2.cvtColor(numpy.array(self.getIM()), cv2.COLOR_BGR2GRAY)
        img_ref = cv2.cvtColor(cv2.imread(ref_img_path), cv2.COLOR_BGR2GRAY)
        w, h = img_ref.shape[::-1]
        res = cv2.matchTemplate(img, img_ref, cv2.TM_CCOEFF_NORMED)
        threshold = 0.95
        loc = numpy.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            #just one box is enough...so just return...
            return pt
        return (-1, -1)

class cl_DODOApp_cap(cl_xcx_cap):
    def __init__(self):
        self.hwnd = win32gui.FindWindow(None, 'DoDo App')
        self.shell = win32com.client.Dispatch("WScript.Shell")
        win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)

    def sendMsg(self, msg):
        mouse_x, mouse_y = pyautogui.position()
        self.showWindow()
        left, top = self.getPos()
        ref_x, ref_y = self.getRefPos(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'ref_img','DODOApp_txtComment.jpg']))
        if ref_x < 0 or ref_y < 0:
            logger.critical('DODOApp: Comment textbox not found!!! Exiting to prevent further damage...')
            sys.exit(0)
        pyautogui.click(x=left + ref_x + 30, y=top + ref_y + 5)
        time.sleep(0.8)
        #we cannot use pyautogui to type unicode characters so will be using clipboard as a workaround
        clipboard.copy(msg)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.hotkey("del")
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.2)
        
        ref_x, ref_y = self.getRefPos(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'ref_img','DODOApp_btnSend.jpg']))
        if ref_x < 0 or ref_y < 0:                
            logger.critical('Send button not found!!! Exiting to prevent further damage...')
            sys.exit(0)
        pyautogui.click(x=left + ref_x + 35, y=top + ref_y + 24)
        pyautogui.hotkey('alt', 'tab')
        pyautogui.moveTo(mouse_x, mouse_y)

    def updateIsland(self, newDODO=None):
        # For DODOApp we do not need to force the update just for the sake of the extension
        if newDODO is None:
            return
        self.showWindow()
        time.sleep(1)
        left, top = self.getPos()
        pyautogui.click(left + 7, top + 120)
        pyautogui.press('pageup')
        time.sleep(0.5)
        pyautogui.press('pageup')
        time.sleep(0.5)
        pyautogui.press('pageup')
        time.sleep(0.5)
        pyautogui.press('pageup')
        time.sleep(0.5)
        ref_x, ref_y = self.getRefPos(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'ref_img','DODOApp_btnChangePwd.jpg']))
        if ref_x < 0 or ref_y < 0:
            logger.critical('DODOApp: Pwd change button not found!!! Exiting to prevent further damage...')
            sys.exit(0)
        pyautogui.click(x=left + ref_x, y=top + ref_y)
        time.sleep(2)
        ref_x, ref_y = self.getRefPos(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'ref_img','DODOApp_lblPwd.jpg']))
        if ref_x < 0 or ref_y < 0:
            logger.critical('DODOApp: Label for DODO code not found!!! Exiting to prevent further damage...')
            sys.exit(0)
        #here we still need the additional offset,
        # as we are actually locating the radio button which is one section above the password text box
        if newDODO is not None:
            pyautogui.click(x=left + ref_x + 200, y=top + ref_y + 15)
            clipboard.copy(newDODO)
            pyautogui.hotkey("ctrl", "a")
            pyautogui.hotkey("del")
            pyautogui.hotkey("ctrl", "v")
            time.sleep(1)
        left, top = self.getPos()
        ref_x, ref_y = self.getRefPos(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'ref_img','DODOApp_btnConfirmChange.jpg']))
        if ref_x < 0 or ref_y < 0:
            logger.critical('DODOApp: Confirm change button not found!!! Exiting to prevent further damage...')
            sys.exit(0)
        pyautogui.click(x=left + ref_x, y=top + ref_y)
        time.sleep(1)
        
        time.sleep(3)#wait for the page to get back to island detail
        # if newDODO is not None:
        #     self.sendMsg(u'[喵] 呼...机场已恢复开放~请刷新页面获取最新密码~（趴...')
        # else:
        #     #sendMsg(quanquan_capture, u'[喵] +3600s')
        #     pass
    
    def closeIsland(self):
        # For DODOApp we do not explicitly close the island.
        # Instead, we rely on manual setup of the closing time
        # when creating the island in app.
        logger.info('Island closed. Exiting...')
        sys.exit(0)

class cl_quanquan_cap(cl_xcx_cap):
    def __init__(self):
        self.hwnd = win32gui.FindWindow(None, u'动森圈圈')
        self.shell = win32com.client.Dispatch("WScript.Shell")
        win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)

    def sendMsg(self, msg):
        mouse_x, mouse_y = pyautogui.position()
        self.showWindow()
        left, top = self.getPos()
        iCount = 0
        pyautogui.click(left + 7, top + 120)
        pyautogui.press('home')
        time.sleep(0.8)
        while True:
            ref_x, ref_y = self.getRefPos(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'ref_img','btnSend.jpg']))
            if ref_x < 0 or ref_y < 0:                
                if iCount <= 2:
                    pyautogui.click(left + 7, top + 120)
                    pyautogui.press('pagedown')
                    time.sleep(0.5)
                    iCount += 1
                    continue
                else:
                    logger.critical('Send button not found!!! Exiting to prevent further damage...')
                    sys.exit(0)
            break
        pyautogui.click(x=left + ref_x - 200, y=top + ref_y + 10)
        #we cannot use pyautogui to type unicode characters so will be using clipboard as a workaround
        clipboard.copy(msg)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.hotkey("del")
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.2)
        pyautogui.click(x=left + ref_x, y=top + ref_y)
        pyautogui.hotkey('alt', 'tab')
        pyautogui.moveTo(mouse_x, mouse_y)

    def updateIsland(self, newDODO=None):
        global g_lastRestart
        self.showWindow()
        time.sleep(1)
        left, top = self.getPos()
        pyautogui.click(left + 7, top + 120)
        pyautogui.press('pageup')
        time.sleep(0.5)
        pyautogui.press('pageup')
        time.sleep(0.5)
        pyautogui.press('pageup')
        time.sleep(0.5)
        pyautogui.press('pageup')
        time.sleep(0.5)
        ref_x, ref_y = self.getRefPos(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'ref_img','btnChangeIsland.jpg']))
        if ref_x < 0 or ref_y < 0:
            logger.critical('Island Change button not found!!! Exiting to prevent further damage...')
            sys.exit(0)
        pyautogui.click(x=left + ref_x, y=top + ref_y)
        time.sleep(1)
        pyautogui.click(x=left + ref_x, y=top + ref_y)
        time.sleep(2)
        ref_x, ref_y = self.getRefPos(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'ref_img','btnPwd.jpg']))
        if ref_x < 0 or ref_y < 0:
            logger.critical('Textbox for DODO code not found!!! Exiting to prevent further damage...')
            sys.exit(0)
        #here we still need the additional offset,
        # as we are actually locating the radio button which is one section above the password text box
        if newDODO is not None:
            pyautogui.click(x=left + ref_x + 266, y=top + ref_y + 60)
            pyautogui.press('backspace')
            pyautogui.press('backspace')
            pyautogui.press('backspace')
            pyautogui.press('backspace')
            pyautogui.press('backspace')
            pyautogui.press('delete')
            pyautogui.press('delete')
            pyautogui.press('delete')
            pyautogui.press('delete')
            pyautogui.press('delete')
            #clipboard.set(string)
            pyautogui.write(newDODO)
        pyautogui.press('pagedown')
        pyautogui.press('pagedown')
        time.sleep(1)
        pyautogui.click(x=left+210, y=top+685)
        time.sleep(2)
        pyautogui.click(x=left+210, y=top+685)
        time.sleep(2)
        pyautogui.click(x=left+210, y=top+685)
        time.sleep(2)
        left, top = self.getPos()
        ref_x, ref_y = self.getRefPos(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'ref_img','btnAgree.jpg']))
        if ref_x < 0 or ref_y < 0:
            logger.critical('Agree button not found!!! Exiting to prevent further damage...')
            sys.exit(0)
        pyautogui.click(x=left + ref_x, y=top + ref_y)
        time.sleep(5)#wait for the page to get back to island detail
        # if newDODO is not None:
        #     self.sendMsg(self, u'[喵] 呼...机场已恢复开放~请刷新页面获取最新密码~（趴...')
        # else:
        #     #self.sendMsg(self, u'[喵] +3600s')
        #     pass
        g_lastRestart = int(time.monotonic())

    def closeIsland(self):
        self.showWindow()
        time.sleep(1)
        left, top = self.getPos()
        pyautogui.click(left + 7, top + 120)
        pyautogui.press('pageup')
        time.sleep(0.5)
        pyautogui.press('pageup')
        time.sleep(0.5)
        pyautogui.press('pageup')
        time.sleep(0.5)
        pyautogui.press('pageup')
        time.sleep(0.5)
        ref_x, ref_y = self.getRefPos(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'ref_img','btnCloseIsland.jpg']))
        if ref_x < 0 or ref_y < 0:
            logger.critical('Island Close button not found!!! Exiting to prevent further damage...')
            sys.exit(0)
        pyautogui.click(x=left + ref_x, y=top + ref_y)
        time.sleep(1)
        pyautogui.click(x=left + ref_x, y=top + ref_y)
        time.sleep(2)
        ref_x, ref_y = self.getRefPos(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'ref_img','btnConfirmClosure.jpg']))
        if ref_x < 0 or ref_y < 0:
            logger.critical('Confirm Closure button not found!!! Exiting to prevent further damage...')
            sys.exit(0)
        pyautogui.click(x=left + ref_x, y=top + ref_y)
        logger.info('Quanquan island closed. Exiting...')
        
        sys.exit(0)

class CustomLogHandler(logging.Handler):
    def emit(self, record):
        body = self.format(record)
        if '- CRITICAL -' in body:
            sendMail(config['DEV_MAIL_RECIPIENT'],'Reopen_island ABENDED!!!', body)
        return 0

def getOCR(filename, language_type='CHN_ENG', engine='easyocr'):
    try:
        if engine == 'baidu':
            # Fetch access token only once for every execution.
            try:
                access_token = getOCR.at
            except AttributeError:
                host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials' + \
                    '&client_id=' + config['baidu_ocr_client_id'] + \
                    '&client_secret=' + config['baidu_ocr_client_secret']
                response = sendRequest(method = 'get', url = host, 
                        data = None, headers = None, comment = 'aip.baidubce.com/oauth')
                if response:
                    #print(response.json())
                    pass

                parsed_json = json.loads(response.text)
                #print(parsed_json['access_token'])
                getOCR.at = parsed_json['access_token']
                access_token = parsed_json['access_token']

            request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
            
            f = open(filename, 'rb')
            img = base64.b64encode(f.read())

            #print(str(time.ctime()) + '|End: Read screenshot')

            params = {"image":img, "language_type":language_type}
            # access_token = parsed_json['access_token']
            request_url = request_url + "?access_token=" + access_token
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            response = sendRequest(method = 'post', url = request_url, data=params, headers=headers, comment='ocr/v1/general_basic')
            if response:
                #print (response.json())
                parsed_json = json.loads(response.text)
                fullStr = ''
                for mbr in parsed_json['words_result']:
                    fullStr += mbr['words'] if fullStr == '' else ' - ' + mbr['words']

        elif engine == 'easyocr':
            try:
                reader = getOCR.easyocr_reader
            except AttributeError:
                getOCR.easyocr_reader = easyocr.Reader(['ch_sim','en'])
                reader = getOCR.easyocr_reader
            
            result = reader.readtext(filename, detail = 0)
            fullStr = ' - '.join(result)
        #print(fullStr)
        return fullStr

    except Exception as x:
        strExcDtl = traceback.format_exc()
        logger.error('OCR failed!!!')
        logger.debug(strExcDtl)
        return ''

def sendMail(to, subject, body=None, attachment_path_list=None):
    msg = MIMEMultipart()

    msg['Subject'] = subject
    msg['From'] = config['GMAIL_NOTIFICATION_USR']
    msg['To'] = to

    msg.attach(MIMEText(body, "plain"))

    if attachment_path_list is not None:
        for attachment_path in attachment_path_list:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            filename = attachment_path.split(
                "\\" if platform.uname().system == 'Windows' else '/')[-1]
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
            )
            msg.attach(part)

    text = msg.as_string()

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(config['GMAIL_NOTIFICATION_USR'], config['GMAIL_NOTIFICATION_PWD'])
        server.sendmail(config['GMAIL_NOTIFICATION_USR'], to.split(','), text)
        server.close()

        logger.info('Email sent!')
    except Exception as x:
        logger.error(str(x))

def trigger_action(ser, *buttons, sec=0.1):
    if not buttons:
        raise ValueError('No Buttons were given.')

    txt = '!'
    for button in buttons:
        # push button
        if button == 'NOTHING':
            time.sleep(sec)
            return
        else:
            txt += str(btnCode[button.upper()]) + ','

    txt = txt[:len(txt)-1] + '@'
    duration = int(sec*40)
    txt += str(duration) + '#'
    ser.write(txt.encode())
    time.sleep(sec - 0.02)

def getConfig():
    config_main = configparser.ConfigParser()
    config_main.read(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'acnh_config.ini']))
    if config_main.has_section('REOPEN_ISLAND'):
        return config_main['REOPEN_ISLAND']
    else:
        logger.error('acnh_config.ini not found!!! Exiting...')
        sys.exit(0)

def cchandler(signal_received, frame):
    # Handle any cleanup here
    logger.info('SIGINT or CTRL-C detected. Giving back controller...')
    for key, value in proc.items():
        if value.is_alive():
            value.terminate()
    for action, duration in command_list_g4:
        trigger_action(ser, *action, sec=duration)
    exit(0)

def getSysTime():
    trigger_action(ser, 'HOME')
    time.sleep(2)
    img = bgd_capture.getIM().crop((934, 119, 1027, 153)).convert('L').point(fn, mode='1')
    filename = os.sep.join([config['CAP_DIR'],'test','sys_time_' + str(int(time.time())) + '.jpg'])
    img.save(filename)
    strText = getOCR(filename,'ENG').replace(' ', '')
    if strText is None or strText == '':
        logger.error('Unable to read system time of Switch OS. Exiting...')
        sys.exit(0)
    logger.info('Switch system time (from OCR): ' + strText)
    trigger_action(ser, 'HOME')
    time.sleep(2)
    return strText if strText is not None else ''

def isSimilarColor(color1, color2):
    THRESHOLD = 5
    # Red Color
    color1_rgb = sRGBColor(color1[0], color1[1], color1[2])

    # Blue Color
    color2_rgb = sRGBColor(color2[0], color2[1], color2[2])

    # Convert from RGB to Lab Color Space
    color1_lab = convert_color(color1_rgb, LabColor)

    # Convert from RGB to Lab Color Space
    color2_lab = convert_color(color2_rgb, LabColor)

    # Find the color difference
    delta_e = delta_e_cie2000(color1_lab, color2_lab)

    return True if delta_e < THRESHOLD else False

def hasInternet():
    url = "http://www.google.com"
    timeout = 5
    try:
        request = requests.get(url, timeout=timeout)
        logger.debug("Connected to the Internet")
        return True
    except (requests.ConnectionError, requests.Timeout) as exception:
        logger.debug("No internet connection.")
        return False

def sendRequest(url, method = 'get', data = None, headers = None, files = None, comment=None):
    t0 = time.time()
    try:
        resp = getattr(requests_retry_session(), method)(url, data = data, headers = headers, files = files, verify=False, timeout=(20, 20))
        #print(url)
    except Exception as x:
        logger.error(str(comment) + ' : ' + x.__class__.__name__)
    else:
        pass
        #print('[INFO] ' + time.ctime() + ': ' + str(comment) + ' : It eventually worked: HTTP', resp.status_code)
    finally:
        t1 = time.time()
        #print('[INFO] ' + time.ctime() + ': ' + str(comment) + ' : Took', t1 - t0, 'seconds')
        logger.debug(str(comment) + ' : Took ' + str(round(t1 - t0,2)) + ' seconds')

    if resp is not None and resp.status_code == 200:
        #parsed_json = json.loads(resp.text)
        #if parsed_json['rc'] != 0:
        #    stopRun('[ERROR] ' + time.ctime() + ': ' + str(comment) + ' rc = ' + str(parsed_json['rc']))
        #print('[OK] ' + time.ctime() + ': ' + str(comment))
        pass
    else:
        logger.error(str(comment) + ' : HTTP ' + str(resp.status_code))

    return resp

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    #status_forcelist=(500, 502, 504),
    session=None):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        #status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
#############################################################################
if __name__ ==  '__main__':

    signal(SIGINT, cchandler)

    config = getConfig()
    tessdata_dir_config = r'--tessdata-dir "' + config['TESSDATA_DIR'] + r'"'
    pytesseract.pytesseract.tesseract_cmd = config['TESSERACT_CMD']

    command_list_g1 = [] #steps of going back into the airport and talk to the attendant (Part I: till after internet connection)
    command_list_g4 = [] #steps of giving back the controller
    command_list_g5 = [] #steps of talking to the attendant (Part II: after internet connection)

    btnCode = {'L_UP':0, 'L_DOWN':1, 'L_LEFT':2, 'L_RIGHT':3, 'R_UP':4, 'R_DOWN':5,
                'R_LEFT':6, 'R_RIGHT':7, 'X':8, 'Y':9, 'A':10, 'B':11, 'L':12, 'R':13,
                'THROW':14, 'NOTHING':15, 'TRIGGERS':16, 'HOME':17, 'MINUS':18}

    # create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch1 = logging.StreamHandler()
    ch1.setLevel(logging.DEBUG)
    ch2 = logging.FileHandler(filename=os.sep.join([config['CAP_DIR'],'visitors','cap_visitor_log.txt']), mode='a', encoding='utf-8')
    ch2.setLevel(logging.INFO)
    ch3 = CustomLogHandler()
    ch3.setLevel(logging.CRITICAL)
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch1.setFormatter(formatter)
    ch2.setFormatter(formatter)
    ch3.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch1)
    logger.addHandler(ch2)
    logger.addHandler(ch3)

    img_disconnect = cv2.imread(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'ref_img','disconnect_original.jpg']))
    img_disconnect = cv2.cvtColor(img_disconnect, cv2.COLOR_BGR2GRAY)

    bgd_capture = cl_bgd_cap()
    proc = {}

    if config['quanquan_enabled'] == 'yes' and config['DODOApp_enabled'] == 'yes':
        logger.critical('xcx quanquan and DODOApp cannot be enabled together!!!')
        sys.exit(0)
    if config['quanquan_enabled'] == 'yes':
        xcx_adapter = cl_quanquan_cap()
        xcx_adapter.sendMsg(u'[喵] 服务重启成功')
    elif config['DODOApp_enabled'] == 'yes':
        if config['DODOApp_use_API'] == 'yes':
            xcx_adapter = DODOApp_API(config=config)
            proc['dodoapp_queue_logger'] = multiprocessing.Process(target=dodoapp_island_queue_logger, args=(config,xcx_adapter,), daemon=True)
            proc['dodoapp_queue_logger'].start()
        else:
            xcx_adapter = cl_DODOApp_cap()

    g_lastRestart = int(time.monotonic())

    thresh = 170
    fn = lambda x: 255 if x > thresh else 0

    #Preload g4 so that the exit handler can hand over the controller back
    with open(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'reopen_island_command_v1.txt']), 'r') as command_file:
        for command_line in command_file:
            group, action, strDuration = command_line.replace('\n', '').split(',')
            actionlist = action.split('&&')
            command_struc = (actionlist, float(strDuration))
            if group == '4':
                command_list_g4.append(command_struc) #release the controller

    ser = serial.Serial(config['COM_PORT'], 9600, timeout=0,bytesize=8, stopbits=1)
    logger.info('<COM port opened.>')
    if config['interactive_mode'] == 'no':
        ser.write(b'^') 
        time.sleep(20)

        g_sysTime = datetime.datetime.strptime(getSysTime(), '%H:%M')
        g_sysTimeMono = int(time.monotonic())
        g_islandUpdateInterval = 3600

        # display the actual (US Eastern) time of store closure at program start
        timeDelta = g_sysTime.replace(hour=23, minute=00) - g_sysTime
        logger.info('Store will be closing at (US Eastern): ' + \
            (datetime.datetime.now() + timeDelta).strftime(r'%Y-%m-%d %H:%M'))
        if config['DODOApp_enabled'] == 'yes' and config['DODOApp_use_API'] == 'yes':
            expTime = str(calendar.timegm((datetime.datetime.now(datetime.timezone.utc) + timeDelta).timetuple())) + '513'
            xcx_adapter.updateIsland(expireTime=expTime)

    while True:
        #img = bgd_capture.getIM().crop((1060,100,1100,101))
        #pixelcolor1 = img.getpixel((0,0))
        #pixelcolor2 = img.getpixel((35,0))
        #if not (pixelcolor1 == (162, 152, 114) and pixelcolor2 == (155, 143, 104)):
        #print(str(time.ctime()),'Detecting network error message...')
        if config['interactive_mode'] == 'no' and \
            (config['quanquan_enabled'] == 'yes' or config['DODOApp_enabled'] == 'yes'):
            #calculate the current switch system time by applying offset to the 
            #original system time captured on start up. This is to avoid expensive capture and OCR
            timeDelta = g_sysTime.replace(hour=23, minute=00) - \
                (g_sysTime + datetime.timedelta(seconds=(int(time.monotonic()) - g_sysTimeMono)))
            if 300 < timeDelta.total_seconds() <= 1200:
                g_islandUpdateInterval = 300
            elif timeDelta.total_seconds() <= 300:
                g_islandUpdateInterval = 60
            if (int(time.monotonic()) - g_lastRestart) > g_islandUpdateInterval:
                #skip island refresh if the shop is closing in 1 hr
                if timeDelta.total_seconds() >= 3600:
                    if isinstance(xcx_adapter,cl_quanquan_cap):
                        xcx_adapter.updateIsland() 
                if timeDelta.total_seconds() > 60:
                    hour, second = divmod(timeDelta.total_seconds(), 3600)
                    minute, second = divmod(second, 60)
                    strTime = (f'{int(hour)}小时' if hour != 0 else '') + \
                        (f'{int(minute)}分钟' if minute != 0 else '')
                    xcx_adapter.sendMsg(f'[喵] 本岛商店将于{strTime}后结束营业。')
                    g_lastRestart = int(time.monotonic())
                else:
                    for action, duration in command_list_g4:
                        trigger_action(ser, *action, sec=duration)
                    xcx_adapter.closeIsland()
        bgd_capture.showWindow()
        time.sleep(0.2)
        img_full = bgd_capture.getIM()
        img = img_full.crop((1036, 550, 1195, 708))
        # filename_tmp = os.sep.join([config['CAP_DIR'],'test','cap_flip_' + str(int(time.time())) + '.jpg'])
        # img.save(filename_tmp)
        pixelcolor1 = img.getpixel((35, 63))
        pixelcolor2 = img.getpixel((84, 110))
        color_ref1 = (51, 50, 51)
        color_ref2 = (34, 141, 197)
        if isSimilarColor(pixelcolor1,color_ref1) and isSimilarColor(pixelcolor2,color_ref2):
            # This is not really related to incoming flights,
            # but rather just find an infrequently triggered spot 
            # to bring the logger back up if terminated for some reason.
            if 'dodoapp_queue_logger' in proc.keys():
                if not proc['dodoapp_queue_logger'].is_alive():
                    proc['dodoapp_queue_logger'] = multiprocessing.Process(
                        target=dodoapp_island_queue_logger, 
                        args=(config,xcx_adapter,), 
                        daemon=True)
                    proc['dodoapp_queue_logger'].start()
                    logger.debug('DODOApp logger restarted')
            
            time.sleep(5) #wait for the flipping anime
            img = bgd_capture.getIM().crop((360, 271, 1191, 367)).convert('L').point(fn, mode='1')
            filename = os.sep.join([config['CAP_DIR'],'visitors','cap_visitor_' + str(int(time.time())) + '.jpg'])
            img.save(filename)
            strPlayerName = getOCR(filename)
            strPlayerName = strPlayerName if strPlayerName is not None else ''
            logger.info('New Visitor: ' + strPlayerName)
            if config['quanquan_announce_traffic'] == 'yes':
                l_t1 = time.monotonic()
                xcx_adapter.sendMsg(u'[喵] 侦测到进港航班：' + strPlayerName + u' （飞行中会“正忙”，请稍候...)')

            # This is to resolve the occasional color flickering from the capture card.
            # Basically we try a few more times before concluding the arrival of the flight
            diffColorCount = 0
            while True:
                img = bgd_capture.getIM().crop((1036, 550, 1195, 708))
                pixelcolor1 = img.getpixel((35, 63))
                pixelcolor2 = img.getpixel((84, 110))
                color_ref1 = (51, 50, 51)
                color_ref2 = (34, 141, 197)
                if isSimilarColor(pixelcolor1,color_ref1) and isSimilarColor(pixelcolor2,color_ref2):
                    diffColorCount = 0
                    time.sleep(2)
                    continue
                else:
                    diffColorCount += 1
                    time.sleep(0.5)
                    if diffColorCount <= 3:
                        continue
                
                # filename_tmp = os.sep.join([config['CAP_DIR'],'test','cap_flip_' + str(int(time.time())) + '.jpg'])
                # img.save(filename_tmp)

                if config['quanquan_announce_traffic'] == 'yes':
                    xcx_adapter.sendMsg(u'[喵] ' + strPlayerName + u' 已落地，用时'
                        + str(int(time.monotonic() - l_t1) + 5) + u'秒。下一位旅客请尝试登机')
                # this is to avoid the next main iteration captures prematurely the fading animation
                # of the airport flip board after the flight arrival
                time.sleep(2)
                break
        #"Network Error" within ACNH
        cv2_img = cv2.cvtColor(numpy.array(img), cv2.COLOR_BGR2GRAY)
        #this is for the other type of "connection error" as an OS msgbox
        cv2_img2 = cv2.cvtColor(
            numpy.array(img_full.crop((555 - 15, 360 - 15, 555 + 156 + 15, 360 + 34 + 15))), cv2.COLOR_BGR2GRAY)
        img_ref = cv2.cvtColor(
            cv2.imread(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'ref_img','txtDisconn.jpg'])), cv2.COLOR_BGR2GRAY)
        res = cv2.matchTemplate(cv2_img2, img_ref, cv2.TM_CCOEFF_NORMED)
        threshold = 0.95
        loc = numpy.where(res >= threshold)
        isDisconnected = False
        for pt in zip(*loc[::-1]):
            isDisconnected = True
            break
        if ssim(img_disconnect, cv2_img) < 0.8 and not isDisconnected:
            #time.sleep(5)
            #img = bgd_capture.getIM().crop((544,523,757,669)).convert('L').point(fn, mode='1')
            img = bgd_capture.getIM().crop((500, 523, 790, 669))
            cv2_img = cv2.cvtColor(numpy.array(img), cv2.COLOR_BGR2GRAY)
            img_ref = cv2.cvtColor(
                cv2.imread(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'ref_img','txtBack.jpg'])), cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(cv2_img, img_ref, cv2.TM_CCOEFF_NORMED)
            threshold = 0.95
            loc = numpy.where(res >= threshold)
            for pt in zip(*loc[::-1]):
                #just one box is enough...so just return...
                #cv2.imwrite(os.sep.join([config['CAP_DIR'],'test','cap_back_' + str(int(time.time())) + '.jpg']),cv2_img)
                filename = os.sep.join([config['CAP_DIR'],'test','cap_back_' + str(int(time.time())) + '.jpg'])
                img.crop((0, 0, 290, 40)).convert('L').point(lambda x: 255 if x > 110 else 0, mode='1').save(filename)
                strPlayerName = getOCR(filename)
                strPlayerName = strPlayerName if strPlayerName is not None else ''
                logger.info('Departing: ' + strPlayerName)
                if config['quanquan_announce_traffic'] == 'yes':
                    if strPlayerName.replace(' ','') == '':
                        xcx_adapter.sendMsg(u'[喵] 有人离岛啦~跑太快没看清>__<...唔...')
                    else:
                        xcx_adapter.sendMsg(u'[喵] ' + strPlayerName + u' 离岛啦~ （离境过程中会短暂“正忙”)')
                time.sleep(5)#to avoid capturing the same message
                break
            continue
        
        logger.error('Connection terminated from ACNH server!!!')
        while(True):
            logger.debug('Checking internet connection...')
            if hasInternet():
                break
            else:
                logger.debug('No internet connection. Try again in 30 seconds.')
                time.sleep(30)

        if (config['quanquan_enabled'] == 'yes' or config['DODOApp_enabled'] == 'yes'):
            xcx_adapter.sendMsg(u'[喵] 炸啦~炸啦~岛炸啦~~密码失效啦~~飞奔向机场重开ing...')
        
        if config['interactive_mode'] == 'yes':
            logger.warning('Go back to OS HOME menu to continue...')
            time.sleep(2)
            pixelcolor1_old = (255, 255, 255)
            pixelcolor2_old = (255, 255, 255)
            while True:
                img = bgd_capture.getIM().crop((1036, 550, 1195, 708))
                pixelcolor1 = img.getpixel((35, 63))
                pixelcolor2 = img.getpixel((84, 110))
                if (pixelcolor1 == pixelcolor1_old and pixelcolor2 == pixelcolor2_old) \
                    or pixelcolor1_old == (255, 255, 255):
                    pixelcolor1_old = pixelcolor1
                    pixelcolor2_old = pixelcolor2
                    continue
                time.sleep(3)
                ser.write(b'^') 
                time.sleep(20)
                break

        #soc.sendall(b'HOME')
        for _ in range(14):
            trigger_action(ser, 'A')
            time.sleep(0.25)
        time.sleep(5)
        #we need this dynamic determination because the loading screen after a disconnect
        #varies. We continue only after confirming the character is at the door outside of the
        #airport.
        logger.info('Waiting for evacuation from the airport...')
        
        # See if the screen lights up again
        while True:
            img = bgd_capture.getIM().crop((625, 305, 630, 310)) \
                .convert('L').point(lambda x: 255 if x > 30 else 0, mode='1')
            pixelcolor1 = img.getpixel((1, 1))
            pixelcolor2 = img.getpixel((2, 2))
            if pixelcolor1 == 0 and pixelcolor2 == 0:
                time.sleep(0.1)
                continue
            break
        
        # Okay the screen lit up. But are we really outside of the airport?
        # In case of persistent network issue, there will be additonal pop up at OS level.
        # Therefore we seek for the frame of the mini map here to make sure 
        # that we are still within the game
        time.sleep(5)
        # This is to resolve the occasional color flickering from the capture card.
        # Basically we try a few more times before concluding the arrival of the flight
        diffColorCount = 0
        while True:
            img = bgd_capture.getIM().crop((990,550,993,700))
            pixelcolor1 = img.getpixel((0,0))
            pixelcolor2 = img.getpixel((0,50))
            pixelcolor3 = img.getpixel((0,100))
            pixelcolor4 = img.getpixel((0,149))
            color_ref = (254, 251, 230)
            if not isSimilarColor(pixelcolor1,color_ref) \
                == isSimilarColor(pixelcolor2,color_ref) \
                == isSimilarColor(pixelcolor3,color_ref) \
                == isSimilarColor(pixelcolor4,color_ref) \
                == True:
                diffColorCount += 1
                time.sleep(1)
                if diffColorCount <= 5:
                    logger.debug('Mini-map not found at the airport. Flickering?')
                    continue
                else:
                    logger.critical('Character is lost in the airport. Exiting to prevent further damage...')
                    sys.exit(0)
            break

        # Reload the command list file so that any changes can be adopted without a restart
        command_list_g1.clear()
        command_list_g4.clear()
        command_list_g5.clear()
        with open(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'reopen_island_command_v1.txt']), 'r') as command_file:
            for command_line in command_file:
                group, action, strDuration = command_line.replace('\n', '').split(',')
                actionlist = action.split('&&')
                command_struc = (actionlist, float(strDuration))
                if group == '1':
                    command_list_g1.append(command_struc)
                elif group == '4':
                    command_list_g4.append(command_struc) #release the controller
                elif group == '5':
                    command_list_g5.append(command_struc)
        # Check the connection again here before getting back into the airport
        while(True):
            logger.debug('Checking internet connection again...')
            if hasInternet():
                break
            else:
                logger.debug('No internet connection. Try again in 30 seconds.')
                time.sleep(30)
        
        logger.debug('Starting g1.')
        for action, duration in command_list_g1:
            trigger_action(ser, *action, sec=duration)
        
        # Attendant will be preparing ACNH server connection after g1...
        # We need to separate g5 from g1, as sometimes the connection to ACNH server
        # takes extra time which leads to failure due to action sequence getting out of sync.
        logger.debug('Waiting for ACNH server connection...')
        bConnectionReady = False
        iRetryCounter = 0
        while bConnectionReady == False:
            img = bgd_capture.getIM().crop((286, 519, 625, 570))
            cv2_img = cv2.cvtColor(numpy.array(img), cv2.COLOR_BGR2GRAY)
            img_ref = cv2.cvtColor(
                cv2.imread(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'ref_img','txtAirportHowToInvite.jpg'])), cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(cv2_img, img_ref, cv2.TM_CCOEFF_NORMED)
            threshold = 0.95
            loc = numpy.where(res >= threshold)
            for pt in zip(*loc[::-1]):
                logger.debug('ACNH server connection established.')
                bConnectionReady = True
                break
            iRetryCounter += 1
            if iRetryCounter >= 300:
                logger.critical('ACNH server connection seems broken... Exiting...')
                for action, duration in command_list_g4:
                    trigger_action(ser, *action, sec=duration)
                if (config['quanquan_enabled'] == 'yes' or config['DODOApp_enabled'] == 'yes'):
                    xcx_adapter.closeIsland()
                sys.exit(0)
            time.sleep(1)
        logger.debug('Starting g5.')
        for action, duration in command_list_g5:
            trigger_action(ser, *action, sec=duration)        
        
        img = bgd_capture.getIM().crop((300, 520, 520, 620)).convert('L').point(fn, mode='1')
        logger.info('DODO code captured.')
        img = img.crop((0, 50, 220, 100))
        text = pytesseract.image_to_string(img, lang='acnh_dodo2',config=tessdata_dir_config)
        logger.debug('Original OCR:' + str(text))
        body = text + '\r\n'
        #text = re.compile(r'(“+|”+|"+|\s+)').sub('', text)
        text = re.compile(r'([^a-zA-Z0-9])').sub('', text)
        #text = text.replace(' ', '').replace('“', '').replace('”', '').replace('"', '')
        
        filename = os.sep.join([config['CAP_DIR'],'cap_new_island_pwd_'+ str(int(time.time())) + '.jpg'])
        img.save(filename) 
        
        if len(text) != 5:
            logger.warning('Local OCR failed. Falling back to Baidu OCR.')
            text = re.compile(r'([^a-zA-Z0-9])').sub('', getOCR(filename,'ENG').replace('O','0'))
            logger.debug('Calibrated Baidu OCR output:' + text)
            body = body + 'Local OCR failed. Falling back to Baidu OCR.'

        body = str(time.ctime()) + '\r\n' + body + text

        attachment_path_list = []
        attachment_path_list.append(filename)
        sendMail(config['new_code_maillist'], 'New DODO Code for Your Island', body, attachment_path_list)

        if len(text) != 5:
            #we will be here only if both tesseract and Baidu gave wrong OCR result
            logger.critical('Incorrect length detected with DODOCode!!!')
            for action, duration in command_list_g4:
                trigger_action(ser, *action, sec=duration)
            if (config['quanquan_enabled'] == 'yes' or config['DODOApp_enabled'] == 'yes'):
                xcx_adapter.closeIsland()
            sys.exit(0)
        else:
            if (config['quanquan_enabled'] == 'yes' or config['DODOApp_enabled'] == 'yes'):
                xcx_adapter.updateIsland(newDODO=text)
                xcx_adapter.sendMsg(u'[喵] 呼...机场已恢复开放~请刷新页面获取最新密码~（趴...')

        for _ in range(14):
            trigger_action(ser, 'B')
            time.sleep(0.25)
        logger.info('Gate Reopened.')
        #now leave the airport and head to the chair
        trigger_action(ser, 'L_LEFT', sec=0.9)
        trigger_action(ser, 'L_DOWN', sec=2.5)
        time.sleep(10)
        trigger_action(ser, 'L_LEFT', sec=0.32)
        trigger_action(ser, 'L_UP', sec=7)
        trigger_action(ser, 'L_RIGHT', sec=0.52)
        trigger_action(ser, 'L_UP', sec=5)

        if config['interactive_mode'] == 'yes':
            logger.info('Interactive mode enabled. Giving back controller...')
            for action, duration in command_list_g4:
                trigger_action(ser, *action, sec=duration)

        time.sleep(30)
        bgd_capture.showWindow()
