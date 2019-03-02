$(function () {

    $(this).on('click', '.js-colour-filter', function () {
        let $input = $(this).find('input');
        let active = !$input.prop('checked');
        $input.prop('checked', active);
        $(this).toggleClass('is-active', active);
        $(this).find('i').toggleClass('inactive', !active);
    });

    $(this).on('click', '.js-only-checkbox', function(){
       let $input = $(this).siblings('input');
       $input.prop('checked', !$input.prop('checked'));
       return false;
    });

    $(this).on('click', '.js-and-checkbox, .js-or-checkbox', function () {
        let $group = $(this).closest('.js-match-colours-group');
        let checked = $(this).hasClass('js-and-checkbox');
        $group.find('.js-match-colours').prop('checked', checked);
        $group.find(checked ? '.js-or-checkbox' : '.js-and-checkbox').removeClass('is-active');
        $group.find(checked ? '.js-and-checkbox' : '.js-or-checkbox').addClass('is-active');
        return false;
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
        if ($tabContentToShow.find('input[type!="hidden"]').length) {
            $tabContentToShow.find('input[type!="hidden"]').first().focus();
        }

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

        loadOwnershipTab(card_id);


        $.ajax('/website/ajax/search_result_add/' + printing_id)
            .done(function (result) {
                $('#card-result-tab-content-' + card_id + '-add').html(result);
            });
    }

    function loadOwnershipTab(card_id) {
        $.ajax('/website/ajax/search_result_ownership/' + card_id)
            .done(function (result) {
                $('#card-result-tab-content-' + card_id + '-ownership').html(result);
            });
    }

    function loadOwnershipSummary(card_id) {
        $.ajax('/website/ajax/ownership_summary/' + card_id)
            .done(function (result) {
                $('#card-result-' + card_id).find('.js-ownership-summary').html(result);
            });
    }

    function loadSetSummary(card_id, printing_id) {
        $.ajax({
            url: '/website/ajax/search_result_set_summary/' + printing_id
        })
            .done(function (result) {
                let $summary = $('#card-result-' + card_id).find('.js-card-result-set-summary');
                let previousScroll = $summary.find('p').get(0).scrollTop;
                $summary.html(result);
                $summary.find('p').get(0).scrollTop = previousScroll;
            });
    }

    $(this).on('click', '.js-page-button', function () {
        if ($(this).hasClass('is-disabled')) {
            return;
        }
        document.location.href = '?' + $(this).data('page-url');
    });

    /**
     * When a user changes the content of a filter field, it should show the "X" remove icon next to it
     */
    $(this).on('change keyup keydown', '.js-filter-field', function () {
        $(this).closest('.js-filter').find('.js-remove-filter').toggleClass(
            'is-hidden',
            $(this).val().length === 0
        );
    });

    /**
     * When a user clicks on the "X" next to a input field, it should clear that field then hide itself
     */
    $(this).on('click', '.js-remove-filter', function () {
        $(this).closest('.js-filter').find('.js-filter-field').val('').change();
    });

    $(this).on('click', '.js-filter-heading', function () {
        let collapsed = !$(this).data('collapsed');
        let $filterField = $(this).closest('.js-collapsible-filter-field');
        $filterField.find('.js-filter-container').toggleClass('is-collapsed', collapsed);
        $filterField.find('input').prop('disabled', collapsed);
        $(this).data('collapsed', collapsed);

        // Focus on any text field in the filter
        if (!collapsed) {
            $filterField.find('input[type="text"]').focus();
        }
    });

    $(this).on('submit', '.js-change-card-ownership-form', function (event) {
        let $form = $(this);
        if ($form.data('disabled')) {
            return;
        }
        let $result = $(this).closest('.js-card-result');
        let card_id = Number($result.data('card-id'));
        let printing_id = Number($result.data('card-printing-id'));
        let count = $form.find('input[name="count"]').val();
        if (Number(count) === 0) {
            return;
        }

        $.ajax({
            url: $(this).attr('action'),
            data: $(this).serialize(),
            type: 'POST'
        }).done(function (result) {
            loadOwnershipTab(card_id);
            loadOwnershipSummary(card_id);
            loadSetSummary(card_id, printing_id);
            $form.find('input').prop('disabled', false);
            $form.data('disabled', false);
            $form.find('input[name="count"]').val('');
        });

        $form.data('disabled', true);
        $form.find('input').prop('disabled', true);

        event.preventDefault();
        return false;
    });

    $('.js-slider-filter').each(function () {
        let $slider = $(this);
        let $filter = $slider.closest('.js-filter');
        let values = [
            $filter.find('.js-min-field').val(),
            $filter.find('.js-max-field').val()
        ];
        if (values[1] === '') {
            values[1] = $slider.data('max-value');
        }
        $slider.slider({
            range: true,
            min: $slider.data('min-value'),
            max: $slider.data('max-value'),
            values: values,
            slide: function (event, ui) {
                let min = ui.values[0];
                let max = ui.values[1];
                $filter.find('.js-lower-mark').text(min);
                $filter.find('.js-upper-mark').text(max);
                $filter.find('.js-min-field').val(min);
                $filter.find('.js-max-field').val(max);
            }
        });
    });

    $(this).on('click', '.js-search-btn', function () {
        $(this).closest('form').submit();
    });
});
