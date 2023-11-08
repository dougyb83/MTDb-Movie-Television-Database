/* jshint esversion: 11, jquery: true */

$(document).ready(function(){
  // modal initialisation
  $('.modal').modal();
  // initialise and set position for side navs
  $('#nav-menu').sidenav({edge: "right"});
  $('#slide-out').sidenav({edge: "left",}, 'draggable', true);
  // open log-in modal when navbar log in clicked
  $(".nav-log-in, .log-in-button").click(function () {    
      $(".log-in-modal").modal("open");
  });
  // if signup modal 'already registered' is clicked, close sign up & open sign in modal
  $("#log-in").click(function () {
      $(".sign-up-modal").modal("close");
      $(".log-in-modal").modal("open");
  });
  // open sign-up modal when navbar sign up clicked
  $(".nav-sign-up, .sign-up-button").click(function () {    
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
    $(".message").text("You must be logged in to perfom that action");
    $(".log-in-modal").modal("open");
  });
  // if the above message is displayed on the login modal and the user doesn't log in - clear the message
  $('.log-in-modal').modal({
    onCloseEnd: function() { // Callback for Modal close
      $(".message").text("");
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
  // hide the sublists and show them when clicked
  $("#watchlists>a").click(function () {
    $(".watchlists").toggleClass("hide show");
  });
  // hide the sublists and show them when clicked
  $("#seenlists>a").click(function () {
    $(".seenlists").toggleClass("hide show");
  });
  // Keep sublists visible when viewing relevant data on list.html
  if ($("#list-sub-title").text().trim() == "Films Watchlist" || $("#list-sub-title").text().trim() == "TV Watchlist") {
    $(".watchlists").toggleClass("hide show");
  }
  else if ($("#list-sub-title").text().trim() == "Films Seenlist" || $("#list-sub-title").text().trim() == "TV Seenlist") {
      $(".seenlists").toggleClass("hide show");
    }
  $(".dropdown-trigger").dropdown();
  $('.tooltipped').tooltip();
});