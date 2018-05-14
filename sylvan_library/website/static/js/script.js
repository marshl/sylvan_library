$(function(){

    $('.toggle-option').on('click', function() {
       $(this).siblings('.toggle-option').removeClass('is-active');
       $(this).addClass('is-active');
       $($(this).data('input-field')).val($(this).data('input-value'));
    });

});