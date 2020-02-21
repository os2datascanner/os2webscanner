import '../css/master.scss';

$(document).ready(function(){
  $("a[data-modal='modal:open']").click(function(e){
      e.preventDefault()

      // Find the target element (same as our href)
      var target = $(this).attr("href")

      // Find the src to set
      var src = $(this).attr("data-src")

      // Find the iframe in our target and set its src
      $(target).find("iframe").attr("src",src);
  });

  // Toggle visiblity of expandable rows, start
  $(document).on("click", "[data-toggle]", function() {
    var expandTarget = $(this).attr("data-toggle");

    if ($(expandTarget).is('[hidden]')) {
      $(expandTarget).removeAttr('hidden');
    } else {
      $(expandTarget).attr('hidden','');
    }
  });
  // Toggle visiblity of expandable rows, stop
})
