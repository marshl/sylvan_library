$(function () {

    $(this).on('click', '.js-page-button', function () {
        if ($(this).hasClass('is-disabled')) {
            return;
        }
        document.location.href = '?' + $(this).data('page-url');
    });

    $(this).on('focus', '.js-search-bar-input', function() {
        $(this).select();
    });
});
