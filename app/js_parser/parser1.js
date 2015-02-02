/*
 * Вариант скрипта парсинга, когда мы заходим на страницу и перекликиваем все шрифты в селекторе
 * чистит уже загруженные шрифты на каждой итерации
 * перехватывает запрошенные шрифты
 * парсит только woff
 */

var page = require('webpage').create(),
    system = require('system'),
    fs = require('fs'),
    preview_url,
    parsed_font_name = null,
    result = [],
    global_timeout = 30*1000,
    loop_timeout = 300;

if (system.args.length === 1) {
    fail_exit("Usage: parser.js <font name>")
} else {
    main(system.args[1]);
}

function main(font_name) {
    preview_url = "http://www.myfonts.com/fonts/paratype/" + font_name + "/webfont_preview.html"
    console.log('requested url ' + preview_url);

    page.onConsoleMessage = function (msg) {
        console.log(msg);
    };

    page.onResourceRequested = function(requestData, networkRequest) {
        if (requestData.url.search(/\/woff\?/i) >= 0) {
            if (parsed_font_name) {
                save_font_url(parsed_font_name, requestData.url);
                networkRequest.abort();
                parsed_font_name = null;
            }
        }
    };

    setTimeout(function() { fail_exit('global timeout'); }, global_timeout);

    page.open(preview_url, function (status) {
        console.log('preview page title ' + page.title);
        if (status !== 'success') {
            fail_exit('fail to load the address')
        }

        var filename = './data/phantom_requests/' + font_name + '_' + new Date().toISOString() + '.html';
        fs.write(filename, page.content, 'w');

        var options_source = get_options();
        var options = JSON.parse(options_source);
        console.log('found options len ' + options.length);

        //custom loop (wait font processing before next option)
        delayed_change_loop(options, 0);
    });
}

function selector_change_event(option_num){
    page.evaluate(function(option_num){
        FontFacePreviews.loaded = [];
        FontFacePreviews.requested = [];
        var selector = document.querySelector('#fontface_previews select');
        var options = selector.querySelectorAll('option');
        options[option_num].selected = true;
        var ev = document.createEvent("MouseEvent");
        ev.initMouseEvent(
            "change", true /* bubble */, true /* cancelable */,
            window, null,
            0, 0, 0, 0, /* coordinates */
            false, false, false, false, /* modifier keys */
            0 /*left*/, null
        );
        selector.dispatchEvent(ev);
    }, option_num);
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

function save_font_url(name, url) {
    console.log('load font ' + name);
    console.log('load font url' + url);
    result.push({name: name, urls: [url]});
}

function success_exit() {
    console.log('parsed urls ' + result.length);
    console.log('OK EXIT:' + JSON.stringify(result));
    phantom.exit(0);
}

function fail_exit(msg) {
    console.log('FAIL EXIT:' + msg);
    phantom.exit(1);
}

function delayed_change_loop(options, current_num) {
    // custom loop (wait font processing before next option)
    console.log(
        'change loop call: options len ' + options.length +
        '; result len ' + result.length +
        '; current name is ' + parsed_font_name +
        '; current num is ' + current_num
    );

    if (result.length == options.length) {
        success_exit();
    }

    if (parsed_font_name) {
        console.log('wait already parsed option');
    } else if (current_num > options.length + 1) {
        console.log('all options requested');
    } else {
        var option = options[current_num];
        console.log('parse option ' + JSON.stringify(option));
        parsed_font_name = option['name'];
        selector_change_event(current_num);
        current_num++;
    }

    setTimeout(function(){ delayed_change_loop(options, current_num)}, loop_timeout)
}