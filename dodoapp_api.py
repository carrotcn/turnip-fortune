import hashlib, hmac, urllib, base64
from base64 import encode
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
    l_retry = 0
    while(True):
        try:
            resp = getattr(requests_retry_session(), method)(url, data = data, headers = headers, 
                files = files, verify=False, timeout=(20, 20))
            #print(url)
            break
        except Exception as x:
            logger.error(str(comment) + ' : ' + x.__class__.__name__)
            l_retry += 1
            time.sleep(15)
            if l_retry == 5:
                break
        else:
            pass
    
    if not 'resp' in locals():
        resp = None

    if resp is not None:
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

@dataclass
class DODOApp_IslandQueueUser:
    def __lt__(self, other):
         return self.rank < other.rank
    id: int
    uid: int
    gameNickName: str
    createTime: int
    lastUpdateTime: int
    nickName: str
    times: int
    rank: int    

class DODOApp_API:
    def __init__(self,config) -> None:
        self.logger = logging.getLogger('__main__')
        self.island_list = []
        # We don't seem to need a full island list from DODOApp...
        # self.refresh_island_list()
        
        self.config_main = config

    def __genStrParam(self,dictParam):
        
        def make_digest(message, key):    
            key = bytes(key, 'UTF-8')
            message = bytes(message, 'UTF-8')
            
            digester = hmac.new(key, message, hashlib.sha1)
            signature1 = digester.digest()
            # signature2 = base64.urlsafe_b64encode(signature1)
            signature2 = base64.standard_b64encode(signature1)
            return str(signature2, 'UTF-8')
        
        strParam = ''
        strMessage = ''
        # for key, val in dictParam.items():
        #     if len(strParam) != 0:
        #         strParam += '&'
        #     strParam = strParam + key + '=' + str(val)
        
        for key in sorted(dictParam.keys()):
            if len(strParam) != 0:
                strParam += '&'
            strParam = strParam + key + '=' + str(dictParam[key])

        strMessage = urllib.parse.unquote(strParam)
        result = make_digest(strMessage, self.config_main['DODOApp_secret_key'])
        strParam = strParam + '&sig=' + urllib.parse.quote(result)

        #print(strParam)
        return strParam

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

    def refreshToken(self):
        headers = self.__get_headers()

        dictParam_body = {}
        dictParam_body['apikey'] = self.config_main['DODOApp_apikey']
        dictParam_body['appType'] = '3'
        dictParam_body['clientTime'] = datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S')
        dictParam_body['clientType'] = '4' # '1' = iOS, '4' = Wechat Miniapp
        dictParam_body['clientVersion'] = '3.9.2'
        dictParam_body['codeType'] = '9'
        dictParam_body['countryCode'] = '1'
        dictParam_body['deviceId'] = self.config_main['DODOApp_deviceId']
        dictParam_body['marketChannel'] = 'official'
        dictParam_body['mobile'] = self.config_main['DODOApp_mobile']
        dictParam_body['packageName'] = 'com.dodolive.app'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['uid'] = '0' # config_main['DODOApp_uid']
        dictParam_body['version'] = '1.0'

        data = self.__genStrParam(dictParam=dictParam_body)

        resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/smsV2/send', 
            data = data.encode('utf-8'), headers = headers, comment = 'smsV2/send')
        try:
            parsed_json = resp.json()
            if parsed_json['status'] != 0:
                self.logger.error(resp.text)
                raise Exception
        except Exception as x:
            self.logger.critical('smsV2/send failed.')
            strExcDtl = traceback.format_exc()
            self.logger.debug(strExcDtl)
            sys.exit(0)

        code = input('Enter SMS code: ')

        dictParam_body = {}
        dictParam_body['apikey'] = self.config_main['DODOApp_apikey']
        dictParam_body['appType'] = '3'
        dictParam_body['clientTime'] = datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S')
        dictParam_body['clientType'] = '4'  # '1' = iOS, '4' = Wechat Miniapp
        dictParam_body['clientVersion'] = '3.9.2'
        dictParam_body['code'] = code
        dictParam_body['countryCode'] = '1'
        dictParam_body['deviceId'] = self.config_main['DODOApp_deviceId']
        dictParam_body['marketChannel'] = 'official'
        dictParam_body['mobile'] = self.config_main['DODOApp_mobile']
        dictParam_body['packageName'] = 'com.dodolive.app'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['uid'] = '0' # config_main['DODOApp_uid']
        dictParam_body['version'] = '1.0'

        data = self.__genStrParam(dictParam=dictParam_body)

        resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/login/v2/oversea', 
            data = data.encode('utf-8'), headers = headers, comment = 'login/v2/oversea')

        try:
            parsed_json = resp.json()
            if parsed_json['status'] != 0:
                self.logger.error(resp.text)
                raise Exception
        except Exception as x:
            self.logger.critical('login/v2/oversea failed.')
            strExcDtl = traceback.format_exc()
            self.logger.debug(strExcDtl)
            sys.exit(0)
        
        self.logger.debug('New token: ' + parsed_json['data']['tokenInfo']['token'])
        self.config_main['DODOApp_token'] = parsed_json['data']['tokenInfo']['token']

    def __get_my_island_raw(self):
        
        headers = self.__get_headers()

        dictParam_body = {}
        dictParam_body['apikey'] = self.config_main['DODOApp_apikey']
        dictParam_body['appType'] = '3'
        dictParam_body['clientTime'] = datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S')
        dictParam_body['clientType'] = '4' # '1' = iOS, '4' = Wechat Miniapp
        dictParam_body['clientVersion'] = '3.9.0'
        dictParam_body['deviceId'] = self.config_main['DODOApp_deviceId']
        dictParam_body['marketChannel'] = 'official'
        dictParam_body['packageName'] = 'com.dodolive.app'
        # dictParam_body['sig'] = '1lDuuidQRsekqsnKDIUHy3BrkFI%3D'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['token'] = self.config_main['DODOApp_token']
        dictParam_body['uid'] = self.config_main['DODOApp_uid']
        dictParam_body['version'] = '1.0'

        data = self.__genStrParam(dictParam=dictParam_body)
        
        resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/animalCrossing/stock/myStockPriceStatus', 
            data = data.encode('utf-8'), headers = headers, comment = 'myStockPriceStatus')
        try:
            parsed_json = resp.json()
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
        dictParam_body['clientType'] = '4' # '1' = iOS, '4' = Wechat Miniapp
        dictParam_body['clientVersion'] = '3.9.0'
        dictParam_body['deviceId'] = self.config_main['DODOApp_deviceId']
        dictParam_body['islandId'] = '10000'
        dictParam_body['marketChannel'] = 'official'
        dictParam_body['orderType'] = '1' # 好菜价. For 全部 remove this parameter
        dictParam_body['packageName'] = 'com.dodolive.app'
        # dictParam_body['sig'] = '5dOFY/sveKC/gsOYHozYIHoaMpE%3D'
        dictParam_body['size'] = '30'
        # dictParam_body['timestamp'] = '1650766574756'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['token'] = self.config_main['DODOApp_token']
        dictParam_body['type'] = '0'
        dictParam_body['uid'] = self.config_main['DODOApp_uid']
        dictParam_body['version'] = '1.0'

        while(True):
            data = self.__genStrParam(dictParam=dictParam_body)
            
            resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/animalCrossing/stocksV3', 
                data = data.encode('utf-8'), headers = headers, comment = 'stocksV3')
            try:
                # since v2.26.0 update, requests library supports Brotli compression if either 
                # the brotli or brotlicffi package is installed. So, if the response encoding 
                # is br, request library will automatically handle it and decompress it.
                parsed_json = resp.json()
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
                self.logger.critical('stockV3 failed.')
                strExcDtl = traceback.format_exc()
                self.logger.debug(strExcDtl)
                sys.exit(0)

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
        dictParam_body['clientType'] = '4' # '1' = iOS, '4' = Wechat Miniapp
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
        # dictParam_body['sig'] = '5dOFY/sveKC/gsOYHozYIHoaMpE%3D'
        # dictParam_body['timestamp'] = '1650766574756'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['token'] = self.config_main['DODOApp_token']
        dictParam_body['type'] = '1'
        dictParam_body['uid'] = self.config_main['DODOApp_uid']
        dictParam_body['version'] = '1.0'

        data = self.__genStrParam(dictParam=dictParam_body)
        # print(data)
        # print(datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S'))

        # sys.exit(0)

        resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/animalCrossing/stock/newStockPrice', 
            data = data.encode('utf-8'), headers = headers, comment = 'newStockPrice')
        try:
            parsed_json = resp.json()
            if parsed_json['status'] != 0:
                self.logger.error(resp.text)
                raise Exception
        except Exception as x:
            self.logger.critical('stock/newStockPrice failed.')
            strExcDtl = traceback.format_exc()
            self.logger.debug(strExcDtl)
            sys.exit(0)

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
        dictParam_body['clientType'] = '4' # '1' = iOS, '4' = Wechat Miniapp
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
        # dictParam_body['sig'] = '5dOFY/sveKC/gsOYHozYIHoaMpE%3D'
        dictParam_body['stockPriceId'] = mysp['id']
        # dictParam_body['timestamp'] = '1650766574756'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['token'] = self.config_main['DODOApp_token']
        dictParam_body['uid'] = mysp['uid']
        dictParam_body['version'] = '1.0'

        data = self.__genStrParam(dictParam=dictParam_body)
        # print(data)
        # print(datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S'))

        # sys.exit(0)

        resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/animalCrossing/stock/update', 
            data = data.encode('utf-8'), headers = headers, comment = 'update')
        try:
            parsed_json = resp.json()
            if parsed_json['status'] != 0:
                self.logger.error(resp.text)
                raise Exception
        except Exception as x:
            self.logger.critical('stock/update failed.')
            strExcDtl = traceback.format_exc()
            self.logger.debug(strExcDtl)
            sys.exit(0)

    def getIslandQueue(self, stockPriceId=None):
        
        local_island_queue = []
        
        headers = self.__get_headers()

        parsed_json = self.__get_my_island_raw()
        mysp = parsed_json['data']['myStockPrice']
        dictParam_body = {}
        dictParam_body['apikey'] = self.config_main['DODOApp_apikey']
        dictParam_body['appType'] = '3'
        # dictParam_body['clientTime'] = r'2022-04-23%2022%3A16%3A14'
        dictParam_body['clientTime'] = datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S')
        dictParam_body['clientType'] = '4' # '1' = iOS, '4' = Wechat Miniapp
        dictParam_body['clientVersion'] = '3.9.0'
        dictParam_body['deviceId'] = self.config_main['DODOApp_deviceId']
        dictParam_body['marketChannel'] = mysp['userInfo']['marketChannel']
        dictParam_body['packageName'] = 'com.dodolive.app' 
        dictParam_body['size'] = '20'
        dictParam_body['stockPriceId'] = mysp['id'] if stockPriceId is None else stockPriceId
        # dictParam_body['timestamp'] = '1650766574756'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['token'] = self.config_main['DODOApp_token']
        dictParam_body['uid'] = mysp['uid']
        dictParam_body['version'] = '1.0'

        data = self.__genStrParam(dictParam=dictParam_body)
        # print(data)
        # print(datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S'))

        # sys.exit(0)

        resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/animalCrossing/stock/list', 
            data = data.encode('utf-8'), headers = headers, comment = 'stock/list')
        try:
            parsed_json = resp.json()
            if parsed_json['status'] != 0:
                self.logger.error(resp.text)
                raise Exception
        except Exception as x:
            self.logger.critical('stock/list failed.')
            strExcDtl = traceback.format_exc()
            self.logger.debug(strExcDtl)
            sys.exit(0)
        
        for islandUser in parsed_json['data']['list']:
            local_island_queue.append(
                DODOApp_IslandQueueUser(    islandUser['id'],
                                            islandUser['uid'],
                                            islandUser['gameNickName'],
                                            islandUser['createTime'],
                                            islandUser['lastUpdateTime'],
                                            islandUser['nickName'],
                                            islandUser['times'],
                                            islandUser['rank']
                                            ))
        return local_island_queue

    def set_my_island_status(self,status):
        headers = self.__get_headers()

        parsed_json = self.__get_my_island_raw()
        mysp = parsed_json['data']['myStockPrice']
        dictParam_body = {}
        dictParam_body['apikey'] = self.config_main['DODOApp_apikey']
        dictParam_body['appType'] = '3'
        # dictParam_body['clientTime'] = r'2022-04-23%2022%3A16%3A14'
        dictParam_body['clientTime'] = datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S')
        dictParam_body['clientType'] = '4' # '1' = iOS, '4' = Wechat Miniapp
        dictParam_body['clientVersion'] = '3.9.0'
        dictParam_body['deviceId'] = self.config_main['DODOApp_deviceId']
        dictParam_body['marketChannel'] = mysp['userInfo']['marketChannel']
        dictParam_body['packageName'] = 'com.dodolive.app' 
        # dictParam_body['sig'] = '5dOFY/sveKC/gsOYHozYIHoaMpE%3D'
        dictParam_body['status'] = status # 2 = pause, 1 = resume
        dictParam_body['stockPriceId'] = mysp['id']
        # dictParam_body['timestamp'] = '1650766574756'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['token'] = self.config_main['DODOApp_token']
        dictParam_body['uid'] = mysp['uid']
        dictParam_body['version'] = '1.0'

        data = self.__genStrParam(dictParam=dictParam_body)
        
        resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/animalCrossing/stock/setStockPriceStatus', 
            data = data.encode('utf-8'), headers = headers, comment = 'setStockPriceStatus')
        try:
            parsed_json = resp.json()
            if parsed_json['status'] != 0:
                self.logger.error(resp.text)
                raise Exception
        except Exception as x:
            self.logger.critical('setStockPriceStatus failed.')
            strExcDtl = traceback.format_exc()
            self.logger.debug(strExcDtl)
            sys.exit(0)

    def closeIsland(self):
        headers = self.__get_headers()

        parsed_json = self.__get_my_island_raw()
        mysp = parsed_json['data']['myStockPrice']
        dictParam_body = {}
        dictParam_body['apikey'] = self.config_main['DODOApp_apikey']
        dictParam_body['appType'] = '3'
        # dictParam_body['clientTime'] = r'2022-04-23%2022%3A16%3A14'
        dictParam_body['clientTime'] = datetime.datetime.now().strftime('%Y-%m-%d%%20%H%%3A%M%%3A%S')
        dictParam_body['clientType'] = '4' # '1' = iOS, '4' = Wechat Miniapp
        dictParam_body['clientVersion'] = '3.9.0'
        dictParam_body['deviceId'] = self.config_main['DODOApp_deviceId']
        dictParam_body['marketChannel'] = mysp['userInfo']['marketChannel']
        dictParam_body['packageName'] = 'com.dodolive.app' 
        # dictParam_body['sig'] = '5dOFY/sveKC/gsOYHozYIHoaMpE%3D'
        dictParam_body['stockPriceId'] = mysp['id']
        # dictParam_body['timestamp'] = '1650766574756'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['token'] = self.config_main['DODOApp_token']
        dictParam_body['uid'] = mysp['uid']
        dictParam_body['version'] = '1.0'

        data = self.__genStrParam(dictParam=dictParam_body)
        
        resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/animalCrossing/stock/delete', 
            data = data.encode('utf-8'), headers = headers, comment = 'delete')
        try:
            parsed_json = resp.json()
            if parsed_json['status'] != 0:
                self.logger.error(resp.text)
                raise Exception
        except Exception as x:
            self.logger.critical('delete failed.')
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
        dictParam_body['clientType'] = '4' # '1' = iOS, '4' = Wechat Miniapp
        dictParam_body['clientVersion'] = '3.9.0'
        dictParam_body['content'] = urllib.parse.quote(content)
        dictParam_body['deviceId'] = self.config_main['DODOApp_deviceId']
        dictParam_body['marketChannel'] = mysp['userInfo']['marketChannel']
        dictParam_body['packageName'] = 'com.dodolive.app' 
        dictParam_body['relatedId'] = mysp['id']
        # dictParam_body['sig'] = '5dOFY/sveKC/gsOYHozYIHoaMpE%3D'
        dictParam_body['timestamp'] = str(calendar.timegm(time.gmtime())) + '513'
        dictParam_body['token'] = self.config_main['DODOApp_token']
        dictParam_body['type'] = '1'
        dictParam_body['uid'] = mysp['uid']
        dictParam_body['version'] = '1.0'

        data = self.__genStrParam(dictParam=dictParam_body)
        
        resp = sendRequest(method = 'post', url = 'https://apis.imdodo.com/animalCrossing/commentV2', 
            data = data.encode('utf-8'), headers = headers, comment = 'commentV2')
        try:
            parsed_json = resp.json()
            if parsed_json['status'] != 0:
                self.logger.error(resp.text)
                raise Exception
        except Exception as x:
            self.logger.critical('commentV2 failed.')
            strExcDtl = traceback.format_exc()
            self.logger.debug(strExcDtl)
            sys.exit(0)