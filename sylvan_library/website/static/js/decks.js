$(function () {
    $("#card-input").autocomplete({
        source: function (request, response) {
            $.ajax({
                url: DECK_CARD_SEARCH_URL,
                data: {
                    card_name: request.term
                },
                success: function (data) {
                    response(data.cards);
                }
            });
        },
        minLength: 2,
    });


    $(this).on('click', '.js-deck-board-tab-container .js-board-tab', function () {
        let $tabContainer = $(this).closest('.js-deck-board-tab-container');
        let tabType = $(this).data('tab-type');
        $tabContainer.data('selected-tab', tabType);
        $tabContainer
            .find('.js-board-tab')
            .removeClass('selected');
        $tabContainer.find('.js-board-tab[data-tab-type="' + tabType + '"]').addClass('selected');
        let $tabContent = $tabContainer.find('.js-board-tab-content[data-tab-type="' + tabType + '"]');
        $tabContainer.find('.js-board-tab-content').not($tabContent).hide();
        $tabContent.show();
        return false;
    });

    $(this).on('click', '.js-add-card-to-board-btn', function() {
        let $tabContainer = $('.js-deck-board-tab-container');
        let tabType = $tabContainer.data('selected-tab');
        let $tab = $tabContainer.find('.js-board-tab-content[data-tab-type="' + tabType + '"]');
        let $name_input = $('#card-input');
        if(!$name_input.val()){
            return false;
        }

        let $quantity_input = $('#id_quantity');
        let quantity= $quantity_input.val();
        if (!quantity) {
            quantity = 1;
        }

        let card_as_text = String(quantity) + 'x ' + $name_input.val();
        console.log(card_as_text);

        let $textArea = $tab.find('textarea');
        if($textArea.text()) {
            $textArea.text($textArea.text() + '\n' + card_as_text);
        } else {
            $textArea.text(card_as_text);
        }
        $name_input.val('');
        $name_input.focus();

        return false;
    });
});