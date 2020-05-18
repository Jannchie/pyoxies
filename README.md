# PYOXIES

Free Python Proxy Pool

## Feature

- Auto crawl free proxies
- Auto Adjust proxies quailty
- Easy to integrate

This is a web application, by maintaining a proxy IP pool and providing the relevant operation interface, to break through the visit frequency limit of the target site, support a short time to mass data crawling.

This application makes use of asyncio and aiohttp, realizes the function of high concurrency crawling free IP proxy through the coroutine technology, and evaluates the accessibility of IP proxy, so as to quickly screen out the available IP proxy pool.

This application provides API interface services using flask.

## Start

Install:

``` bash
clone git@github.com:Jannchie/pyoxies.git
cd proxies
pip3 install -r requirements.txt
```

---

Start server:

``` bash
python3 app.py
 * Running on http://127.0.0.1:5000/
```

Or

``` bash
$ export FLASK_APP=app.py
$ flask run --host 0.0.0.0 --port 52047
 * Running on http://127.0.0.1:52047/
```

## API Reference

| METHOD | PATH          | DESC                |
| ------ | ------------- | ------------------- |
| [GET]  | /proxy        | 获得所有的代理      |
| [GET]  | /proxy        | 获得所有的代理      |
| [GET]  | /proies/http  | 获得所有的HTTP代理  |
| [GET]  | /proies/https | 获得所有的HTTPS代理 |
| [POST] | /proies       | 添加一个代理        |
