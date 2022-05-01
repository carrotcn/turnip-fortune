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

import re
import cv2
import numpy
from skimage.metrics import structural_similarity as ssim

from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

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
        logger.info('acnh_config.ini not found!!! Exiting...')
        sys.exit(0)

def cchandler(signal_received, frame):
    # Handle any cleanup here
    logger.info('SIGINT or CTRL-C detected. Giving back controller...')
    for action, duration in command_list_g4:
        trigger_action(ser, *action, sec=duration)
    exit(0)

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
        logger.info(str(comment) + ' : Took ' + str(round(t1 - t0,2)) + ' seconds')

    if resp.status_code == 200:
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
signal(SIGINT, cchandler)

config = getConfig()
tessdata_dir_config = r'--tessdata-dir "' + config['TESSDATA_DIR'] + r'"'
pytesseract.pytesseract.tesseract_cmd = config['TESSERACT_CMD']

command_list_g1 = []
command_list_g4 = []
btnCode = {'L_UP':0, 'L_DOWN':1, 'L_LEFT':2, 'L_RIGHT':3, 'R_UP':4, 'R_DOWN':5,
            'R_LEFT':6, 'R_RIGHT':7, 'X':8, 'Y':9, 'A':10, 'B':11, 'L':12, 'R':13,
            'THROW':14, 'NOTHING':15, 'TRIGGERS':16, 'HOME':17, 'MINUS':18}

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch1 = logging.StreamHandler()
ch1.setLevel(logging.DEBUG)
# ch2 = logging.FileHandler(filename=os.sep.join([config['CAP_DIR'],'visitors','cap_visitor_log.txt']), mode='a', encoding='utf-8')
# ch2.setLevel(logging.INFO)
# ch3 = CustomLogHandler()
# ch3.setLevel(logging.CRITICAL)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch1.setFormatter(formatter)
# ch2.setFormatter(formatter)
# ch3.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch1)
# logger.addHandler(ch2)
# logger.addHandler(ch3)

bgd_capture = cl_bgd_cap()

thresh = 170
fn = lambda x: 255 if x > thresh else 0

with open(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'reopen_island_command_v1.txt']), 'r') as command_file:
    for command_line in command_file:
        group, action, strDuration = command_line.replace('\n', '').split(',')
        actionlist = action.split('&&')
        command_struc = (actionlist, float(strDuration))
        if group == '4':
            command_list_g4.append(command_struc) #release the controller

ser = serial.Serial(config['COM_PORT'], 9600, timeout=0,bytesize=8, stopbits=1)
logger.info('<COM port opened.>')
ser.write(b'^') 
time.sleep(20)

img = bgd_capture.getIM().crop((300, 520, 520, 620)).convert('L').point(fn, mode='1')
logger.info('DODO code captured.')
img = img.crop((0, 50, 220, 100))
text = pytesseract.image_to_string(img, lang='dodo',config=tessdata_dir_config)
logger.debug('Original OCR:' + str(text))
body = text + '\r\n'
#text = re.compile(r'(“+|”+|"+|\s+)').sub('', text)
text = re.compile(r'([^a-zA-Z0-9])').sub('', text)
#text = text.replace(' ', '').replace('“', '').replace('”', '').replace('"', '')

filename = os.sep.join([config['CAP_DIR'],'cap_new_island_pwd_'+ str(int(time.time())) + '.jpg'])
img.save(filename) 

if len(text) != 5:
    logger.error('Local OCR failed. Falling back to Baidu OCR.')
    sys.exit(0)

for _ in range(14):
    trigger_action(ser, 'B')
    time.sleep(0.25)
logger.info('Gate opened.')

#now leave the airport and head to the chair
trigger_action(ser, 'L_LEFT', sec=0.9)
trigger_action(ser, 'L_DOWN', sec=2.5)
time.sleep(10)
trigger_action(ser, 'L_LEFT', sec=0.32)
trigger_action(ser, 'L_UP', sec=7)
trigger_action(ser, 'L_RIGHT', sec=0.52)
trigger_action(ser, 'L_UP', sec=5)

trigger_action(ser, 'HOME')
time.sleep(2)

config_temp = configparser.ConfigParser()
config_temp.read(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'dodoapp_local_config.ini']))
if not config_temp.has_section('DODOApp'):
    logger.error('dodoapp_local_config.ini not found!!! Exiting...')
    sys.exit(0)
strPrice = config_temp['DODOApp']['island_price']
strIsPrivate = config_temp['DODOApp']['isPrivate']

xcx_adapter = DODOApp_API(config=config)
expTime = str(calendar.timegm((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)).timetuple())) + '513'
strDesc = u'时旅高价，介意勿排。\n\n请给小花~\n\n每次排队只能上岛卖一次，留言多次无效！如需多次请每次重新排队。\n上岛角色名字必须与排队时填写的“游戏昵称”一致，以便岛主验证身份防止偷渡。\n如发现有违反会手动炸岛+拉黑。\n\n岛主挂机人不在，炸岛随缘重开。'
xcx_adapter.createIsland(expireTime=expTime,isPrivate=strIsPrivate,newDODO=text,price=strPrice,desc=strDesc)