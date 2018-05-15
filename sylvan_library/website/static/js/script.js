$(function(){

    $('.js-toggle-option').on('click', function() {
       $(this).siblings('.js-toggle-option').removeClass('is-active');
       $(this).addClass('is-active');
       $($(this).data('input-field')).val($(this).data('input-value'));
    });

    $('.js-colour-filter input').on('change', function() {
        if(this.checked) {
            $(this).closest('.js-colour-filter').addClass('is-active');
        } else {
            $(this).closest('.js-colour-filter').removeClass('is-active');
        }
    });

});