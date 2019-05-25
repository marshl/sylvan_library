$(function () {

    $(this).on('click', '.js-page-button', function () {
        if ($(this).hasClass('is-disabled')) {
            return;
        }
        document.location.href = '?' + $(this).data('page-url');
    });

    $(this).on('focus', '.js-search-bar-input', function () {
        $(this).select();
    });

    $(this).on('click', '.js-profile-button', function () {
        toggleProfileContainer();
        return false;
    });

    function toggleProfileContainer() {
        let $profileContainer = $('.js-profile-container');
        let isExpanded = !$profileContainer.data('expanded');
        $profileContainer.data('expanded', isExpanded);
        $profileContainer.toggle(isExpanded);
    }

    $(this).on('click', 'body', function (event) {
        let $profileContainer = $('.js-profile-container');
        if (!$profileContainer.data('expanded')) {
            return;
        }

        if (!$(event.target).closest('.js-profile-container').length && !$(event.target).closest('.top-bar').length) {
            toggleProfileContainer();
            return false;
        }
    });

    $(this).on('mouseenter', '.js-card-link', function (event) {
        let imagePath = $(this).data('image-path');
        let cardName = $(this).data('card-name');
        let popupContainer = $('.js-image-popup-container');
        if (!popupContainer.length) {
            popupContainer = $('<div class="js-image-popup-container image-popup-container"><img src="" alt=""/></div>');
            popupContainer.appendTo($('body'));
        }

        popupContainer.find('img').attr('src', imagePath).attr('alt', cardName);
        popupContainer.stop().fadeIn(250);
        let bodyRect = document.body.getBoundingClientRect();
        let elemRect = $(this).get(0).getBoundingClientRect();
        let offset = 20;
        let left = elemRect.left - bodyRect.left + offset + $(this).width();
        if (left + popupContainer.width() > $(document).width()) {
            left = elemRect.left - bodyRect.left - offset - popupContainer.width();
        }

        popupContainer.css({
            top: (elemRect.top - bodyRect.top + $(this).height() - popupContainer.height() / 2) + "px",
            left: (left) + "px"
        })
    });

    $(this).on('mouseleave', '.js-card-link', function () {
        $('.js-image-popup-container').stop().fadeOut(150);
    });
});
