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
        if ($(this).data('selected')) {
            return;
        }

        $('.js-card-result').data('selected', false);
        $(this).data('selected', true);

        $('.js-card-result-expander').show();
        $(this).find('.js-card-result-expander').hide();

        let $image = $(this).find('.js-card-result-image');
        $('.js-card-result-image').removeClass('clicked');
        $image.addClass('clicked');
        $('.js-card-result-tab-container').slideUp();
        $(this).find('.js-card-result-tab-container').slideDown();

        let printing_id = $(this).data('card-printing-id');
        let card_id = $(this).data('card-id');

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
    });
});