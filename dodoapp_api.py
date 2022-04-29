import requests
import datetime,time,calendar
import json
import sys, traceback, logging
from dataclasses import dataclass
import urllib.parse
import configparser,os
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

proxies = {
   'http': 'http://127.0.0.1:8888',
   'https': 'http://127.0.0.1:8888',
}

def sendRequest(url, method = 'get', data = None, headers = None, files = None, comment=None):
    logger = logging.getLogger('__main__')
    t0 = time.time()
    try:
        resp = getattr(requests_retry_session(), method)(url, data = data, headers = headers, 
            files = files, verify=False, timeout=(20, 20))
        #print(url)
    except Exception as x:
        logger.error(str(comment) + ' : ' + x.__class__.__name__)
    else:
        pass
        
    if resp.status_code == 200:
        pass
    else:
        logger.error(f'[ERROR] HTTP {str(resp.status_code)}')
    
    return resp

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    #status_forcelist=(500, 502, 504),
    session=None,
):
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

def genStrParam(dictParam):
    
    strParam = ''

    for key, val in dictParam.items():
        if len(strParam) != 0:
            strParam += '&'
        strParam = strParam + key + '=' + str(val)
    
    #print(strParam)
    return strParam

@dataclass
class DODOApp_Island:
    id: int
    uid: int
    price: int
    createTime: int
    itype: int
    password: str
    lastUpdateTime: int
    expireTime: int
    nickName: str
    require: str

class DODOApp_API:
    def __init__(self,config) -> None:
        self.logger = logging.getLogger('__main__')
        self.island_list = []
        # We don't seem to need a full island list from DODOApp...
        # self.refresh_island_list()
        
        self.config_main = config

    def __get_headers(self):
        headers = { 'Content-type': 'application/x-www-form-urlencoded;charset=UTF-8', 
                    'Accept': '*/*', 
                    'Accept-Encoding': 'gzip, deflate, br',
                    'clientVersion':'3.9.0',
                    'Accept-Language':'en-US;q=1, zh-Hans-US;q=0.9, ja-JP;q=0.8',
                    'token':self.config_main['DODOApp_token'],
                    'deviceId':self.config_main['DODOApp_deviceId'],
                    'clientType':'1',
                    'User-Agent': 'AnimalCrossingCircle/3.9.0 (iPhone; iOS 15.4.1; Scale/3.00)'}

        return headers

    def __get_my_island_raw(self):
        
        headers = self.__get_headers()

        dictParam_body = {}
        dictParam_body['apikey'] = self.config_main['DODOApp_apikey']
        dictParam_body['appType'] = '3'
        dictParam_body['clientTime'] = datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S')
        dictParam_body['clientType'] = '1'
        dictParam_body['clientVersion'] = '3.9.0'
        dictParam_body['deviceId'] = self.config_main['DODOApp_deviceId']
        dictParam_body['marketChannel'] = 'official'
        dictParam_body['packageName'] = 'com.dodolive.app'
        dictParam_body['sig'] = '1lDuuidQRsekqsnKDIUHy3BrkFI%3D'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['token'] = self.config_main['DODOApp_token']
        dictParam_body['uid'] = self.config_main['DODOApp_uid']
        dictParam_body['version'] = '1.0'

        data = genStrParam(dictParam=dictParam_body)
        
        resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/animalCrossing/stock/myStockPriceStatus', 
            data = data.encode('utf-8'), headers = headers, comment = 'myStockPriceStatus')
        try:
            parsed_json = json.loads(resp.text)
            if parsed_json['status'] != 0:
                self.logger.error(resp.text)
                raise Exception
        except Exception as x:
            return None
        return parsed_json

    def refresh_island_list(self):

        local_island_list = []
        
        headers = self.__get_headers()

        dictParam_body = {}
        dictParam_body['apikey'] = self.config_main['DODOApp_apikey']
        dictParam_body['appType'] = '3'
        # dictParam_body['clientTime'] = r'2022-04-23%2022%3A16%3A14'
        dictParam_body['clientTime'] = datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S')
        dictParam_body['clientType'] = '1'
        dictParam_body['clientVersion'] = '3.9.0'
        dictParam_body['deviceId'] = self.config_main['DODOApp_deviceId']
        dictParam_body['islandId'] = '10000'
        dictParam_body['marketChannel'] = 'official'
        dictParam_body['orderType'] = '1' # 好菜价. For 全部 remove this parameter
        dictParam_body['packageName'] = 'com.dodolive.app'
        dictParam_body['sig'] = '5dOFY/sveKC/gsOYHozYIHoaMpE%3D'
        dictParam_body['size'] = '30'
        # dictParam_body['timestamp'] = '1650766574756'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['token'] = self.config_main['DODOApp_token']
        dictParam_body['type'] = '0'
        dictParam_body['uid'] = self.config_main['DODOApp_uid']
        dictParam_body['version'] = '1.0'

        while(True):
            data = genStrParam(dictParam=dictParam_body)
            
            resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/animalCrossing/stocksV3', 
                data = data.encode('utf-8'), headers = headers, comment = 'stocksV3')
            try:
                parsed_json = json.loads(resp.text)
                if parsed_json['status'] != 0:
                    self.logger.error(resp.text)
                    raise Exception
                for island_raw in parsed_json['data']['list']:
                    if island_raw['price'] == 0: continue
                    local_island_list.append(
                        DODOApp_Island( island_raw['id'],
                                        island_raw['uid'],
                                        island_raw['price'],
                                        island_raw['createTime'],
                                        island_raw['type'],
                                        island_raw['password'],
                                        island_raw['lastUpdateTime'],
                                        island_raw['expireTime'],
                                        island_raw['userInfo']['nickName'],
                                        island_raw['require']
                                        ))

                if parsed_json['data']['hasMore']:
                    self.logger.debug('refresh_island_list: hasMore')
                    # dictParam_body['context'] = r'%7B%22lastId%22%3A-98836080%7D'
                    dictParam_body['context'] = urllib.parse.quote(parsed_json['data']['context'])
                else:
                    break
            except Exception as x:
                self.logger.error('stockV3 failed.')
                strExcDtl = traceback.format_exc()
                self.logger.debug(strExcDtl)
                return

        self.island_list = local_island_list

    def createIsland(self,expireTime=None,isPrivate=None,newDODO=None,price=None,desc=None):
        headers = self.__get_headers()
        
        # parsed_json = self.__get_my_island_raw()
        # mysp = parsed_json['data']['myStockPrice']
        dictParam_body = {}
        dictParam_body['apikey'] = self.config_main['DODOApp_apikey']
        dictParam_body['appType'] = '3'
        # dictParam_body['clientTime'] = r'2022-04-23%2022%3A16%3A14'
        dictParam_body['autoComplete'] = '1'
        dictParam_body['autoCompleteTime'] = '15'
        dictParam_body['clientTime'] = datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S')
        dictParam_body['clientType'] = '1'
        dictParam_body['clientVersion'] = '3.9.0'
        dictParam_body['deviceId'] = self.config_main['DODOApp_deviceId']
        dictParam_body['expireTime'] = expireTime
        dictParam_body['isAutoCall'] = '1'
        dictParam_body['isGratis'] = '1'
        dictParam_body['isPrivate'] = isPrivate
        dictParam_body['islandId'] = '10000'
        dictParam_body['marketChannel'] = 'official'
        dictParam_body['maxRankLimit'] = '5'
        dictParam_body['packageName'] = 'com.dodolive.app' 
        dictParam_body['password'] = newDODO
        dictParam_body['price'] = price
        dictParam_body['require'] = urllib.parse.quote(desc)
        dictParam_body['sameTimeCount'] = '2'
        dictParam_body['sig'] = '5dOFY/sveKC/gsOYHozYIHoaMpE%3D'
        # dictParam_body['timestamp'] = '1650766574756'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['token'] = self.config_main['DODOApp_token']
        dictParam_body['type'] = '1'
        dictParam_body['uid'] = self.config_main['DODOApp_uid']
        dictParam_body['version'] = '1.0'

        data = genStrParam(dictParam=dictParam_body)
        # print(data)
        # print(datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S'))

        # sys.exit(0)

        resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/animalCrossing/stock/newStockPrice', 
            data = data.encode('utf-8'), headers = headers, comment = 'newStockPrice')
        try:
            parsed_json = json.loads(resp.text)
            if parsed_json['status'] != 0:
                self.logger.error(resp.text)
                raise Exception
        except Exception as x:
            self.logger.error('stock/update failed.')
            strExcDtl = traceback.format_exc()
            self.logger.debug(strExcDtl)

    def updateIsland(self,newDODO=None,desc=None,expireTime=None):
        headers = self.__get_headers()

        parsed_json = self.__get_my_island_raw()
        mysp = parsed_json['data']['myStockPrice']
        dictParam_body = {}
        dictParam_body['apikey'] = self.config_main['DODOApp_apikey']
        dictParam_body['appType'] = '3'
        # dictParam_body['clientTime'] = r'2022-04-23%2022%3A16%3A14'
        dictParam_body['autoComplete'] = mysp['autoComplete']
        dictParam_body['autoCompleteTime'] = mysp['autoCompleteTime']
        dictParam_body['clientTime'] = datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S')
        dictParam_body['clientType'] = '1'
        dictParam_body['clientVersion'] = '3.9.0'
        dictParam_body['deviceId'] = self.config_main['DODOApp_deviceId']
        dictParam_body['expireTime'] = mysp['expireTime'] if expireTime is None else expireTime
        dictParam_body['imageUrls'] = urllib.parse.quote(mysp['imageUrls'])
        dictParam_body['isAutoCall'] = mysp['isAutoCall'] 
        dictParam_body['isGratis'] = mysp['isGratis'] 
        dictParam_body['marketChannel'] = mysp['userInfo']['marketChannel']
        dictParam_body['packageName'] = 'com.dodolive.app' 
        dictParam_body['password'] = mysp['password'] if newDODO is None else newDODO
        dictParam_body['require'] = mysp['require'] if desc is None else desc 
        dictParam_body['sameTimeCount'] = mysp['sameTimeCount'] 
        dictParam_body['sig'] = '5dOFY/sveKC/gsOYHozYIHoaMpE%3D'
        dictParam_body['stockPriceId'] = mysp['id']
        # dictParam_body['timestamp'] = '1650766574756'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['token'] = self.config_main['DODOApp_token']
        dictParam_body['uid'] = mysp['uid']
        dictParam_body['version'] = '1.0'

        data = genStrParam(dictParam=dictParam_body)
        # print(data)
        # print(datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S'))

        # sys.exit(0)

        resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/animalCrossing/stock/update', 
            data = data.encode('utf-8'), headers = headers, comment = 'update')
        try:
            parsed_json = json.loads(resp.text)
            if parsed_json['status'] != 0:
                self.logger.error(resp.text)
                raise Exception
        except Exception as x:
            self.logger.error('stock/update failed.')
            strExcDtl = traceback.format_exc()
            self.logger.debug(strExcDtl)

    def set_my_island_status(self,status):
        headers = self.__get_headers()

        parsed_json = self.__get_my_island_raw()
        mysp = parsed_json['data']['myStockPrice']
        dictParam_body = {}
        dictParam_body['apikey'] = self.config_main['DODOApp_apikey']
        dictParam_body['appType'] = '3'
        # dictParam_body['clientTime'] = r'2022-04-23%2022%3A16%3A14'
        dictParam_body['clientTime'] = datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S')
        dictParam_body['clientType'] = '1'
        dictParam_body['clientVersion'] = '3.9.0'
        dictParam_body['deviceId'] = self.config_main['DODOApp_deviceId']
        dictParam_body['marketChannel'] = mysp['userInfo']['marketChannel']
        dictParam_body['packageName'] = 'com.dodolive.app' 
        dictParam_body['sig'] = '5dOFY/sveKC/gsOYHozYIHoaMpE%3D'
        dictParam_body['status'] = status # 2 = pause, 1 = resume
        dictParam_body['stockPriceId'] = mysp['id']
        # dictParam_body['timestamp'] = '1650766574756'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['token'] = self.config_main['DODOApp_token']
        dictParam_body['uid'] = mysp['uid']
        dictParam_body['version'] = '1.0'

        data = genStrParam(dictParam=dictParam_body)
        
        resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/animalCrossing/stock/setStockPriceStatus', 
            data = data.encode('utf-8'), headers = headers, comment = 'setStockPriceStatus')
        try:
            parsed_json = json.loads(resp.text)
            if parsed_json['status'] != 0:
                self.logger.error(resp.text)
                raise Exception
        except Exception as x:
            self.logger.error('setStockPriceStatus failed.')
            strExcDtl = traceback.format_exc()
            self.logger.debug(strExcDtl)

    def closeIsland(self):
        headers = self.__get_headers()

        parsed_json = self.__get_my_island_raw()
        mysp = parsed_json['data']['myStockPrice']
        dictParam_body = {}
        dictParam_body['apikey'] = self.config_main['DODOApp_apikey']
        dictParam_body['appType'] = '3'
        # dictParam_body['clientTime'] = r'2022-04-23%2022%3A16%3A14'
        dictParam_body['clientTime'] = datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S')
        dictParam_body['clientType'] = '1'
        dictParam_body['clientVersion'] = '3.9.0'
        dictParam_body['deviceId'] = self.config_main['DODOApp_deviceId']
        dictParam_body['marketChannel'] = mysp['userInfo']['marketChannel']
        dictParam_body['packageName'] = 'com.dodolive.app' 
        dictParam_body['sig'] = '5dOFY/sveKC/gsOYHozYIHoaMpE%3D'
        dictParam_body['stockPriceId'] = mysp['id']
        # dictParam_body['timestamp'] = '1650766574756'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['token'] = self.config_main['DODOApp_token']
        dictParam_body['uid'] = mysp['uid']
        dictParam_body['version'] = '1.0'

        data = genStrParam(dictParam=dictParam_body)
        
        resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/animalCrossing/stock/delete', 
            data = data.encode('utf-8'), headers = headers, comment = 'delete')
        try:
            parsed_json = json.loads(resp.text)
            if parsed_json['status'] != 0:
                self.logger.error(resp.text)
                raise Exception
        except Exception as x:
            self.logger.error('delete failed.')
            strExcDtl = traceback.format_exc()
            self.logger.debug(strExcDtl)
        
        self.logger.info('Island closed. Exiting...')
        sys.exit(0)

    def sendMsg(self,content):
        headers = self.__get_headers()
        headers['Content-type'] = 'application/x-www-form-urlencoded'

        parsed_json = self.__get_my_island_raw()
        mysp = parsed_json['data']['myStockPrice']
        dictParam_body = {}
        dictParam_body['apikey'] = self.config_main['DODOApp_apikey']
        dictParam_body['appType'] = '3'
        # dictParam_body['clientTime'] = r'2022-04-23%2022%3A16%3A14'
        dictParam_body['clientTime'] = datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S')
        dictParam_body['clientType'] = '1'
        dictParam_body['clientVersion'] = '3.9.0'
        dictParam_body['content'] = urllib.parse.quote(content)
        dictParam_body['deviceId'] = self.config_main['DODOApp_deviceId']
        dictParam_body['marketChannel'] = mysp['userInfo']['marketChannel']
        dictParam_body['packageName'] = 'com.dodolive.app' 
        dictParam_body['relatedId'] = mysp['id']
        dictParam_body['sig'] = '5dOFY/sveKC/gsOYHozYIHoaMpE%3D'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['token'] = self.config_main['DODOApp_token']
        dictParam_body['type'] = '1'
        dictParam_body['uid'] = mysp['uid']
        dictParam_body['version'] = '1.0'

        data = genStrParam(dictParam=dictParam_body)
        
        resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/animalCrossing/commentV2', 
            data = data.encode('utf-8'), headers = headers, comment = 'commentV2')
        try:
            parsed_json = json.loads(resp.text)
            if parsed_json['status'] != 0:
                self.logger.error(resp.text)
                raise Exception
        except Exception as x:
            self.logger.error('stock/update failed.')
            strExcDtl = traceback.format_exc()
            self.logger.debug(strExcDtl)