var fs = require('fs'),
    system = require('system');


if (system.args.length > 1 && system.args[1] == 'test') {
    console.log('TEST MODE ENABLE');
    test();
    phantom.exit(0);
}

exports.parse_css = parse_css;


function parse_css(source, font_names) {
    var source_strs = source.split("\n").filter(function(r) {
        return (r.indexOf('@font-face') == 0);
    });
    console.log('found source strings: ' + source_strs.length);

    var family_re = /font\-family:\s'(.*)';/i;
    var url_re = /\)(;src:\s|,)url\((.+?)\)\sformat/gi;
    var out = [];
    for (var i=0; i<source_strs.length; i++) {
        var row = source_strs[i];
        console.log('parse css row: ' + row.slice(0, 100));
        var res = family_re.exec(row);
        if (!res) {
            console.log('not parsed family');
            continue;
        }

        var font_name = res[1];
        console.log('family: ' + font_name);
        if (font_names.indexOf(font_name) < 0) {
            console.log('not selected family');
            continue;
        }

        var font_urls = [];
        var res = null;
        while ((res = url_re.exec(row)) != null) {
            font_urls.push('http://easy.myfonts.net' + res[2]);
        }
        font_urls = font_urls.filter(function(value, index, self) {
            return self.indexOf(value) === index;
        });
        console.log('urls: ' + font_urls.length + '; ' + font_urls);

        out.push({'name': font_name, 'urls': font_urls});
    }
    return out;
}

function assert(condition, message) {
    if (!condition) {
        throw message + ' FAILED' || "Assertion failed";
    }
}

function test() {
    var css_source = fs.read('tmp_source.css');
    console.log('source len: ' + css_source.length);
    var res = parse_css(css_source, ['News Gothic Light']);
    console.log('RESULT: ' + JSON.stringify(res));
    assert(res.length == 1, 'length');
    assert(res[0].name == 'News Gothic Light', 'parse font');
    assert(res[0].urls.length == 4, 'parse urls length');
    assert(res[0].urls[0] == 'http://easy.myfonts.net/v2/eot?3Ah8HC7Qb48WpMZAnR76OgCn1f0Sadad8HT&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cCo6Ly8qL3YyL2VvdD8zQWg4SEM3UWI0OFdwTVpBblI3Nk9nQ24xZjBTYWRhZDhIVCIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTQyMjY2MjQwMH19fV19&Signature=J1B3sPRXoKqpnogXSqFxy8xg0CrQBln9DWH7vcFUG-nLOE1v3waaDpsim-IG2QRiSIByeVCe~vJgvx4eXJQKDRdm68b5kA9AwlvoHLL4orIPvbANbLzbzsJAUu1SDNZYqy0IdUvX17aq7c5~KQSfrcZ-67oR63EjndnIF~KuW-qUZ9~qIatg~zFW8N-~fzEusjA8gCilmA-g2XRjSb0LFDTOijyqE04uG-ZxrDWJYTJHls7uFmjRCgQuB0a6OVjaZeK63Oks6rY4s821qOg28AFtyTdlSBNRe6MWDhP4Q~ahbh6uRsyoE3c-h07iDdkY5pTG6uMKzDzc3pIbiEYJCQ__&Key-Pair-Id=APKAJN6QFZEE4BZCL6XQ#iefix');
    assert(res[0].urls[3] == 'http://easy.myfonts.net/v2/ttf?1Vj1ldbaO4PVmcGBoB9C9IgQeuki1Wlrsbqf&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cCo6Ly8qL3YyL3R0Zj8xVmoxbGRiYU80UFZtY0dCb0I5QzlJZ1FldWtpMVdscnNicWYiLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE0MjI2NjI0MDB9fX1dfQ__&Signature=ts~QpEF2hysPhvL8lNZuhsRWDJ0qmUxMeCeoE3BWXm4ewSrEvrvzc6MGfuuKUixQSEth6jztJA1edc5hTi2sykBO0c0AFBgoTZ-Vch58hDjAR-ZvS3oU887QHsuJo78Z5KhEZmDaK~KNBD4NG2AdGSq0aLkPHieIfaCErAI~Or8hr15tygpk0bl57k2v7J9IkaJucfnIJJorldzDPZGgf64U4h0wQ5-NcQnU-Il6M0YoODzMJc7aukrz4URu2suVV3axQU9~tcUEOCtR6SMqZDlX2iiOCxYuSI5WxHmFGvb-1qN8jPVvafQG02qPV3BUJjLKGlbYOK1-JjGZfnnKaw__&Key-Pair-Id=APKAJN6QFZEE4BZCL6XQ');
    console.log('TEST ASSERTS SUCCESS');
}




