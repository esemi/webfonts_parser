#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'esemi'

import os.path
import sys

import tornado.ioloop
from tornado.web import Application
import tornado.gen
import tornado.escape
import tornado.httpserver
from tornado.options import define, options, parse_command_line

from components import uimodules
from components.handlers import MainHandler, ParseRequestHandler, TmpHandler
from components.models import DB


APP_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="enable debug mode", type=bool)
define("curl_conn", default=50, help="crawler connections count", type=int)
define("curl_timeout", default=30, help="crawler connection timeout", type=int)
define("cookie_secret", default='@TODO', help="set u cookie secret value into config.py", type=str)


def make_app():
    handlers = [
        (r"/?", MainHandler),
        (r"/parse/", ParseRequestHandler),
        (r"/tmp/", TmpHandler),
    ]

    settings = dict(
        cookie_secret=options.cookie_secret,
        template_path=os.path.join(APP_DIR, "templates"),
        static_path=os.path.join(APP_DIR, "static"),
        xsrf_cookies=True,
        ui_modules=uimodules,
        debug=options.debug
    )

    app = Application(handlers, **settings)
    app.db = DB()
    app.app_path = APP_DIR

    return app


if __name__ == "__main__":
    parse_command_line()

    # todo add logs path to options
    # todo add PYTHONPATH to supervisord.conf ?

    app = make_app()
    http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
    http_server.bind(options.port, address='127.0.0.1')
    http_server.start()

    tornado.ioloop.IOLoop.instance().start()