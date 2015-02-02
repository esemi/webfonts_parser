# -*- coding: utf-8 -*-

import datetime

import motor
import tornado.gen as gen


class DB():
    def __init__(self):
        self.db = motor.MotorClient().web_fonts
        self.fonts = self.db.fonts
        self.fonts.ensure_index('url', unique=True, background=True, dropDups=True)

    @gen.coroutine
    def get_font_summary(self, valid_url):
        doc = yield self.fonts.find_one({'url': valid_url})
        if doc:
            raise gen.Return({'url': valid_url, 'variants': doc['variants']})
        else:
            raise gen.Return(None)

    @gen.coroutine
    def save_font_summary(self, valid_url, fonts):
        doc = {
            'url': valid_url,
            'date_create': datetime.datetime.now(),
            'variants': fonts
        }
        yield self.fonts.update({'url': valid_url}, doc, upsert=True)