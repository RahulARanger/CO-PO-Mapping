window.onload = function() {
    window.addEventListener("beforeunload", function (e) {
        const confirmationMessage = 'Leaving this page, will remove all the data that was given. Please consider once';
        (e || window.event).returnValue = confirmationMessage; //Gecko + IE
        return confirmationMessage; //Gecko + Webkit, Safari, Chrome etc.
    });
};
