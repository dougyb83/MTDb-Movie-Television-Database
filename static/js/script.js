/* jshint esversion: 11, jquery: true */

$(document).ready(function(){
    $('.sidenav').sidenav({edge: "right"});
    if (document.getElementById("genres")) {
        let genres = document.getElementById("genres").textContent
        document.getElementById("genre-input").setAttribute("value", genres)
    }
    $(".modal").modal();
    $(".flash-modal").modal();
    $(".flash-modal").modal("open");
  });


// modal variables
const signUpModal = document.getElementById("sign-up-modal");
const logInModal = document.getElementById("log-in-modal");
const signUpCloseButton = document.querySelector("[sign-up-close-modal]");
const logInCloseButton = document.querySelector("[log-in-close-modal]");

// closes sign up modal when button pressed
signUpCloseButton.addEventListener("click", () => {
    signUpModal.close();    
});

// closes log in modal when button pressed
logInCloseButton.addEventListener("click", () => {
    logInModal.close(); 
});

// // closes sign up modal by clicking anywhere on screen
// signUpModal.addEventListener("click", () => {
//     signUpModal.close();    
// });

// // closes log in modal by clicking anywhere on screen
// logInModal.addEventListener("click", () => {
//     logInModal.close();    
// });

// displays sign up modal
$(".sign-up-button").click(function () {    
    signUpModal.showModal();
});

// displays log in modal
$(".log-in-button").click(function () {
    logInModal.showModal();
});

// closes log in modal anddisplays sign up modal
$("#sign-up").click(function () {
    logInModal.close(); 
    signUpModal.showModal();
});

// closes sign in modal and displays log in modal
$("#log-in").click(function () {
    signUpModal.close(); 
    logInModal.showModal();
});

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
