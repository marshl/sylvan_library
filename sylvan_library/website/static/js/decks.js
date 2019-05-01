$(function () {
    console.log($('#card-input'));
    $("#card-input").autocomplete({
        source: function (request, response) {
            $.ajax({
                url: DECK_CARD_SEARCH_URL,
                data: {
                    card_name: request.term
                },
                success: function (data) {
                    console.log(data);
                    response(data.cards);
                }
            });
        },
        minLength: 2,
        select: function (event, ui) {
            console.log(ui);
            //log("Selected: " + ui.item.value + " aka " + ui.item.id);
        }
    });


    $(this).on('click', '.js-deck-board-tab-container .js-board-tab', function () {
        let $container = $(this).closest('.js-deck-board-tab-container');
        let tabType = $(this).data('tab-type');
        showTab($container, tabType);
        return false;
    });

    function showTab($tabContainer, tabType) {
        $tabContainer
            .find('.js-board-tab')
            .removeClass('selected');
        $tabContainer.find('.js-board-tab[data-tab-type="' + tabType + '"]').addClass('selected');
        let $tabContent = $tabContainer.find('.js-board-tab-content[data-tab-type="' + tabType + '"]');
        $tabContainer.find('.js-board-tab-content').not($tabContent).hide();
        $tabContent.show();
    }
});