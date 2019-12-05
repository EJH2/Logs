function loadJS() {

    document.querySelectorAll('.pre--multiline').forEach((block) => {
        hljs.highlightBlock(block);
    });

    const lightDiv = document.getElementById('lightbox_div');

    for (let attach of document.getElementsByClassName('message-attachment-thumbnail')) {
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

    for (let s of document.getElementsByClassName('spoiler-box')) {
        s.onclick = function () {
            s.classList.toggle('spoiler-hidden');
        };
        s.classList.add('spoiler-hidden');
    }

    for (let s of document.getElementsByClassName('mention user')) {
        s.onclick = function () {
            return copyIDMention(s);
        }
    }

    for (let s of document.querySelectorAll('span.mentioned')) {
        s.parentElement.classList.add('mentioned')
    }

    for (let s of document.querySelectorAll('span.mention')) {
        if (s.title === uid) {
            s.classList.add('mentioned');
        }
    }
}

window.addEventListener('DOMContentLoaded', (event) => {
    document.body.classList.remove('no-js');

    initialTheme();

    loadJS();

    if (typeof InfiniteScroll !== 'undefined') {
        let infScroll = new InfiniteScroll('.infinite-container', {
            path: '.infinite-more-link',
            append: '.infinite-item',
            status: '.infinite-scroll-status',
            hideNav: '.infinite-next',
            history: false,
        });
        infScroll.on('append', function (response, path, items) {
            loadJS()
        });
    }
});

function toggleDrawer(element) {
    element.classList.toggle('rotated');
}

function initialTheme() {
    let theme = window.localStorage.getItem('theme') || (
        window.matchMedia('(prefers-color-scheme: dark)').media === 'not all' ? 'dark' : (
            window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
        )
    );
    setTheme(theme)
}

function setTheme(theme) {
    let cssThemes = document.getElementsByClassName('theme');
    let hlThemes = document.getElementsByClassName('hl_theme');
    let guildIcon = document.getElementById('header-icon');
    if (theme === 'light') {
        for (let cssTheme of cssThemes) {
            cssTheme.setAttribute('href', '/static/discord_logview/css/logs_light.css');
        }
        for (let hlTheme of hlThemes) {
            hlTheme.setAttribute('href', 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.6/styles/solarized-light.min.css');
        }
        if (guildIcon.src.indexOf('processing') === -1) {
            guildIcon.src = '/static/discord_logview/icons/black_file.png';
        }
    } else {
        for (let cssTheme of cssThemes) {
            cssTheme.setAttribute('href', '/static/discord_logview/css/logs_dark.css');
        }
        for (let hlTheme of hlThemes) {
            hlTheme.setAttribute('href', 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.6/styles/solarized-dark.min.css');
        }
        if (guildIcon.src.indexOf('processing') === -1) {
            guildIcon.src = '/static/discord_logview/icons/white_file.png';
        }
    }
}

function toggleTheme() {
    let theme = window.localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    console.log(theme);
    if (theme === 'dark') {
        window.localStorage.setItem('theme', 'light');
        setTheme('light');
    } else {
        window.localStorage.setItem('theme', 'dark');
        setTheme('dark');
    }
}

function toggleUsers() {
    let list = document.getElementById('users');
    let check = document.getElementById('user-list-toggle');
    if (list.style.maxHeight === '0px' || list.style.maxHeight === '') {
        list.style.maxHeight = list.scrollHeight + 'px';
    } else {
        list.style.maxHeight = '0px';
    }
    check.classList.toggle('rotated');
}

function copyID(element) {
    let copyText = element.children[1];
    let textArea = document.createElement('textarea');
    textArea.value = copyText.textContent;
    document.body.appendChild(textArea);
    copyText.classList.toggle('copied');
    setTimeout(function () {
        copyText.classList.toggle('copied');
    }, 1000);
    textArea.select();
    document.execCommand('Copy');
    textArea.remove();
}

function copyIDMention(element) {
    let textArea = document.createElement('textarea');
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
    const userList = document.getElementById('user-list');
    const users = userList.getElementsByClassName('user');
    let ids = [];
    for (let c of users) {
        ids.push(c.getElementsByClassName('id')[0].innerText);
    }
    let textArea = document.createElement('textarea');
    textArea.value = (ids).join(' ');
    document.body.appendChild(textArea);
    setTimeout(function () {
        element.classList.toggle('copied');
    }, 1000);
    textArea.select();
    document.execCommand('Copy');
    textArea.remove();
    element.classList.toggle('copied');
}
