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
        console.log($profileContainer.data('expanded'));
        if (!$profileContainer.data('expanded')) {
            return;
        }

        if (!$(event.target).closest('.js-profile-container').length && !$(event.target).closest('.top-bar').length) {
            toggleProfileContainer();
            return false;
        }
    });
});
