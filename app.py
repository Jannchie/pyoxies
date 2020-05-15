import logging
from logging.config import dictConfig
from apscheduler.schedulers.background import BackgroundScheduler
from concurrent.futures import ThreadPoolExecutor
from flask import request
from pool import ProxyPool
from flask import Flask, jsonify
from random import randint
import schedule
from util import logger

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)


pp = ProxyPool()
pp.build_proxy_set()


def get_proxy_set_length():
  global pp
  logger.critical(f'Available Proxies Count: {len(pp.proxy_set)}')


def get_one_proxy():
  proxy_gener = single_proxy_gener()


@app.route('/rejudge')
def rejudge():
  logger.critical(f'Rejudge Proxies Started!')
  with ThreadPoolExecutor(2) as executor:
    executor.submit(pp.rejudge_proxy_set())
  logger.critical(f'Rejudge Proxies Finished!')
  return 'ok'


@app.route('/proxy/add')
def add_multi_proxy():
  logger.critical(f'Adding Proxies Started!')
  count = len(pp.proxy_set)
  if count > 100:
    logger.critical(f'Available Proxies Enough (Count = {count})')
    return 'ok'
  with ThreadPoolExecutor(2) as executor:
    executor.submit(pp.add_proxy_set())
  logger.critical(f'Adding Proxies Finished!')
  return 'ok'


@app.route('/')
def hello_world():
  return '[GET] /proxy 获得一个代理\n'


@app.route('/proxy', methods=['GET', 'POST', 'DELETE'])
def get_one():
  if request.method == 'GET':
    return pp.get_one_proxy()
  elif request.method == 'POST':
    pc.raw_proxies.put({'address': request.get_data().decode("utf-8"),
                        'protocol': 'https', 'type': 'unknown'})
    return "SUCCESS"
  elif request.method == 'DELETE':
    pass


scheduler = BackgroundScheduler()
scheduler.add_job(get_proxy_set_length, 'interval', minutes=1)
scheduler.add_job(add_multi_proxy, 'interval', minutes=15)
scheduler.add_job(rejudge, 'interval', minutes=5)
scheduler.start()
