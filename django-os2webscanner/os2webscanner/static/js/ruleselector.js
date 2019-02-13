(function(os2web, $) {
  // initialize tooltips
  $("[data-toggle=\"tooltip\"]").tooltip();

  // listen to tooltip events dynamically in order to calculate proper tooltip size
  $("body").on("inserted.bs.tooltip", "#available_rules li a, #selected_rules > .selected_rule span", function() {
    var elm = $(this);
    var tooltipElm = elm.next(".tooltip");
    var textLength = elm.attr("title").length || elm.attr("data-original-title").length;
    var boxWidth = Math.min(textLength, 30); // whatever is smallest of text length and 30 characters
    tooltipElm.css({
      width: "calc(" + boxWidth + "ch + 5px)"
    });
  });

  // adding a rule to the list of selected rules
  $("#available_rules").on("click", "> li[data-rule-id]:not([data-disabled])", function() {
    var $this = $(this);
    var ruleId = $this.attr("data-rule-id");
    var ruleAnchor = $this.find("a");
    $("#rules_list").before($("<div/>", {
      class: "selected_rule",
      "data-rule-id": ruleId,
      html: $("<a/>", {
        text: "",
        class: "remove-rule",
        href: "#",
        "aria-label": "Fjern denne regel"
      }).add($("<span/>", {
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

    $this.closest("form").append($("<input/>", { // add a hidden input field to the form
      type: "hidden",
      name: "regex_rules",
      value: ruleId
    }));

    recalcIframeHeight();
  });


  if ( $("#edit-scanner-modal-title").length ){
    // removing a rule from the list of selected rules
    $("#selected_rules").on("click", ".remove-rule", function() {
      var elm = $(this).closest("div"); // we want the actual parent div, not the a itself
      var ruleId = elm.attr("data-rule-id");
      var ruleLi = $("#available_rules").find("li[data-rule-id=\"" + ruleId + "\"]");
      var ruleAnchor = ruleLi.find("a");
      ruleLi.removeAttr("data-disabled");
      ruleAnchor.tooltip(); // re-enable tooltip

      $(this).closest("form").find("input[type=\"hidden\"][name=\"regex_rules\"][value=\"" + ruleId + "\"]").remove(); // remove the hidden input field corresponding to the rule we removed
      elm.remove();

      recalcIframeHeight();
    });
  }

  // // adding a system rule
  // $("#available_rules").on("click", "[data-systemrule-target]:not([data-disabled])", function() {
  //   var $this = $(this);
  //   var targ = $("#id_" + $this.attr("data-systemrule-target"));
  //   targ.prop("checked", true).trigger("change"); // we need to manually trigger change event, as it doesn't happen automatically when programmatically setting the checked prop
  // });
  //
  // // toggling a .checkbox-group input[type="checkbox"]:first-of-type should also toggle the visibility of the parent .checkbox-group
  // $("#selected_rules .checkbox-group input[type=\"checkbox\"]:first-of-type").change(function() {
  //   toggleCheckboxGroup($(this));
  //   recalcIframeHeight();
  // });

  // filter the list of rules when search field changes value
  $("#rule-filter").on("textInput input", os2debounce(function() {
    var value = $(this).val().trim();
    if(value.length < 3) {
      $("#available_rules li").show(); // reset all li to shown
      return; // return early!
    }
    var needle = new RegExp(value, "gi");
    $("#available_rules .rule").each(function() {
      var haystack = $(this);
      if(!haystack.text().match(needle)) {
        haystack.hide();
      } else {
        haystack.show();
      }
    });
    // we also need to hide headings and separators if an entire section becomes invisible.
    $("#available_rules .dropdown-header").each(function() {
      var header = $(this);
      var nextRules = header.nextUntil(".dropdown-header", ".rule"); // check to see if we're in a section of the list that actually contains rules (i.e. not filter box at the top)
      if(nextRules.length > 0) {
        var isEmpty = true;
        nextRules.each(function() {
          if($(this).is(":visible")) {
            isEmpty = false;
            return;
          }
        });
        if(isEmpty) {
          header.hide();
        } else {
          header.show();
        }
      }
    });
  }, 150));

  // set height of dropdown list in order to prevent it from breaking out of window
  $("#rules_list").on("show.bs.dropdown", function() {
    var top = $(this).offset().top;
    var docHeight = $("body").height();
    var maxHeight = top - 15;
    $("#available_rules").css("max-height", maxHeight + "px");
  });

  // function toggleCheckboxGroup(checkbox) {
  //   var state = checkbox.prop("checked");
  //   var checkboxGroup = checkbox.parent(".checkbox-group");
  //   var ruleLi = $("[data-systemrule-target=\"" + checkbox.attr("id").replace("id_", "") + "\"]");
  //   if(state) {
  //     checkboxGroup.show();
  //     ruleLi.attr("data-disabled", "");
  //   } else {
  //     checkboxGroup.hide();
  //     ruleLi.removeAttr("data-disabled");
  //   }
  //   handleSubChoices(checkbox);
  // }

    $( document ).ready(function() {
        // Handler for .ready() called.
        if($("#is_edit_view")){
            $("#selected_rules .remove-rule").addClass('disabled')
            /*$("#selected_rules span").css('color', '#aaa')*/
            $("#selected_rules span").addClass('disabled')
        }
    });

})(os2web, jQuery);
