function loadJS() {

    document.querySelectorAll('.pre--multiline').forEach((block) => {
        hljs.highlightBlock(block);
    });

    const lightDiv = document.getElementById('lightbox_div');

    for (let attach of document.getElementsByClassName('chatlog__attachment-thumbnail')) {
        let a = attach.parentElement;
        a.onclick = function () {
            let id = a.getAttribute('href').substring(1);
            let lightA = document.createElement('a');
            lightA.setAttribute('id', id);
            lightA.classList.add('lightbox');
            let lightImg = document.createElement('img');
            lightImg.setAttribute('src', attach.getAttribute('src'));
            lightA.onclick = function () {
                window.history.back();
                lightDiv.innerHTML = '';
            };
            lightA.appendChild(lightImg);
            lightDiv.appendChild(lightA);
        };
    }

    for (let t of document.getElementsByTagName('time')) {
        let date = t.getAttribute('datetime');
        t.textContent = moment(date).calendar();
    }

    for (let s of document.getElementsByClassName('chatlog__spoiler-box')) {
        s.onclick = function () {
            s.classList.toggle('chatlog__spoiler-hidden');
        };
        s.classList.add('chatlog__spoiler-hidden');
    }

    for (let s of document.getElementsByClassName('mention user')) {
        s.onclick = function () {
            return copyIDMention(s);
        }
    }

    for (let s of document.querySelectorAll('span.mention')) {
        s.parentElement.style.margin = '2px 0';
    }

    for (let s of document.querySelectorAll('span.mentioned')) {
        s.parentElement.classList.add('mentioned')
    }
}

window.addEventListener('DOMContentLoaded', (event) => {
    document.body.classList.remove('no-js');

    loadJS();

    if (typeof InfiniteScroll !== 'undefined') {
        let infScroll = new InfiniteScroll('.infinite-container', {
            path: '.infinite-more-link',
            append: '.infinite-item',
            status: '.infinite-scroll-status',
            hideNav: '.infinite-next',
            history: 'replace',
        });
        infScroll.on('append', function (response, path, items) {
            loadJS()
        });
    }
});

function toggleDrawer(element) {
    element.classList.toggle('rotated');
}

function toggleTheme() {
    let theme = document.getElementById('theme');
    let hlTheme = document.getElementById('hl_theme');
    let guildIcon = document.getElementsByClassName('info__guild-icon')[0];
    if (theme.getAttribute('href').indexOf('dark') > -1) {
        theme.setAttribute('href', '/static/django_logs/css/logstyle_light.css');
        hlTheme.setAttribute('href', 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.6/styles/solarized-light.min.css');
    } else {
        theme.setAttribute('href', '/static/django_logs/css/logstyle_dark.css');
        hlTheme.setAttribute('href', 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.6/styles/solarized-dark.min.css');
    }
    if (guildIcon.src.indexOf('white_file') > -1) {
        guildIcon.src = "/static/django_logs/icons/black_file.png"
    } else if (guildIcon.src.indexOf('black_file') > -1) {
        guildIcon.src = "/static/django_logs/icons/white_file.png"
    }
}

function toggleUsers() {
    let list = document.getElementsByClassName('info__users')[0];
    let check = document.getElementsByClassName('info__user-toggle')[0];
    if (list.style.maxHeight === "0px" || list.style.maxHeight === "") {
        list.style.maxHeight = list.scrollHeight + "px";
    } else {
        list.style.maxHeight = "0px";
    }
    check.classList.toggle('rotated');
}

function copyID(element) {
    let copyText = element.children[1];
    let textArea = document.createElement("textarea");
    textArea.value = copyText.textContent;
    document.body.appendChild(textArea);
    copyText.classList.toggle('copied');
    setTimeout(function () {
        copyText.classList.toggle('copied');
    }, 1000);
    textArea.select();
    document.execCommand("Copy");
    textArea.remove();
}

function copyIDMention(element) {
    let textArea = document.createElement("textarea");
    textArea.value = element.getAttribute('title');
    document.body.appendChild(textArea);
    element.classList.toggle('copied');
    setTimeout(function () {
        element.classList.toggle('copied');
    }, 1000);
    textArea.select();
    document.execCommand("Copy");
    textArea.remove();
}

function copyAllMenu(element) {
    let tooltip = element.parentElement.children[1];
    copyAll(tooltip);
}

function copyAll(element) {
    let textArea = document.createElement("textarea");
    textArea.value = ([]).join(" ");
    document.body.appendChild(textArea);
    setTimeout(function () {
        element.classList.toggle('copied');
    }, 1000);
    textArea.select();
    document.execCommand("Copy");
    textArea.remove();
    element.classList.toggle('copied');
}
