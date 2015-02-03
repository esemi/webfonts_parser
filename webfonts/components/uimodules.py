# -*- coding: utf-8 -*-

import tornado.web
import tornado.escape


class XSRFInput(tornado.web.UIModule):
    def render(self):
        return '<input type="hidden" value="%s" id="csrf-token"/>' % tornado.escape.xhtml_escape(
            self.handler.xsrf_token)