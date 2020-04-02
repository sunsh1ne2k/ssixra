window.onload = function() {
  getVerificationUpdate();
};


function getVerificationUpdate(){
    var host = document.getElementById("url").textContent;
    var websocket = new WebSocket(host);

    websocket.onopen = function(ev){};
    websocket.onmessage = function(ev){
        if (ev.data == "verified"){
            document.forms[0].submit();
        }
    };
    websocket.onerror = function(ev) {};

}

function changeSSI(ssi) {
    var params = location.search;

    var pattern = new RegExp('\\b(ssi=).*?(&|#|$)');
    if (params.search(pattern)>=0) {
        params = params.replace(pattern,'$1' + ssi + '$2');
    } else {
        params = params + "&ssi=" + ssi;
    }

    window.location = location.pathname + params;
}