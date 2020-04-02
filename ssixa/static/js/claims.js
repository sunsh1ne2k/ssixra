function verifyClaim(claim_name) {
    var url = "/claims/verifyclaim";

    var claim_value = $('#' + claim_name +'_value').val();

    var response = "";
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == XMLHttpRequest.DONE) {
            response = xmlHttp.responseText;
        }
    };

    xmlHttp.open("GET", url+"?claim_name="+claim_name+"&claim_value="+claim_value, false);
    xmlHttp.send();

    if (response == "error"){
        $('#' + claim_name +'_info').text("An error has occurred");
        $('#' + claim_name +'_info').removeAttr("hidden");
        $('#' + claim_name +'_info').addClass("ssixa-error");
        $('#' + claim_name +'_info').removeClass("ssixa-success");
    } else {
        $('#' + claim_name +'_info').text("Verification has started");
        $('#' + claim_name +'_info').removeAttr("hidden");
        $('#' + claim_name +'_info').removeClass("ssixa-error");
        $('#' + claim_name +'_info').addClass("ssixa-success");
    }

}

function getAttestation(claim_name) {
    var url = "/claims/getattestation";

    var response = "";
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == XMLHttpRequest.DONE) {
            response = xmlHttp.responseText;
        }
    };

    xmlHttp.open("GET", url+"?claim_name="+claim_name, false);
    xmlHttp.send();

    if (response == "error"){
        $('#' + claim_name +'_info').text("An error has occurred");
        $('#' + claim_name +'_info').removeAttr("hidden");
        $('#' + claim_name +'_info').addClass("ssixa-error");
        $('#' + claim_name +'_info').removeClass("ssixa-success");
    } else {
        $('#' + claim_name +'_info').text("");
        $('#' + claim_name +'_info').append(response);
        $('#' + claim_name +'_info').removeAttr("hidden");
        $('#' + claim_name +'_info').removeClass("ssixa-error");
        $('#' + claim_name +'_info').removeClass("ssixa-success");
    }

}