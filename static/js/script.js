/* jshint esversion: 11, jquery: true */

$(document).ready(function(){
    $('.sidenav').sidenav({edge: "right"});
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
