#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'esemi'


import unittest

from webfonts.components.handlers import ParseRequestHandler


class QueryUrlParserTest(unittest.TestCase):

    _parser = None

    def setUp(self):
        self._parser = ParseRequestHandler.query_url_parse

    def test_success(self):
        urls = [
            # basic full url
            (u'http://www.myfonts.com/fonts/typesetit/the-nauti-gal/', u'http://www.myfonts.com/fonts/typesetit/the-nauti-gal/'),
            # basic full url ssl
            (u'https://www.myfonts.com/fonts/typesetit/the-nauti-gal/', u'http://www.myfonts.com/fonts/typesetit/the-nauti-gal/'),
            # encoded full url
            (u'http%3A%2F%2Fwww.myfonts.com%2Ffonts%2Ftypesetit%2Fthe-nauti-gal%2F', u'http://www.myfonts.com/fonts/typesetit/the-nauti-gal/'),
            # url w/o scheme
            (u'www.myfonts.com/fonts/typesetit/the-nauti-gal/', u'http://www.myfonts.com/fonts/typesetit/the-nauti-gal/'),
            # url w/o www
            (u'https://myfonts.com/fonts/typesetit/the-nauti-gal/', u'http://www.myfonts.com/fonts/typesetit/the-nauti-gal/'),
            # url w/o scheme and www
            (u'myfonts.com/fonts/typesetit/the-nauti-gal/', u'http://www.myfonts.com/fonts/typesetit/the-nauti-gal/'),
            # url w/o scheme, www and tail slash
            (u'myfonts.com/fonts/typesetit/the-nauti-gal', u'http://www.myfonts.com/fonts/typesetit/the-nauti-gal/'),
            # url w/ postfix
            (u'http://www.myfonts.com/fonts/typesetit/the-nauti-gal/webfont_preview.html', u'http://www.myfonts.com/fonts/typesetit/the-nauti-gal/'),
            (u'myfonts.com/fonts/typesetit/the-nauti-gal/webfontsdasd/asdasd/_preview.html', u'http://www.myfonts.com/fonts/typesetit/the-nauti-gal/'),
        ]

        for i, (url, success) in enumerate(urls):
            res = self._parser(url)
            self.assertEqual(res, success, 'case num %d' % i)

    def test_error(self):
        urls = [
            u'hsdasdttp://www.myfonts.com/fonts/typesetit/the-nauti-gal/webfont_preview.html',
            u'otherfonts.com/fonts/typesetit/the-nauti-gal/webfont_preview.html',
        ]

        for url in urls:
            res = self._parser(url)
            self.assertIsNone(res)

if __name__ == '__main__':
    unittest.main()
