$(function () {

    $(this).on('click', '.js-card-result-tab-container .js-card-result-tab', function () {
        let $container = $(this).closest('.js-card-result-tab-container');
        let tabType = $(this).data('tab-type');
        showTab($container, tabType);
        return false;
    });

    function showTab($tabContainer, tabType) {
        $tabContainer
            .find('.js-card-result-tab')
            .removeClass('selected');
        $tabContainer.find('.js-card-result-tab[data-tab-type="' + tabType + '"]').addClass('selected');
        let $tabContent = $tabContainer.find('.js-card-result-tab-content[data-tab-type="' + tabType + '"]');
        $tabContainer.find('.js-card-result-tab-content').not($tabContent).hide();
        $tabContent.show();
        if (tabType === 'add') {
            $tabContent.find('input[type!="hidden"]').first().focus();
        }

        Cookies.set('selected_tab', tabType);
    }

    if ($('.js-card-result').length === 1) {
        expandCardResult($('.js-card-result'));
    }

    $(this).on('click', '.js-card-result', function () {
        expandCardResult($(this))
    });

    function expandCardResult($cardResult) {
        if ($cardResult.hasClass('expanded')) {
            return;
        }

        $('.js-card-result').removeClass("expanded");
        $cardResult.addClass("expanded");

        $('.js-card-result-expander').show();
        $cardResult.find('.js-card-result-expander').hide();

        let $image = $cardResult.find('.js-card-result-image');
        $('.js-card-result-image').removeClass('clicked');
        $image.addClass('clicked');
        $('.js-card-result-tab-container').slideUp();
        $cardResult.find('.js-card-result-tab-container').slideDown();

        let printing_id = $cardResult.data('card-printing-id');
        let card_id = $cardResult.data('card-id');

        let selectedTab = Cookies.get('selected_tab') || 'details';
        let $tabContainer = $cardResult.find('.js-card-result-tab-container');
        showTab($tabContainer, selectedTab);

        loadTabDataForPrinting($tabContainer, card_id, printing_id);
    }

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
        let $tabContainer = $result.find('.js-card-result-tab-container');

        loadTabDataForPrinting($tabContainer, $result.data('card-id'), printing_id);
        return false;
    });

    function loadTabDataForPrinting($tabContainer, card_id, printing_id) {

        $.ajax('/website/ajax/search_result_details/' + printing_id)
            .done(function (result) {
                $tabContainer.find('.js-card-result-tab-content[data-tab-type="details"]').html(result);
            });

        $.ajax('/website/ajax/search_result_rulings/' + card_id)
            .done(function (result) {
                $tabContainer.find('.js-card-result-tab-content[data-tab-type="rulings"]').html(result);
            });

        $.ajax('/website/ajax/search_result_languages/' + printing_id)
            .done(function (result) {
                $tabContainer.find('.js-card-result-tab-content[data-tab-type="languages"]').html(result);
            });

        if (IS_LOGGED_IN) {
            loadOwnershipTab($tabContainer, card_id);
            $.ajax('/website/ajax/search_result_add/' + printing_id)
                .done(function (result) {
                    let $tab = $tabContainer.find('.js-card-result-tab-content[data-tab-type="add"]');
                    $tab.html(result);
                    if (!$tab.isHidden) {
                        $tab.find('input[type!="hidden"]').first().focus();
                    }
                });


            $.ajax('/website/ajax/search_result_decks/' + card_id)
                .done(function (result) {
                    $tabContainer.find('.js-card-result-tab-content[data-tab-type="decks"]').html(result);
                });
        }

        $.ajax('/website/ajax/search_result_links/' + card_id)
            .done(function (result) {
                $tabContainer.find('.js-card-result-tab-content[data-tab-type="links"]').html(result);
            });


        $.ajax('/website/ajax/search_result_prices/' + printing_id)
            .done(function (result) {
                $tabContainer.find('.js-card-result-tab-content[data-tab-type="prices"]').html(result);
            });
    }

    function loadOwnershipTab($tabContainer, card_id) {
        $.ajax('/website/ajax/search_result_ownership/' + card_id)
            .done(function (result) {
                $tabContainer.find('.js-card-result-tab-content[data-tab-type="ownership"]').html(result);
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
        event.preventDefault();
        let $form = $(this);
        if ($form.data('disabled')) {
            return false;
        }
        let $result = $(this).closest('.js-card-result');
        let card_id = Number($result.data('card-id'));
        let printing_id = Number($result.data('card-printing-id'));
        let count = $form.find('input[name="count"]').val();
        if (Number(count) === 0) {
            return false;
        }

        let $tabContainer = $(this).closest('.js-card-result').find('.js-card-result-tab-container');

        $.ajax({
            url: $(this).attr('action'),
            data: $(this).serialize(),
            type: 'POST'
        }).done(function (result) {
            loadOwnershipTab($tabContainer, card_id);
            loadOwnershipSummary(card_id);
            loadSetSummary(card_id, printing_id);
            $form.find('input').prop('disabled', false);
            $form.data('disabled', false);
            $form.find('input[name="count"]').val('');
        });

        $form.data('disabled', true);
        $form.find('input').prop('disabled', true);

        return false;
    });

    $(this).on('click', '.js-image-split-btn', function () {
        $(this)
            .closest('.js-card-result')
            .find('.js-card-result-image')
            .toggleClass('rotated');
    });

    $(this).on('click', '.js-image-flip-btn', function () {
        $(this)
            .closest('.js-card-result')
            .find('.js-card-result-image')
            .toggleClass('rotated');
    });


    $(this).on('click', '.js-image-transform-btn', function () {
        $(this)
            .closest('.js-card-result')
            .find('.js-card-result-image-container')
            .toggleClass('flipped');
    });

    $(this).keydown(function (event) {
        if (event.ctrlKey && (event.key === "ArrowLeft" || event.key === "ArrowRight")) {
            const $expandedResult = $(".js-card-result.expanded");
            const $selectedSet = $expandedResult.find(".js-card-result-set-symbol.clicked");
            const selectedIndex = $selectedSet.data("index");
            let targetIndex;
            if (event.key === "ArrowLeft") {
                targetIndex = selectedIndex - 1;
            } else {
                targetIndex = selectedIndex + 1;
            }
            let target = `.js-card-result-set-symbol[data-index="${targetIndex}"]`;
            console.log(target);
            const $newTarget = $expandedResult.find(target);
            if ($newTarget) {
                $newTarget.trigger("click");
            }
            event.preventDefault();
        }
    });
});
