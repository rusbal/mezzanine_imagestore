(function($){$(function(){
    var n = $('select#id_user option').size();
    if (n <= 2) {
        $('select#id_user option:last').attr('selected', 'selected');
    }
});})(django.jQuery);

