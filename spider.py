import requests
from queue import SimpleQueue
from lxml.etree import HTML
from time import sleep


def get_proxies_from_hua(proxies: SimpleQueue):
  url = 'http://106.15.91.109:22333/ok_ips'
  res = requests.get(url)
  adrs = res.text[1:-1].replace('\'', '').replace(' ', '').split(',')
  for adr in adrs:
    proxies.put({'address': adr, 'protocol': 'http', 'type': 'unknown'})


def get_proxies_from_sslproxies(proxies: SimpleQueue):
  urls = [
      'https://free-proxy-list.net/',
      'https://www.sslproxies.org/'
  ]
  for url in urls:
    res = requests.get(url)
    html = HTML(res.text)
    addresses = html.xpath(
        '//*[@id="raw"]/div/div/div[2]/textarea/text()')[0].split('\n')[3:]
    for adr in addresses:
      proxies.put(
          {'address': adr, 'protocol': 'http', 'type': 'unknown'})
    sleep(1)
    pass


def get_proxies_from_xicidaili(proxies: SimpleQueue):
  for page in range(1, 3):
    sleep(1)
    res = requests.get(
        f'https://www.xicidaili.com/wn/{page}', headers={'user-agent': ''})
    html = HTML(res.text)
    if html == None:
      continue
    for tr in html.xpath('//table//tr')[1:]:
      i_pro = 5
      i_type = 4
      if tr[i_type] == 'HTTPS':
        i_pro = 4
        i_type = 3
      tr = tr.xpath('./td/text()')
      proxy = f'{tr[0]}:{tr[1]}'
      if tr[i_type] == '透明':
        tr[i_type] = 'transparent proxy'
      elif tr[i_type] == '高匿':
        tr[i_type] = 'elite proxy'
      elif tr[i_type] == '匿名':
        tr[i_type] == 'anonymous'
      else:
        tr[i_type] = 'unknown'
        pass
      proxies.put(
          {'address': proxy, 'protocol': tr[i_pro].lower(), 'type': tr[i_type]})
    pass
