#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'esemi'

import os.path
import sys

import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.escape
import tornado.httpserver
from tornado.options import define, options, parse_config_file

from components import uimodules
from components.handlers import MainHandler, ParseRequestHandler, TmpHandler
from components.models import DB


APP_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="enable debug mode", type=bool)
define("curl_conn", default=50, help="crawler connections count", type=int)
define("curl_timeout", default=30, help="crawler connection timeout", type=int)
define("cookie_secret", help="set u cookie secret value into config.py", type=str)


class Application(tornado.web.Application):
    def __init__(self):
        self.db = DB()
        self.app_path = APP_DIR

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

        super(Application, self).__init__(handlers, **settings)


if __name__ == "__main__":
    os.chdir(APP_DIR)
    parse_config_file("config.py")
    app = Application()

    # TODO run one app per core
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.bind(options.port)
    http_server.start()

    tornado.ioloop.IOLoop.instance().start()