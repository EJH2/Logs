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

const privacyRadios = document.logForm.privacy;
const guildDiv = document.getElementById('guildDiv');
const guildOption = document.getElementById('guild');
function guildVisibility(value) {
    if (!(['guild', 'mods'].includes(value))) {
        guildDiv.style.display = 'none';
        guildOption.required = false;
    }
    else {
        guildDiv.style.display = 'block';
        guildOption.required = true;
    }
}
guildVisibility(document.logForm.privacy.value);
for (let i = 0; i < privacyRadios.length; i++) {
    privacyRadios[i].addEventListener('change', function () {guildVisibility(this.value)})
}
