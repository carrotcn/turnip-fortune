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
import multiprocessing

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from bgd_cap import cl_bgd_cap
from dodoapp_api import DODOApp_API

# def sendRequest(url, method = 'get', data = None, headers = None, files = None, comment=None):
#     t0 = time.time()
#     try:
#         resp = getattr(requests_retry_session(), method)(url, data = data, headers = headers, files = files, verify=False, timeout=(20, 20))
#         #print(url)
#     except Exception as x:
#         logger.error(str(comment) + ' : ' + x.__class__.__name__)
#     else:
#         pass
#         #print('[INFO] ' + time.ctime() + ': ' + str(comment) + ' : It eventually worked: HTTP', resp.status_code)
#     finally:
#         t1 = time.time()
#         #print('[INFO] ' + time.ctime() + ': ' + str(comment) + ' : Took', t1 - t0, 'seconds')
#         logger.info(str(comment) + ' : Took ' + str(round(t1 - t0,2)) + ' seconds')

#     if resp.status_code == 200:
#         #parsed_json = json.loads(resp.text)
#         #if parsed_json['rc'] != 0:
#         #    stopRun('[ERROR] ' + time.ctime() + ': ' + str(comment) + ' rc = ' + str(parsed_json['rc']))
#         #print('[OK] ' + time.ctime() + ': ' + str(comment))
#         pass
#     else:
#         logger.error(str(comment) + ' : HTTP ' + str(resp.status_code))

#     return resp

# def requests_retry_session(
#     retries=3,
#     backoff_factor=0.3,
#     #status_forcelist=(500, 502, 504),
#     session=None):
#     session = session or requests.Session()
#     retry = Retry(
#         total=retries,
#         read=retries,
#         connect=retries,
#         backoff_factor=backoff_factor,
#         #status_forcelist=status_forcelist,
#     )
#     adapter = HTTPAdapter(max_retries=retry)
#     session.mount('http://', adapter)
#     session.mount('https://', adapter)
#     return session

def dodoapp_island_queue_logger(config,xcx_adapter):
    qclogger = logging.getLogger('qclogger')
    qclogger.setLevel(logging.DEBUG)
    queue_changelog_f = logging.FileHandler(filename=os.sep.join([config['CAP_DIR'],'visitors','dodoapp_queue_changelog.txt']), mode='a', encoding='utf-8')
    queue_changelog_f.setLevel(logging.DEBUG)
    # queue_changelog_s = logging.StreamHandler(sys.stdout)
    # queue_changelog_s.setLevel(logging.DEBUG)
    qcformatter = logging.Formatter(fmt='%(asctime)s - %(message)s', datefmt='%m-%d %H:%M:%S')
    queue_changelog_f.setFormatter(qcformatter)
    qclogger.addHandler(queue_changelog_f)
    # qclogger.addHandler(queue_changelog_s)
    
    island_queue = {}
    
    while True:
        # current_queue = xcx_adapter.getIslandQueue('1204135')
        current_queue = xcx_adapter.getIslandQueue()
        sorted_queue = sorted(current_queue)
        with open(os.sep.join([config['CAP_DIR'],'visitors','dodoapp_current_queue.txt']), 'w',encoding='utf-8') as dodoapp_current_queue_file:
            dodoapp_current_queue_file.write('Current Queue (' + str(datetime.datetime.now().strftime(r'%H:%M:%S')) + ')\n')
            current_queue_list = []
            for index, user in enumerate(sorted_queue):
                current_queue_list.append(user.id)
                dodoapp_current_queue_file.write(f'{index + 1}: {user.nickName} - {user.gameNickName}\n')
                if user.id not in island_queue.keys():
                    qclogger.info('[+] ' + f'{user.nickName} - {user.gameNickName} - Rank: {user.rank}')
                island_queue[user.id] = user #ADD for new user, UPDATE for existing user (e.g., rank)
            # Here we create a copy of the original keys list. Otherwise the pop() will change the length of the list and cause exception
            for user in list(island_queue.keys()):
                if user not in current_queue_list:
                    qclogger.info('[-] ' + f'{island_queue[user].nickName} - {island_queue[user].gameNickName} - Rank: {island_queue[user].rank}')
                    island_queue.pop(user)
        time.sleep(20)

def getConfig():
    config_main = configparser.ConfigParser()
    config_main.read(os.sep.join([os.path.dirname(os.path.realpath(__file__)),'acnh_config.ini']))
    if config_main.has_section('REOPEN_ISLAND'):
        return config_main['REOPEN_ISLAND']
    else:
        logger = logging.getLogger('__main__')
        logger.error('acnh_config.ini not found!!! Exiting...')
        sys.exit(0)

if __name__ ==  '__main__':
    logger = logging.getLogger('__main__')
    logger.setLevel(logging.DEBUG)
    # create console handler and set level to debug
    ch1 = logging.StreamHandler()
    ch1.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    # add formatter to ch
    ch1.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch1)
    
    config = getConfig()
    xcx_adapter = DODOApp_API(config=config)
    dodoapp_island_queue_logger(config, xcx_adapter)
