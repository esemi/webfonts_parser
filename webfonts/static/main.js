Zepto(function($){
    $(document).on('ajaxBeforeSend', function(e, xhr, options) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(options.type)) {
            xhr.setRequestHeader("X-CSRFToken", $('#csrf-token').val());
        }
    });

    $('.js-order').on('submit', function(e){
        $.post('/parse/', { url: $('.js-order-field').val(), cache: false }, function(response){
            console.log(response.result);
        });
        return false;
    });
});