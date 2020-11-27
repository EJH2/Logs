const baguetteSettings = {animation: 'fadeIn', noScrollbars: true, buttons: false};

let lastDate = moment(0);

function insertDivider(message) {
    let dividerSpan = document.createElement('span');
    dividerSpan.classList.add('content-1o0f9g');
    let msgTime = message.querySelectorAll('.timestamp-3ZCmNB time, .timestamp-3ZCmNB span')[0];
    let date = msgTime.getAttribute('datetime');
    dividerSpan.innerText = moment(date).format('MMMM D, YYYY');
    let dividerDiv = document.createElement('div');
    dividerDiv.classList.add('divider-3_HH5L', 'hasContent-1_DUdQ', 'divider-JfaTT5', 'hasContent-1cNJDh');
    dividerDiv.appendChild(dividerSpan);
    message.parentElement.insertBefore(dividerDiv, message);
}

function loadJS(page) {

    for (let t of page.querySelectorAll('.timestamp-3ZCmNB time, .timestamp-3ZCmNB span')) {
        let currentDate = moment(t.getAttribute('datetime'));
        if (currentDate.date() !== lastDate.date() && lastDate._i !== 0) {
            insertDivider(t.closest('div.message-group'))
        }
        if (currentDate > lastDate) {
            lastDate = currentDate;
        }
    }

    page.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightBlock(block);
    });

    baguetteBox.run('.imageZoom-1n-ADA', baguetteSettings);

    for (let t of page.getElementsByTagName('time')) {
        let date = t.getAttribute('datetime');
        t.textContent = moment(date).calendar();
    }

    for (let h of page.querySelectorAll('.timestampVisibleOnHover-2bQeI4 span')) {
        let date = h.getAttribute('datetime');
        h.textContent = moment(date).format('LT')
    }

    for (let s of page.getElementsByClassName('spoilerText-3p6IlD')) {
        s.onclick = function () {
            s.classList.toggle('hidden-HHr2R9');
        };
        s.classList.add('hidden-HHr2R9');
    }

    for (let s of page.getElementsByClassName('mention user')) {
        s.onclick = function () {
            return copyIDMention(s);
        }
    }

    for (let s of page.querySelectorAll('span.mentioned')) {
        s.parentElement.classList.add('mentioned')
    }

    for (let s of page.querySelectorAll('span.mention')) {
        if (s.title === uid) {
            s.classList.add('mentioned');
        }
    }

    for (let m of page.querySelectorAll('.message-group')) {
        let avatarElem = m.getElementsByClassName('avatar-1BDn8e')[0];
        if (avatarElem.src.indexOf('.gif') > -1) {
            avatarElem.src = avatarElem.src.replace('.gif', '.png');
            m.onmouseenter = function () {
                avatarElem.src = avatarElem.src.replace('.png', '.gif');
            };
            m.onmouseleave = function () {
                avatarElem.src = avatarElem.src.replace('.gif', '.png');
            }
        }
    }
}

window.addEventListener('DOMContentLoaded', (event) => {
    document.body.classList.remove('no-js');

    initialTheme();

    loadJS(document.getElementById('message-page-1') || document.getElementById('message-container'));

    if (typeof InfiniteScroll !== 'undefined') {
        let infScroll = new InfiniteScroll('.infinite-container', {
            path: '.infinite-more-link',
            append: '.infinite-item',
            status: '.infinite-scroll-status',
            hideNav: '.infinite-next',
            history: false,
        });
        infScroll.on('append', function (response, path, items) {
            loadJS(items[0]);
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
    let html = document.querySelectorAll('html')[0];
    if (theme === 'light') {
        html.classList.replace('theme-dark', 'theme-light');
        for (let cssTheme of cssThemes) {
            cssTheme.setAttribute('href', '/static/discord_logview/css/logs_light.css');
        }
        for (let hlTheme of hlThemes) {
            hlTheme.setAttribute('href', 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.6/styles/solarized-light.min.css');
        }
        if (guildIcon.src.indexOf('processing') === -1 && ['black_file', 'white_file'].indexOf(guildIcon.src.slice(-14, -4)) > -1) {
            guildIcon.src = '/static/discord_logview/icons/black_file.png';
        }
    } else {
        html.classList.replace('theme-light', 'theme-dark');
        for (let cssTheme of cssThemes) {
            cssTheme.setAttribute('href', '/static/discord_logview/css/logs_dark.css');
        }
        for (let hlTheme of hlThemes) {
            hlTheme.setAttribute('href', 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.6/styles/solarized-dark.min.css');
        }
        if (guildIcon.src.indexOf('processing') === -1 && ['black_file', 'white_file'].indexOf(guildIcon.src.slice(-14, -4)) > -1) {
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
