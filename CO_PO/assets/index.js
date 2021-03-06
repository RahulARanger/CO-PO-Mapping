window.onload = function() {
    window.addEventListener("beforeunload", function (e) {
        const confirmationMessage = 'Leaving this page, will remove all the data that was given. Please consider once';
        (e || window.event).returnValue = confirmationMessage; //Gecko + IE
        return confirmationMessage; //Gecko + Webkit, Safari, Chrome etc.
    });
};



function decide_modal(n_clicks, opened){
    console.log(n_clicks, opened)
    if(n_clicks === undefined){
        return false;
    }
    return !Boolean(opened);
}

function get_latest_info(current_version){
    
}



window.dash_clientside = Object.assign({}, window.dash_clientside, {
    modal:{
        decide_modal
    },
    tips: {
        handle_tips: (opened) => new Array(4).fill(opened)
    }
});


console.log(window.dash_clientside)