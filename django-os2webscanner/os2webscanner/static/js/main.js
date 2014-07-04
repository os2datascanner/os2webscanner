os2web = window.os2web || {};
(function(os2web, $) {
    // Enable iframe-based modal dialogs
    $('.modal.iframe').on('shown.bs.modal', function() {
      var $this = $(this), src = $this.attr("data-href");
      if(src)
        $this.find('iframe').first().attr("src", src);
    });

    // Validation radio buttons in the domain dialog
    $('input.validateradio').on("click", function() {
        var $this = $(this),
            id = '#validation_method_desc_' + $this.attr('value');
        $this.attr('data-target', id);
        $this.tab('show');
    });

    $.extend(os2web, {
        iframeDialog: function(id_or_elem, url, title) {
            $elem = $(id_or_elem);
            $elem.find('iframe').first().attr('src', 'about:blank');
            $elem.attr('data-href', url);
            if(title) {
                label_id = $elem.attr('aria-labelledby');
                if(label_id) {
                    $('#' + label_id).html(title);
                }
            }
            $elem.modal({show: true});
        }
    });
})(os2web, jQuery);
