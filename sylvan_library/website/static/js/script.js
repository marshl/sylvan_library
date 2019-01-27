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
    });
});