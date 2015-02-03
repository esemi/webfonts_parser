/*
 * Вариант скрипта парсинга, когда хаходим на страницу шрифта и парсим css из объекта дома
 * идём на просмотр шрифта
 * парсим css свойство
 */


var page = require('webpage').create(),
    system = require('system'),
    parser = require('./css_parser'),
    fs = require('fs'),
    global_timeout = 30*1000;

if (system.args.length === 1) {
    fail_exit("Usage: css_parsing.js <webfont preview url> (Example: css_parsing.js http://www.myfonts.com/fonts/urw/news-gothic/webfont_preview.html)")
} else {
    main(system.args[1]);
}

function main(preview_url) {
    console.log('requested url ' + preview_url);

    var font_name = preview_url.split('/').slice(-2, -1);
    console.log('requested font name ' + font_name);

    page.onConsoleMessage = function (msg) {
        console.log(msg);
    };

    setTimeout(function() { fail_exit('global timeout'); }, global_timeout);

    page.open(preview_url, function (status) {
        console.log('preview page title ' + page.title);
        if (status !== 'success') {
            fail_exit('fail to load the address')
        }

        var filename = './data/phantom_requests/' + font_name + '_' + new Date().toISOString() + '.html';
        console.log('debug: ' + fs.write(filename, page.content, 'w'));

        var options_source = get_options();
        var options = JSON.parse(options_source);
        console.log('found options len ' + options.length);

        var css_source = get_css();
        console.log('found css source ' + css_source.length);
        var css_filename = './data/phantom_requests/' + font_name + '_' + new Date().toISOString() + '.css';
        fs.write(css_filename, css_source, 'w');

        var result = parser.parse_css(css_source, options.map(function(e) { return e.name; }));
        if (options.length === result.length) {
            success_exit(result);
        } else {
            fail_exit('not all fonts parsed');
        }
    });
}

function get_css() {
    return page.evaluate(function(){
        return FontFacePreviews.css;
    });
}

function get_options() {
    return page.evaluate(function(){
        var out = [];
        var selector = document.querySelector('#fontface_previews select');
        if (!selector) {
            console.log('not found font selector');
        } else {
            var options = selector.querySelectorAll('option');
            for(var i= 0; i<options.length; i++) {
                var el = options[i];
                out.push({'id': el.id, 'name': el.text, 'html': el.outerHTML});
            }
        }
        return JSON.stringify(out);
    });
}

function success_exit(result) {
    console.log('parsed fonts ' + result.length);
    console.log('OK EXIT:' + JSON.stringify(result));
    phantom.exit(0);
}

function fail_exit(msg) {
    console.log('FAIL EXIT:' + msg);
    phantom.exit(1);
}
