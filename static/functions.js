function async_request(url, callback, cbdata) {
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            var result = JSON.parse(xmlhttp.responseText);
            callback(result, cbdata);
        }
    };
    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}

function hex2(n)
{
    if (n < 16) {
        return '0' + n.toString(16);
    } else {
        return n.toString(16);
    }
}

function range2color(value, min, max) {
    green = (value - min) * 255 / (max - min);
    if (green > 255) {
        green = 255;
    }
    red = 255 - green;
    return '#' + hex2(red) + hex2(green) + '00';
}

