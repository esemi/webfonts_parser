# -*- coding: utf-8 -*-

import re
import os
import urllib
import shlex
from datetime import datetime

from tornado.log import app_log
from tornado.web import MissingArgumentError, RequestHandler
import tornado.gen as gen
import tornado.process
from tornado.options import options
from tornado.httpclient import AsyncHTTPClient, HTTPError, HTTPRequest
import mmh3
import json


_FONT_TYPES = {'application/x-font-ttf': 'ttf', 'application/font-woff': 'woff',
               'application/font-woff2': 'woff2', 'application/vnd.ms-fontobject': 'eot'}


class BaseHandler(RequestHandler):
    def error_json_response(self, error):
        self.set_status(400)
        self.finish({'error': error})

    def success_json_response(self, data):
        self.set_status(200)
        self.finish({'data': data})

    @staticmethod
    @gen.coroutine
    def call_subprocess(cmd):
        args = shlex.split(cmd)
        steam = tornado.process.Subprocess.STREAM
        sub_process = tornado.process.Subprocess(args, stdout=steam, stderr=steam)
        result, error = yield [
            gen.Task(sub_process.stdout.read_until_close),
            gen.Task(sub_process.stderr.read_until_close)
        ]
        raise gen.Return((result, error))


class MainHandler(BaseHandler):
    @tornado.web.addslash
    def get(self):
        self.render("index.html")


class ParseRequestHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        """Order crawling and return font data or error"""
        try:
            query_url = self.get_argument('url')
            cache_disable = bool(int(self.get_argument('ignore-cache', default=0)))
        except MissingArgumentError:
            raise gen.Return(self.error_json_response('missing_arg'))

        app_log.info('parsing request: %s %s' % (query_url, cache_disable))
        valid_url = self.query_url_parse(query_url)
        if not valid_url:
            app_log.info('not valid url requested')
            raise gen.Return(self.error_json_response('not_valid_url'))

        # check cache
        font_summary = yield self.application.db.get_font_summary(valid_url)

        if cache_disable or not font_summary:
            app_log.info('parse start')
            phantom_res = yield self.phantom_parsing_call(valid_url)
            if not phantom_res:
                app_log.warn('phantom parsing fail')
                raise gen.Return(self.error_json_response('not_parsed_url'))
            app_log.info('found %d fonts' % len(phantom_res))

            fonts = yield self.fonts_crawling(phantom_res)
            if not fonts:
                app_log.warn('fonts crawling fail')
                raise gen.Return(self.error_json_response('not_crawled_fonts'))
            app_log.info('crawled %d fonts' % len(fonts))

            app_log.info('save font parse result to cache')
            yield self.fonts_save(valid_url, fonts)

        font_summary = yield self.application.db.get_font_summary(valid_url)
        raise gen.Return(self.success_json_response(font_summary))

    @staticmethod
    def query_url_parse(url):
        url_regexp = re.compile('^(http(s)?://)?(www\.)?(myfonts\.com/fonts/[^/]+/[^/]+)(/)?.*$',
                                re.IGNORECASE | re.UNICODE)
        try:
            clean_url = url_regexp.search(urllib.unquote(url.strip())).group(4)
        except AttributeError:
            return None
        else:
            return 'http://www.%s/' % clean_url

    def phantom_logs_save(self, url, stdout, stderr):
        filename = "%s_%s.log" % (mmh3.hash(url), str(datetime.now()))
        path = os.path.sep.join([self.application.app_path, 'data', 'app_logs', filename])
        # todo use https://github.com/felipecruz/pyaio
        with open(path, 'w') as f:
            f.write(url)
            f.write('\nstdout>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n')
            f.write(stdout)
            f.write('\nstderr>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n')
            f.write(stderr)

    @gen.coroutine
    def fonts_save(self, base_url, fonts):
        # todo remove unused fonts from file system
        app_log.info('save %s fonts' % base_url)
        base_hash = mmh3.hash(base_url)
        for font_key, item in enumerate(fonts):
            app_log.info('save %s font' % item['name'])
            font_hash = mmh3.hash(item['name'])
            new_fonts = []
            for f in item['fonts']:
                filename = "%s_%s.%s" % (base_hash, font_hash, f['type'])
                app_log.info('filename %s' % filename)
                web_path = os.path.sep.join(['static', 'fonts', filename])
                path = os.path.sep.join([self.application.app_path, web_path])
                # todo use https://github.com/felipecruz/pyaio
                with open(path, 'w') as fd:
                    fd.write(f['source'])
                new_fonts.append({'type': f['type'], 'filename': filename})
            fonts[font_key]['fonts'] = new_fonts
            del new_fonts

        yield self.application.db.save_font_summary(base_url, fonts)
        raise gen.Return()

    @staticmethod
    def phantom_result_parse(result_str):
        # todo unitest
        last_row = result_str.split("\n")[-2]
        if last_row.startswith('OK EXIT:'):
            return json.loads(last_row[8:])
        else:
            return False

    @gen.coroutine
    def phantom_parsing_call(self, url):
        app_log.info('phantom process start %s' % url)
        # todo proxy servers
        # todo logs path
        js_parser_path = os.path.sep.join([self.application.app_path, 'js_parser'])
        phantom_parser_cmd = "%s --ignore-ssl-errors='true' --load-images='false' --proxy=%s %s %swebfont_preview.html"\
                             % (os.path.sep.join([js_parser_path, 'phantomjs-1.9.8', 'phantomjs']),
                                '182.239.127.139:81', os.path.sep.join([js_parser_path, 'parser2.js']), url)
        app_log.info('command: <<%s>>' % phantom_parser_cmd)

        try:
            result, error = yield self.call_subprocess(phantom_parser_cmd)
        except Exception as e:
            app_log.warning('phantom crash: <<%s>>' % e)
            raise gen.Return(False)

        app_log.info('phantom process end: <<%d>> <<%d>>' % (len(result), len(error)))
        self.phantom_logs_save(url, result, error)

        raise gen.Return(self.phantom_result_parse(result))

    @staticmethod
    def fonts_response_parse(basic_fonts, responses):
        # todo unitest
        for r in responses:
            if r.code != 200 or r.error:
                app_log.warn('not success response found %d %s' % (r.code, r.error))
                return False
            if r.headers['Content-Type'] not in _FONT_TYPES.keys():
                app_log.warn('not valid content type found %s' % r.headers['Content-Type'])
                return False

        result = []
        for f in basic_fonts:
            app_log.info('parse %s fonts (%d)' % (f['name'], len(f['urls'])))
            tmp_urls = []
            for url in f['urls']:
                try:
                    response = filter(lambda r: r.request.url == url, responses)[0]
                except IndexError:
                    app_log.warn('not found response for selected font url %s %s' % (f['name'], url))
                    return False
                else:
                    tmp_urls.append({'type': _FONT_TYPES[response.headers['Content-Type']], 'source': response.body})
            result.append({'name': f['name'], 'fonts': tmp_urls})
        return result

    @gen.coroutine
    def fonts_crawling(self, basic_fonts):
        name_url_tuples = [(i['name'], url) for i in basic_fonts for url in i['urls']]
        num_conn = min(len(name_url_tuples), options.curl_conn)
        app_log.info('crawling start %d %d %d' % (len(name_url_tuples), num_conn, options.curl_timeout))

        AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient", max_clients=num_conn)
        http_client = AsyncHTTPClient()
        responses = []
        for i, item in enumerate(name_url_tuples):
            request = HTTPRequest(item[1], connect_timeout=options.curl_timeout, request_timeout=options.curl_timeout,
                                  follow_redirects=False)
            responses.append(http_client.fetch(request))

        app_log.info('wait complete all requests')

        # todo replace to raise_error=False param of http_client.fetch (next version Tornado)
        try:
            source_results = yield responses
        except HTTPError as e:
            app_log.warn('font request return http error %s' % e)
            raise gen.Return(False)

        app_log.info('start responses parse %d %d' % (len(basic_fonts), len(responses)))
        fonts_results = self.fonts_response_parse(basic_fonts, source_results)
        app_log.info('end responses parse')
        raise gen.Return(fonts_results)


class TmpHandler(BaseHandler):
    # todo TEST REAL CONCURENT ASYNC CALL SUBPROCESS FROM BROWSER
    # (ab test is success, but browser not is ab....)!!!
    @gen.coroutine
    def get(self):
        app_log.info('proc start')
        result, error = yield self.call_subprocess('sleep 10')
        app_log.info('proc end: %s %s' % (result, error))