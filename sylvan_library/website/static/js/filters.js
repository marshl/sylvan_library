$(function () {

    $(this).on('click', '.js-colour-filter', function () {
        let $input = $(this).find('input');
        let active = !$input.prop('checked');
        $input.prop('checked', active);
        $(this).toggleClass('is-active', active);
        $(this).find('i').toggleClass('inactive', !active);
    });


    $(this).on('click', '.js-rarity-filter', function () {
        let $input = $(this).siblings('input');
        let active = !$input.prop('checked');
        $input.prop('checked', active);
        $(this).toggleClass('clicked', active);
    });

    $(this).on('click', '.js-only-checkbox', function () {
        let $input = $(this).siblings('input');
        $input.prop('checked', !$input.prop('checked'));
        return false;
    });

    $(this).on('click', '.js-and-checkbox, .js-or-checkbox', function () {
        let $group = $(this).closest('.js-match-group');
        let checked = $(this).hasClass('js-and-checkbox');
        $group.find('.js-match-input').prop('checked', checked);
        $group.find(checked ? '.js-or-checkbox' : '.js-and-checkbox').removeClass('is-active');
        $group.find(checked ? '.js-and-checkbox' : '.js-or-checkbox').addClass('is-active');
        return false;
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

    $('.js-filter-heading').each(function () {
        if ($(this).data('collapsed')) {
            $(this).closest('.js-collapsible-filter-field').find('input').prop('disabled', true);
        }
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
