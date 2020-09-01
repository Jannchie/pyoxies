from main import ProxyPool
import logging
from logging.config import dictConfig

from datetime import datetime
from flask import request
from flask import Flask, jsonify
from random import randint
from util import logger

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)


@app.route('/')
def hello_world():
  http_count = len(pp.available_http_proxy_set)
  https_count = len(pp.available_https_proxy_set)
  state = f"<h1>总体运行状态</h1>"
  state += f"<div>运行时间: {datetime.now() - pp.start_time }</div>"
  state += f"<div>鉴定效率: {pp.total_judged /( datetime.now() - pp.start_time).total_seconds()} 个/秒</div>"
  state += f"Unadjudge Proxy Count: { pp.un_adjudge_proxy_queue.qsize()}<br>" + \
      f"Total Adjudge Count: { pp.total_judged}<br>" + \
      f"Available HTTP Proxies Count: { http_count }<br>" + \
      f"Available HTTPS Proxies Count: { https_count }<br>" + \
      f"Available Proxies Count: { http_count + https_count }<br>"
  if len(pp.statistic) != 0:
    state += f"<h1>各爬虫运行状态</h1>"
  for source in pp.statistic:
    state += f"{source} Sum: {pp.statistic[source]['sum']}, Pass: {pp.statistic[source]['success']}, Rate: { round(pp.statistic[source]['success'] / pp.statistic[source]['sum'] * 100,2)}%<br>"
  return f'''
  <div>
    {state}
  </div>
  <h1>API列表</h1>
  <table>
    <tr>
      <td>[GET]</td>
      <td><a href="/proxy">/proxy</a></td>
      <td>获得所有的代理</td>
    </tr>
    <tr>
      <td>[GET]</td>
      <td><a href="/proxies">/proxies</a></td>
      <td>获得所有的代理</td>
    </tr>
    <tr>
      <td>[GET]</td>
      <td><a href="/proxies/http">/proxies/http</a></td>
      <td>获得所有的HTTP代理</td>
    </tr>
    <tr>
      <td>[GET]</td>
      <td><a href="/proxies/https">/proxies/https</a></td>
      <td>获得所有的HTTPS代理</td>
    </tr>
    <tr>
      <td>[POST]</td>
      <td>/proxy</td>
      <td>添加一个代理</td>
    </tr>
  </table>
  '''


@app.route('/proxies')
def get_all():
  return jsonify({'proxies': pp.get_all_proxy()})


@app.route('/proxies/http')
def get_http():
  return jsonify({'proxies': pp.get_http_proxy()})


@app.route('/proxies/https')
def get_https():
  return jsonify({'proxies': pp.get_https_proxy()})


@app.route('/proxy', methods=['GET', 'POST'])
def get_one():
  if request.method == 'GET':
    return jsonify({'proxies': pp.get_all_proxy()})
  elif request.method == 'POST':
    ip = request.get_data().decode("utf-8")
    pp.flask_put_proxy(ip)
    logger.info(f'Post: {ip}')
    return "SUCCESS"


if __name__ == "__main__":
  pp = ProxyPool()
  app.run()
