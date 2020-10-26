import time
import asyncio
import aiohttp
from datetime import datetime
from lxml.etree import HTML
import threading
import logging
from util import logger
from asyncio import TimeoutError

from concurrent.futures import ThreadPoolExecutor
import concurrent
io_pool_exc = ThreadPoolExecutor()


class Res():
  def __init__(self):
    self.status = 'err'


class ProxyPool():
  def __init__(self):
    super().__init__()
    self.start_time = datetime.now()

    self.get_proxy_interval = 60 * 30
    self.review_interval = 60
    self.pass_timeout = 3
    self.review_threshold = 25
    self.fetch_threshold = 200
    self.adjudicator_number = 256
    self.reviewer_number = 128

    self.un_adjudge_proxy_queue = asyncio.Queue()
    self.review_proxy_queue = asyncio.Queue()

    self.total_judged = 0
    self.available_http_proxy_set = set()
    self.available_https_proxy_set = set()
    self.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(self.loop)

    self.loop.create_task(self.__post_review())
    self.loop.create_task(self.__forever_put_proxy())
    self.loop.create_task(self.__print_state())
    self.statistic = dict()
    self.core_threading = threading.Thread(
        name=f"pool-core", target=self.__run)
    self.core_threading.start()
    self.adjudicator_semaphore = asyncio.Semaphore(self.adjudicator_number)
    self.reviewer_semaphore = asyncio.Semaphore(self.reviewer_number)

  def __run(self):
    # loop.set_debug(True)
    self.loop.create_task(self.__judge())
    # self.loop.run_in_executor(io_pool_exc, f.readline)
    self.loop.create_task(self.__review())
    self.loop.run_forever()

  def get_all_proxy(self):
    return list(self.available_http_proxy_set) + list(self.available_https_proxy_set)

  def get_http_proxy(self):
    return list(self.available_http_proxy_set)

  def get_https_proxy(self):
    return list(self.available_https_proxy_set)

  async def __print_state(self):
    while True:
      logger.info(
          f"Unadjudge Proxy Count: { self.un_adjudge_proxy_queue.qsize()}")
      logger.info(f"Total Adjudge Count: { self.total_judged}")
      http_count = len(self.available_http_proxy_set)
      https_count = len(self.available_https_proxy_set)
      logger.info(
          f"Available HTTP Proxies Count: { http_count }")
      logger.info(
          f"Available HTTPS Proxies Count: { https_count }")
      logger.info(
          f"Available Proxies Count: { http_count + https_count }")
      logger.info("Get Interval: %s, Review Interval: %s, Pass Timeout: %s" % (self.get_proxy_interval,
                                                                               self.review_interval,
                                                                               self.pass_timeout))
      await asyncio.sleep(30)
    pass

  async def __post_review(self):
    while True:
      await asyncio.sleep(self.review_interval)
      if len(self.get_all_proxy()) >= self.review_threshold and self.review_proxy_queue.qsize() == 0:
        temp_proxies = list(self.available_http_proxy_set)
        temp_proxies += list(self.available_https_proxy_set)
        for proxy in temp_proxies:
          await asyncio.sleep(0.1)
          await self.review_proxy_queue.put(proxy)

  async def __send_review(self, proxy):
    async with self.reviewer_semaphore:
      is_pass, protocol = await self.__judge_ip({'proxy': proxy, 'source': "Reviewer"}, f'Reviewer    ')
    if not is_pass:
      self.available_http_proxy_set.discard(proxy)
      self.available_https_proxy_set.discard(proxy)

  async def __review(self):
    await asyncio.sleep(1)
    while True:
      if not self.review_proxy_queue.empty():
        proxy = await self.review_proxy_queue.get()
        self.review_proxy_queue.task_done()
        async with self.reviewer_semaphore:
          self.loop.create_task(self.__send_review(proxy))
      else:
        await asyncio.sleep(0.1)

  async def put_proxy(self, proxy, source):

    await self.un_adjudge_proxy_queue.put({'proxy': proxy, 'source': source})

  def flask_put_proxy(self, proxy):
    self.loop.create_task(self.un_adjudge_proxy_queue.put(
        {'proxy': proxy, 'source': 'server'}))

  async def __get_proxy_from_free_proxy(self, session):
    '''
    Crawl data from 89ip.
    '''
    try:
      # url = 'http://free-proxy.cz/zh/proxylist/country/all/all/ping/level1/%d'
      # for page in range(1, 3):
      #   res = await session.get(url % page, timeout=10)
      #   text = await res.text()
      #   html = HTML(text)
      #   for data in html.xpath('//table/tbody/tr'):
      #     pass
      #   await asyncio.sleep(3)
      pass
    except Exception as e:
      logging.exception(e)
      pass

  async def __get_proxy_from_yundaili(self, session):
    '''
    Crawl data from yundaili.
    '''
    url = 'http://www.ip3366.net/free/?stype=4422&page={}'
    try:
      for page in range(1, 3):
        res = await session.get(url.format(page), timeout=10)
        text = await res.text()
        html = HTML(text)
        for data in html.xpath('//table/tbody/tr'):
          row = data.xpath('.//td/text()')
          address = row[0].replace('\n', '').replace('\t', '')
          port = row[1].replace('\n', '').replace('\t', '')
          await self.put_proxy(f'http://{address}:{port}', '云代理')
        await asyncio.sleep(3)
    except Exception as e:
      logging.exception(e)
      pass

  async def __get_proxy_from_xiaohuan(self, session):
    page = ''
    url = "https://ip.ihuan.me/address/{}"
    count = 0
    while count < 3:
      res = await session.get(url.format(page), timeout=10)
      text = await res.text()
      html = HTML(text)
      for tr in html.xpath('//tbody/tr'):
        ip = tr.xpath('./td[1]/a/text()')
        port = tr.xpath('./td[2]/text()')
        await self.put_proxy(f'http://{ip[0]}:{port[0]}', '小幻代理')
      page = html.xpath('//nav/ul/li/a/@href')[1]
      await asyncio.sleep(1)
      count += 1

  async def __get_proxy_from_nimadaili(self, session):
    '''
    Crawl data from nimadaili.
    '''
    try:
      for cata in ['gaoni']:
        for page in range(1, 5):
          res = await session.get(f'http://www.nimadaili.com/{cata}/{page}/', timeout=10)
          text = await res.text()
          html = HTML(text)
          for data in html.xpath('//table/tbody/tr'):
            row = data.xpath('.//td/text()')
            address = row[0]
            await self.put_proxy(f'http://{address}', '尼玛代理')
          await asyncio.sleep(3)
    except Exception as e:
      logging.exception(e)
      pass

  async def __get_proxy_from_jiangxianli(self, session):
    try:
      url = 'https://ip.jiangxianli.com/api/proxy_ips?page={}&order_by=validated_at&order_rule=DESC'
      for page in range(1, 5):
        pass
        res = await session.get(url.format(page), timeout=10)
        j = await res.json()
        for proxy_info in j['data']['data']:
          await self.put_proxy('http://{ip}:{port}'.format(**proxy_info), '江西安利')
          pass
        await asyncio.sleep(3)
    except Exception as e:
      logging.exception(e)
      pass
#

  async def __get_proxy_from_kuai(self, session):
    '''
    Crawl data from kuai.
    '''
    try:
      for page in range(1, 5):
        url = f'https://www.kuaidaili.com/free/inha/{page}/'
        res = await session.get(url, timeout=10)
        text = await res.text()
        html = HTML(text)
        for data in html.xpath('//table/tbody/tr'):
          ip = data.xpath('.//td[1]/text()')[0]
          port = data.xpath('.//td[2]/text()')[0]
          await self.put_proxy(f'http://{ip}:{port}', '快代理')
    except Exception as e:
      logging.exception(e)
      pass

  async def __get_proxy_from_hua(self, session):
    '''
    Crawl data from hua er bu ku.
    '''
    try:
      url = 'http://106.15.91.109:34333/ok_ips'
      res = await session.get(url, timeout=10)
      text = await res.text()
      adrs = text[1:-1].replace('\'', '').replace(' ', '').split(',')
      for adr in adrs[0:2000]:
        await self.put_proxy(f'http://{adr}', '花儿不哭')
    except Exception as e:
      logging.exception(e)
      pass

  async def __get_proxy_from_xila(self, session):
    '''
    Crawl data from xiladaili.
    '''
    try:
      for page in range(1, 5):
        url = f'http://www.xiladaili.com/gaoni/{page}/'
        res = await session.get(url, timeout=10)
        text = await res.text()
        html = HTML(text)
        for data in html.xpath('//table/tbody/tr'):
          ip = data.xpath('.//td[1]/text()')[0]
          await self.put_proxy(f'http://{ip}', '西拉代理')
    except Exception as e:
      logging.exception(e)
      pass

  async def __get_proxies_from_sslproxies(self, session):
    urls = [
        'https://www.sslproxies.org/',
        'https://www.us-proxy.org/',
        'https://free-proxy-list.net/',
        'https://free-proxy-list.net/uk-proxy.html',
        'https://free-proxy-list.net/anonymous-proxy.html'
    ]
    idx = 0
    proxies = self.get_https_proxy()
    for url in urls:
      i = 5
      while i > 0:
        await asyncio.sleep(3)
        try:
          if len(proxies) <= idx:
            idx = 0
          res = await session.get(url,  proxy='', timeout=10)
          html = HTML(await res.text())
          addresses = html.xpath(
              '//*[@id="raw"]/div/div/div[2]/textarea/text()')[0].split('\n')[3:]
          for adr in addresses:
            await self.put_proxy('http://' + adr, 'sslproxies')
          break
        except Exception:
          i -= 1
          if idx + 1 > len(proxies):
            proxies = self.get_https_proxy()
          idx += 1
          if (idx >= len(proxies)):
            idx == 0
          logger.exception(f"Parse {url} Fail")
      await asyncio.sleep(1)

  async def __proxylistplus(self, session):
    url = 'https://list.proxylistplus.com/Fresh-HTTP-Proxy-List-1'
    res = await session.get(url,  proxy='', timeout=10)
    html = HTML(await res.text())
    rows = html.xpath('//tr[@class="cells"]')[1:]
    for row in rows:
      r = row.xpath('./td/text()')
      await self.put_proxy(f'http://{r[0]}:{r[1]}', 'proxy list plus')

  async def __forever_put_proxy(self):
    '''
    For adding a proxy task, crawl data from other website.
    '''
    session = aiohttp.ClientSession()
    while True:
      try:
        if self.un_adjudge_proxy_queue.qsize() == 0 and len(self.get_all_proxy()) <= self.fetch_threshold:
          tasks = [
              # self.loop.create_task(self.__get_proxy_from_kuai(session)),
              self.loop.create_task(self.__proxylistplus(session)),
              self.loop.create_task(self.__get_proxy_from_xiaohuan(session)),
              self.loop.create_task(
                  self.__get_proxy_from_jiangxianli(session)),
              self.loop.create_task(self.__get_proxy_from_hua(session)),
              self.loop.create_task(self.__get_proxy_from_nimadaili(session)),
              # self.loop.create_task(self.__get_proxy_from_yundaili(session)),
              self.loop.create_task(self.__get_proxy_from_xila(session)),
              # self.loop.create_task(self.__get_proxy_from_free_proxy(session)),
              # self.loop.create_task(self.__get_proxy_from_89(session)),
              # self.loop.create_task(
              #     self.__get_proxies_from_sslproxies(session))
          ]
          await asyncio.wait(tasks)
        await asyncio.sleep(15)
      except Exception as e:
        self.logger.exception(e)
    await session.close()

  async def __send_judge(self, proxy_info):
    async with self.adjudicator_semaphore:
      is_pass, protocol = await self.__judge_ip(proxy_info, f'Adjudicator ')
    if is_pass:
      if protocol == 'http ':
        self.available_http_proxy_set.add(proxy_info['proxy'])
      else:
        self.available_https_proxy_set.add(proxy_info['proxy'])
    self.total_judged += 1

  async def __judge(self):
    '''
    Judge task.
    '''
    await asyncio.sleep(1)
    while True:
      try:
        if not self.un_adjudge_proxy_queue.empty():
          proxy_info = await self.un_adjudge_proxy_queue.get()
          self.un_adjudge_proxy_queue.task_done()
          async with self.adjudicator_semaphore:
            self.loop.create_task(self.__send_judge(proxy_info))
        else:
          await asyncio.sleep(1)
      except Exception as e:
        logging.exception(e)

  async def __get_judge_result(self, proxy):
    '''
    Successively judege whether the HTTPS request or the HTTP request can be successfully proxy.
    '''
    try:
      async with aiohttp.ClientSession() as session:
        for protocol in ['http', 'https']:
          delta_t = 0
          start_t = datetime.now()
          retry = 3
          count = 0
          mid_1 = 1
          mid_2 = 1
          flag = 0
          for i in range(retry):
            res = Res()
            try:
              count += 1
              try:
                res = await session.get(
                    f'{protocol}://api.bilibili.com/x/relation/stat?vmid=7', proxy=proxy, timeout=5)
              except concurrent.futures._base.TimeoutError as e:
                continue
              except aiohttp.client_exceptions.ServerDisconnectedError as e:
                return ('dis', round(delta_t.total_seconds() / count, 1), 'disco')
              if res.status == 200:
                # 成功
                j = await res.json()
                mid_1 = j['data']['mid']
                break
              elif res.status in [500, 412]:
                break
              elif retry - 1 == i:
                # 重试次数用完
                if protocol == 'http':
                  flag = 1
                  continue
                delta_t = datetime.now() - start_t
                return (res.status, round(delta_t.total_seconds() / count, 1), 'error')
            except Exception as e:
              if retry - 1 == i:
                if protocol == 'http':
                  flag = 1
                  continue
                delta_t = datetime.now() - start_t
                return (res.status, round(delta_t.total_seconds() / count, 1), 'error')
          if flag == 1:
            continue
          for i in range(retry):
            res = Res()
            try:
              count += 1
              res = await session.get(
                  f'{protocol}://api.bilibili.com/x/relation/stat?vmid=1850091', proxy=proxy, timeout=5)
              if res.status == 200:
                j = await res.json()
                mid_2 = j['data']['mid']
                break
              elif retry - 1 == i:
                if protocol == 'http':
                  flag = 1
                  continue
                delta_t = datetime.now() - start_t
                return (res.status, round(delta_t.total_seconds() / count, 1), 'error')
            except Exception as e:
              if retry - 1 == i:
                if protocol == 'http':
                  flag = 1
                  continue
                delta_t = datetime.now() - start_t
                return (res.status, round(delta_t.total_seconds() / count, 1), 'error')
          if flag == 1:
            continue
          delta_t = datetime.now() - start_t
          if mid_1 != mid_2:
            return (res.status, round(delta_t.total_seconds() / count, 1), protocol)
          else:
            return ('cac', round(delta_t.total_seconds() / count, 1), 'cache')
        # await session.close()
    except Exception as e:
      pass

  async def __judge_ip(self, proxy_info, name):
    proxy = proxy_info['proxy']
    source = proxy_info['source']
    try:
      code, t, protocol = await asyncio.wait_for(
          self.__get_judge_result(proxy), 10)
    except Exception as e:
      code = "tim"
      t = 9.9
      protocol = 'timeo'
    if code == 200:
      state = '\033[1;32m PASS \033[0m'
      if t > self.pass_timeout:
        state = '\033[1;33m SLOW \033[0m'
        flag = True
      else:
        flag = True
    else:
      state = '\033[1;31m FAIL \033[0m'
      flag = False
    if protocol == 'http':
      protocol += ' '
    logger.info(
        f'[ {name} ] [{state}] ({code}) {t}s <{protocol} {proxy}> From {source}')
    if source in self.statistic:
      self.statistic[source]['sum'] += 1
      if flag:
        self.statistic[source]['success'] += 1
    else:
      self.statistic[source] = {}
      self.statistic[source]['sum'] = 1
      self.statistic[source]['success'] = 1 if flag else 0
    return flag, protocol


if __name__ == "__main__":
  ProxyPool()
