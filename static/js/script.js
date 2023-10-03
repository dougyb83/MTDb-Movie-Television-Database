/* jshint esversion: 11, jquery: true */

$(document).ready(function(){
  // modal initialisation
  $('.modal').modal();
  // initialise and set position for side navs
  $('#nav-menu').sidenav({edge: "right"});
  $('#slide-out').sidenav({edge: "left"});
  // open log-in modal when navbar log in clicked
  $(".log-in-button").click(function () {    
      $(".log-in-modal").modal("open");
  });
  // if signup modal 'already registered' is clicked, close sign up & open sign in modal
  $("#log-in").click(function () {
      $(".sign-up-modal").modal("close");
      $(".log-in-modal").modal("open");
  });
  // open sign-up modal when navbar sign up clicked
  $(".sign-up-button").click(function () {    
      $(".sign-up-modal").modal("open");
  });
  // if login modal 'register account' is clicked, close open sign & open sign up in modal
  $("#sign-up").click(function () {
      $(".log-in-modal").modal("close");
      $(".sign-up-modal").modal("open");        
  });
  // if a flash message exists, open a modal
  $(".flash-modal").modal("open");
  // if a non registered user performs a register user action display a warning and prompt login
  $(".non-session-activity").click(function () {
    $(".message").text("You must be logged in to perfom that action")
    $(".log-in-modal").modal("open");
  });
  // if the above message is displayed on the login modal and the user doesn't log in - clear the message
  $('.log-in-modal').modal({
    onCloseEnd: function() { // Callback for Modal close
      $(".message").text("") 
      } 
    }
  );
  // when the edit review button is clicked, make the text editable
  $("#edit-review-btn").click(function () {
    let reviewText = $("#review").text();
    $("#edit-review").html(`
      <div class="input-field">
        <label for="review" class="active">Your Review!</label>
        <textarea id="review" name="review" class="review materialize-textarea" maxlength="290">${reviewText}</textarea>                                
        <button class="btn waves-effect waves-light right" title="Add Review" type="submit">
            Submit Review
        </button>
      </div>
    `);
  });
  // if the current page contains an id of 'rating' and the rating variable has a value then check the radio button
  if (document.getElementById("rating") && rating) {
    document.getElementById("star" + rating.toString()).setAttribute("checked", "checked");
  }
});
// hide the sublists and show them when clicked
$(".watchlists").addClass("hide");
$("#watchlists>a").click(function () {
  $(".watchlists").toggleClass("hide")
  $(".watchlists").toggleClass("show")
});
// hide the sublists and show them when clicked
$(".seenlists").addClass("hide");
$("#seenlists>a").click(function () {
  $(".seenlists").toggleClass("hide")
  $(".seenlists").toggleClass("show")
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
