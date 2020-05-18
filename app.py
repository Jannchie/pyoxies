from main import ProxyPool
import logging
from logging.config import dictConfig

from flask import request
from flask import Flask, jsonify
from random import randint
import schedule
from util import logger

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

pp = ProxyPool()


@app.route('/')
def hello_world():
  return'''
  <table>
    <tr>
      <td>[GET]</td>
      <td>/proxy</td>
      <td>获得所有的代理</td>
    </tr>
    <tr>
      <td>[GET]</td>
      <td>/proxy</td>
      <td>获得所有的代理</td>
    </tr>
    <tr>
      <td>[GET]</td>
      <td>/proies/http</td>
      <td>获得所有的HTTP代理</td>
    </tr>
    <tr>
      <td>[GET]</td>
      <td>/proies/https</td>
      <td>获得所有的HTTPS代理</td>
    </tr>
    <tr>
      <td>[POST]</td>
      <td>/proies</td>
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
    pc.put_proxy(request.get_data().decode("utf-8"))
    return "SUCCESS"


if __name__ == "__main__":
  app.run()
