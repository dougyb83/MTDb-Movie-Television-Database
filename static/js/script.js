/* jshint esversion: 11, jquery: true */

$(document).ready(function(){
    $('.sidenav').sidenav({edge: "right"});
    if (document.getElementById("genres")) {
        let genres = document.getElementById("genres").textContent
        document.getElementById("genre-input").setAttribute("value", genres)
    }
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
