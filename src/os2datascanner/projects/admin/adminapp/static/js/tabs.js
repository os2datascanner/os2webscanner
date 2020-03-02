// Designguide
function openTab(evt, typeName) {
  // Declare all variables
  var i, tabcontent, tablinks;

  // Get all elements with class="tabcontent" and hide them
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  // Get all elements with class="tablinks" and remove the class "active"
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }

  // Show the current tab, and add an "active" class to the button that opened the tab
  document.getElementById(typeName).style.display = "block";
  evt.currentTarget.className += " active";
}

// Menu tabs
var web = document.getElementById('web')
var file = document.getElementById('file')
var exchange = document.getElementById('exchange')

if (location.pathname === '/') {
  web.classList.add('active')
}
if (location.pathname === '/webscanners/') {
  web.classList.add('active')
}
if (location.pathname === '/filescanners/') {
  file.classList.add('active')
}
if (location.pathname === '/exchangescanners/') {
  exchange.classList.add('active')
}