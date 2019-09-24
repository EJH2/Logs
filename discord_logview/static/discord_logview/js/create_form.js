function clear_file() {
    const file = document.getElementById('file');
    const new_file = document.createElement('input');
    new_file.type = "file";
    new_file.id = file.id;
    new_file.name = file.name;
    new_file.onchange = file.onchange;
    file.parentNode.replaceChild(new_file, file);
}

function clear_url() {
    document.getElementById('url').value = '';
}
