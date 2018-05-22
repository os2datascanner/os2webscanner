(function(os2web, $) {
  // initialize tooltips
  $("[data-toggle=\"tooltip\"]").tooltip();

  // listen to tooltip events dynamically
  $("body").on("inserted.bs.tooltip", "#available_rules li a, #selected_rules li span", function() {
    var elm = $(this);
    var tooltipElm = elm.next(".tooltip");
    var textLength = elm.attr("title").length || elm.attr("data-original-title").length;
    var boxWidth = Math.min(textLength, 30);
    tooltipElm.css({
      width: boxWidth + "ch"
    });
  });

  // adding a rule to the list of selected rules
  $("#available_rules").on("click", "li:not([data-disabled]):not(.dropdown-header)", function() {
    var $this = $(this);
    var ruleId = $this.attr("data-rule-id");
    var ruleAnchor = $this.find("a");
    $("#selected_rules").append($("<li/>", {
      "data-rule-id": ruleId,
      html: $("<a/>", {
        text: "\u00d7", // &times;
        class: "remove-rule",
        href: "#",
        "aria-label": "Fjern denne regel"
      }).add($("<span>", {
        text: ruleAnchor.text(),
        "data-toggle": "tooltip",
        "data-placement": "top",
        title: ruleAnchor.attr("title") || ruleAnchor.attr("data-original-title"),
        tabindex: 0
      }))
    }));
    $("#selected_rules [data-rule-id=\"" + ruleId + "\"] [data-toggle=\"tooltip\"]").tooltip(); // enable tooltipping on new element
    $this.attr("data-disabled", ""); // set the data-disabled attribute, so we can't add the item again.
    ruleAnchor.tooltip("destroy"); // disable tooltip

    $("form[name=\"rulesets\"]").append($("<input/>", { // add a hidden input field to the form
      type: "hidden",
      name: "rules[]",
      value: ruleId
    }));

    recalcIframeHeight();
  });

  // removing a rule from the list of selected rules
  $("#selected_rules").on("click", "li a", function() {
    var elm = $(this).closest("li"); // we want the actual parent li, not the a itself
    var ruleId = elm.attr("data-rule-id");
    var ruleLi = $("#available_rules").find("li[data-rule-id=\"" + ruleId + "\"]");
    var ruleAnchor = ruleLi.find("a");
    ruleLi.removeAttr("data-disabled");
    ruleAnchor.tooltip(); // re-enable tooltip
    elm.remove();

    $("form[name=\"rulesets\"]").find("input[value=\"" + ruleId + "\"]").remove(); // remove the hidden input field corresponding to the rule we removed

    recalcIframeHeight();
  });

  function recalcIframeHeight() { // we need to do this every time we add/remove an item from the rule list
    var thisBodyHeight = $("body").height();
    var parentIframe = $(".modal-body iframe", window.parent.document);
    parentIframe.height(thisBodyHeight);
  }
})(os2web, jQuery);
