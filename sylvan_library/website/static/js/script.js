$(function () {

    $('.js-toggle-option').on('click', function () {
        $(this).siblings('.js-toggle-option').removeClass('is-active');
        $(this).addClass('is-active');
        $($(this).data('input-field')).val($(this).data('input-value'));
    });

    $('.js-colour-filter input').on('change', function () {
        if (this.checked) {
            $(this).closest('.js-colour-filter').addClass('is-active');
        } else {
            $(this).closest('.js-colour-filter').removeClass('is-active');
        }
    });

    $(this).on('click', '.js-card-result-tab-container .js-card-result-tab', function () {
        let $container = $(this).closest('.js-card-result-tab-container');
        $container
            .find('.js-card-result-tab')
            .removeClass('ReactTabs__Tab--selected')
            .addClass('ReactTabs__Tab')
            .attr('aria-selected', false)
            .attr('aria-expanded', false);
        $(this).addClass('ReactTabs__Tab--selected');
        $(this).removeClass('ReactTabs__Tab');
        $(this).attr('aria-selected', true);
        $(this).attr('aria-expanded', true);

        let $tabContentToShow = $($(this).data('target-tab'));
        $container.find('.js-card-result-tab-content').not($tabContentToShow).hide();
        $tabContentToShow.show();

        return false;
    });

    $(this).on('click', '.js-card-result', function () {
        if ($(this).data('is-expanded')) {
            return;
        }

        $('.js-card-result').data('is-expanded', false);
        $(this).data('is-expanded', true);

        $('.js-card-result-expander').show();
        $(this).find('.js-card-result-expander').hide();

        let $image = $(this).find('.js-card-result-image');
        $('.js-card-result-image').removeClass('clicked');
        $image.addClass('clicked');
        $('.js-card-result-tab-container').slideUp();
        $(this).find('.js-card-result-tab-container').slideDown();

        let printing_id = $(this).data('card-printing-id');
        let card_id = $(this).data('card-id');

        loadTabDataForPrinting(card_id, printing_id);
    });

    $(this).on('click', '.js-card-result-set-symbol', function () {
        let $result = $(this).closest('.js-card-result');
        let printing_id = Number($(this).data('card-printing-id'));

        if (Number($result.data('card-printing-id')) === printing_id) {
            return false;
        }

        $result.data('card-printing-id', printing_id);
        $result.find('.js-card-result-set-symbol').removeClass('clicked');
        $(this).addClass('clicked');

        $result.find('.js-card-result-image').attr('src', $(this).data('image-url'));

        loadTabDataForPrinting($result.data('card-id'), printing_id);
        return false;
    });

    function loadTabDataForPrinting(card_id, printing_id) {
        $.ajax('/website/ajax/search_result_details/' + printing_id)
            .done(function (result) {
                $('#card-result-tab-content-' + card_id + '-details').html(result);
            });

        $.ajax('/website/ajax/search_result_rulings/' + card_id)
            .done(function (result) {
                $('#card-result-tab-content-' + card_id + '-rulings').html(result);
            });

        $.ajax('/website/ajax/search_result_languages/' + printing_id)
            .done(function (result) {
                $('#card-result-tab-content-' + card_id + '-languages').html(result);
            });

        $.ajax('/website/ajax/search_result_ownership/' + card_id)
            .done(function (result) {
                $('#card-result-tab-content-' + card_id + '-ownership').html(result);
            });
    }

    $(this).on('click', '.js-page-button', function () {
        if ($(this).hasClass('is-disabled')) {
            return;
        }
        document.location.href = '?' + $(this).data('page-url');
    });
});