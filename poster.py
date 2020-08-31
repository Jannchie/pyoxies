import time
import asyncio
import aiohttp
from datetime import datetime
from lxml.etree import HTML
import threading
import logging
from util import logger
from asyncio import TimeoutError


class Poster():
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
          res = await session.get(url,  proxy='' if len(proxies) == 0 else proxies[idx], timeout=10)
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
