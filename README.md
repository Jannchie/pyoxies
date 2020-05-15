# PYOXIES

Python Proxy Pool

This is a web application, by maintaining a proxy IP pool and providing the relevant operation interface, to break through the visit frequency limit of the target site, support a short time to mass data crawling.

This application makes use of asyncio and aiohttp, realizes the function of high concurrency crawling free IP proxy through the coroutine technology, and evaluates the accessibility of IP proxy, so as to quickly screen out the available IP proxy pool.

This application provides API interface services using flask.


## Start

``` shell
$ export FLASK_APP=app.py
$ flask run
 * Running on http://127.0.0.1:5000/
 ```
