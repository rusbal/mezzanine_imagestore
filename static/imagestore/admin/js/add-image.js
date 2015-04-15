(function($){$(function(){
    var n = $('select#id_user option').size();
    if (n <= 2) {
        $('select#id_user option:last').attr('selected', 'selected');
    }

    /**
     * Hide thumb preview when adding image
     */
    $('input#id_mediafile').remove();
});})(django.jQuery);

