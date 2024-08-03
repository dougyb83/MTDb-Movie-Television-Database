/* jshint esversion: 11, jquery: true */

$(document).ready(function () {
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
  // when submit is clicked, close log in or sign up modal. show loading spinner
  $("#sign-up-button, #log-in-button").click(function () {
    $(".log-in-modal").modal("close");
    $(".sign-up-modal").modal("close");
    $('#loading-overlay').fadeToggle(100);
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
    onCloseEnd: function () { // Callback for Modal close
      $(".message").text("");
    }
  });
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
  } else if ($("#list-sub-title").text().trim() == "Films Seenlist" || $("#list-sub-title").text().trim() == "TV Seenlist") {
    $(".seenlists").toggleClass("hide show");
  }
  $(".dropdown-trigger").dropdown();
  $('.tooltipped').tooltip();


  // search suggestions functionality
  const searchInput = document.getElementById("search");
  const suggestionsContainer = document.getElementById("suggestions");

  searchInput.addEventListener("input", () => {
    if (searchInput.value.length > 3) {
      fetch(`/search_suggestions/${searchInput.value}`)
        .then(data => {
          if (!data.ok) {
            throw Error(data.status);
          }
          return data.json();
        }).then(update => {
          let suggestions = update.results;
          displaySuggestions(suggestions);
        }).catch(e => {
          console.log(e);
        });
    } else if (searchInput.value.length < 3) {
      suggestionsContainer.classList.add('hidden');
      suggestionsContainer.innerHTML = '';
    }
  });

  function displaySuggestions(suggestions) {
    suggestionsContainer.innerHTML = '';
    if (suggestions.length > 0) {
      const suggestionsList = document.createElement("ul");
      suggestionsList.id = 'suggestions-list';
      suggestions.forEach(suggestion => {
        const suggestionItem = document.createElement("li");
        let title = suggestion.title ? suggestion.title : suggestion.name;
        let posterPath = !suggestion.poster_path ? "/static/images/no-image-placeholder.png" : `https://image.tmdb.org/t/p/w500${suggestion.poster_path}`;
        suggestionItem.innerHTML =
          `<a href="/search/${suggestion.media_type}/${suggestion.id}">
              <div class="suggestions-div">
              <img src="${posterPath}" alt="${title}">
                <span>${title}</span>
              </div>
          </a>`;
        suggestionsList.appendChild(suggestionItem);
        suggestionsContainer.classList.remove('hidden');
      });
      suggestionsContainer.appendChild(suggestionsList);
    } else {
      suggestionsContainer.innerHTML = '<p>No results found</p>';
    }
  }

  // Add a click event listener to the document
  document.addEventListener('click', function (event) {
    // Check if the click is outside the suggestions div
    if (!suggestionsContainer.contains(event.target) && event.target !== searchInput) {
      // Hide the suggestions div
      suggestionsContainer.classList.add('hidden');
    }
  });

  // Add a click event listener to the suggestions div to stop propagation
  suggestionsContainer.addEventListener('click', function (event) {
    event.stopPropagation();
  });

  // Remove the hidden class when the search input is clicked
  searchInput.addEventListener('click', function (event) {
    if (searchInput.value.length > 3) {
      suggestionsContainer.classList.remove('hidden');
      event.stopPropagation(); // Prevent the click from propagating to the document
    }
  });
});