/* jshint esversion: 11, jquery: true */

$(document).ready(function(){
    $('.sidenav').sidenav({edge: "right"});
    if (document.getElementById("genres")) {
        let genres = document.getElementById("genres").textContent
        let genreElement = document.getElementsByClassName("genre-input")
        for (let element of genreElement) {
          element.setAttribute("value", genres)
        }
    } 
    $('.log-in-modal').modal({
      onCloseEnd: function() { // Callback for Modal close
        $(".message").text("") 
        } 
      }
    );
  });

  $(".log-in-modal").modal();
  $(".log-in-button").click(function () {    
      $(".log-in-modal").modal("open");
  });
  $("#log-in").click(function () {
      $(".sign-up-modal").modal("close");
      $(".log-in-modal").modal("open");
  });
  $(".sign-up-modal").modal();
  $(".sign-up-button").click(function () {    
      $(".sign-up-modal").modal("open");
  });
  $("#sign-up").click(function () {
      $(".log-in-modal").modal("close");
      $(".sign-up-modal").modal("open");        
  });
  $(".flash-modal").modal();
  $(".flash-modal").modal("open");

  $(".non-session-activity").click(function () {
    $(".message").text("You must be logged in to perfom that action")
    $(".log-in-modal").modal("open");
  });




  // if (document.getElementById('star1').checked) {

  // } else if (document.getElementById('star2').checked) {

  // } else if (document.getElementById('star3').checked) {

  // } else if (document.getElementById('star4').checked) {

  // } else {

  // }


// function autocomplete() {
//     // gets the partial search string to send to api
//     let searchString = document.getElementById("search").value;
//     // only search if string is longer than 2 chars
//     if (searchString.length >= 3) {
//         // send searchString to backend
//         fetch("/autocomplete")
//         console.log(searchString);
//     }
// }
