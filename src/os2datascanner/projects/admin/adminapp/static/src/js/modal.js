// Get the modal
var modal = document.getElementById("myModal");

// Get the button that opens the modal
var btn = document.getElementById("show-modal");

// Get the <span> element that closes the modal
var ds_modal_close = document.getElementsByClassName("button--modal-close")[0];

// Get backdrop
var ds_modal_backdrop = document.getElementsByClassName("ds-modal__wrapper")[0];

// When the user clicks the button, open the modal 
btn.onclick = function () {
  modal.style.visibility = "visible";
  modal.classList.add("ds-modal--open");
}

// When the user clicks on <botton> (x), close the modal
ds_modal_close.onclick = function () {
  modal.style.visibility = "hidden";
  modal.classList.remove("ds-modal--open");
}

// When the user clicks anywhere outside of the modal, close it
ds_modal_backdrop.onclick = function (event) {
  modal.style.visibility = "hidden";
  modal.classList.remove("ds-modal--open");
}
