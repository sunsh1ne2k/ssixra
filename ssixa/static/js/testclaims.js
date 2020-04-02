function getAttestation() {
    var url = "/testclaims/getattestation";

    var claim_name = $('#claim_name').val();
    var claim_value = $('#claim_value').val();

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
        $('#claim_info').text("An error has occurred");
        $('#claim_info').removeAttr("hidden");
        $('#claim_info').addClass("ssixa-error");
        $('#claim_info').removeClass("ssixa-success");
    } else {
        $('#claim_info').text("");
        $('#claim_info').append(response);
        $('#claim_info').removeAttr("hidden");
        $('#claim_info').removeClass("ssixa-error");
        $('#claim_info').removeClass("ssixa-success");
    }

}