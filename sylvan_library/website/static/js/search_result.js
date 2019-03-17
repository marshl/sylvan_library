$(function () {

    $(this).on('click', '.js-card-result-tab-container .js-card-result-tab', function () {
        let $container = $(this).closest('.js-card-result-tab-container');
        $container
            .find('.js-card-result-tab')
            .removeClass('selected')
            .attr('aria-expanded', false);
        $(this).addClass('selected');
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

    $(this).on('click', '.js-image-split-btn', function() {
        $(this)
            .closest('.js-card-result')
            .find('.js-card-result-image')
            .toggleClass('split');
    });

    $(this).on('click', '.js-image-flip-btn', function() {
        $(this)
            .closest('.js-card-result')
            .find('.js-card-result-image')
            .toggleClass('flip');
    });
});
