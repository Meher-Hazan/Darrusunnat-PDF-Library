// STARTUP
fetch(CONFIG.dbUrl)
    .then(res => res.json())
    .then(data => {
        db = data.sort((a, b) => b.id - a.id);
        setTab('home');
        startClock();
        updateViewIcon();
    })
    .catch(() => document.getElementById('app').innerHTML = "<div class='loading'>ডেটা লোড হয়নি।</div>");

function startClock() {
    setInterval(() => {
        const d = new Date();
        const t = d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
        const date = d.toLocaleDateString('bn-BD');
        
        if(document.getElementById('mobTime')) document.getElementById('mobTime').innerText = t;
        if(document.getElementById('mobDate')) document.getElementById('mobDate').innerText = date;
        if(document.getElementById('pcTime')) document.getElementById('pcTime').innerText = t;
        if(document.getElementById('pcDate')) document.getElementById('pcDate').innerText = date;
    }, 1000);
}

function setTab(tab, pushHist = true) {
    if(pushHist) historyStack.push(currentTab);
    currentTab = tab;
    CONFIG.displayLimit = 24;
    
    document.querySelectorAll('.pc-link, .nav-item').forEach(el => el.classList.remove('active'));
    if(document.getElementById('pc-'+tab)) document.getElementById('pc-'+tab).classList.add('active');
    if(document.getElementById('mob-'+tab)) document.getElementById('mob-'+tab).classList.add('active');
    
    const hero = document.getElementById('heroSection');
    if(tab === 'home') {
        hero.style.display = 'flex';
        document.getElementById('search').value = "";
    } else {
        hero.style.display = 'none';
    }
    
    window.scrollTo(0, 0);

    if (tab === 'home') {
        currentList = db;
        renderBooks(db.slice(0, CONFIG.displayLimit));
    } else if (tab === 'save') {
        currentList = db.filter(b => saved.includes(b.id));
        renderBooks(currentList, "সংরক্ষিত বই");
    } else if (tab === 'az') renderFolders('az');
    else if (tab === 'auth') renderFolders('author');
    else if (tab === 'cat') renderFolders('category');
}

function goBack() {
    if(historyStack.length > 0) {
        setTab(historyStack.pop(), false);
    } else {
        setTab('home', false);
    }
}

function handleSearch() {
    const q = document.getElementById('search').value;
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        if(!q) { if(currentTab === 'home') renderBooks(db.slice(0, CONFIG.displayLimit)); return; }
        const fuse = new Fuse(db, { keys: ['title', 'author', 'category'], threshold: 0.3 });
        const results = fuse.search(q).map(r => r.item);
        currentList = results;
        renderBooks(results, `অনুসন্ধান ফলাফল: "${q}"`);
    }, 300);
}

function renderBooks(list, title = '') {
    const app = document.getElementById('app');
    if(!list.length) { app.innerHTML = "<div class='loading'>কোনো বই পাওয়া যায়নি</div>"; return; }

    let html = title ? `<h2 class='sec-title'>${title}</h2>` : '';
    html += viewMode === 'grid' ? '<div class="grid">' : '<div class="list-view">';
    
    list.forEach(b => {
        const img = b.image || 'https://via.placeholder.com/300x450/0f4c3a/ffffff?text=Book';
        const isSaved = saved.includes(b.id) ? 'active' : '';
        const clickFn = `openModal(${b.id})`;
        const saveFn = `toggleSave(event, ${b.id})`;
        
        if (viewMode === 'grid') {
            html += `
            <div class="card" onclick="${clickFn}">
                <div class="save-btn ${isSaved}" onclick="${saveFn}"><i class="fas fa-bookmark"></i></div>
                <div class="card-img-wrap"><img src="${img}" class="card-img" loading="lazy"></div>
                <div class="card-info"><div class="card-title">${b.title}</div><div class="card-cat">${b.author || 'অজ্ঞাত'}</div></div>
            </div>`;
        } else {
            html += `
            <div class="list-item" onclick="${clickFn}">
                <img src="${img}" class="list-thumb" loading="lazy">
                <div class="list-data"><div class="list-title">${b.title}</div><div class="list-cat">${b.author || 'অজ্ঞাত'}</div></div>
            </div>`;
        }
    });
    html += '</div>';
    if(currentTab === 'home' && list.length < db.length && !document.getElementById('search').value) {
        html += `<button class="load-more" onclick="loadMore()">আরও দেখুন</button>`;
    }
    app.innerHTML = html;
}

function renderFolders(type) {
    const groups = {};
    db.forEach(b => {
        let key = 'অন্যান্য';
        if(type === 'az') {
            const clean = b.title.replace(/^[\d\s\.\-\_\#\(\)\[\]\:\>]+/, '').trim();
            const match = clean.match(/^[a-zA-Z\u0980-\u09FF\u0600-\u06FF]/);
            key = match ? match[0].toUpperCase() : '#';
        } else {
            key = b[type] || 'অজ্ঞাত';
            if(type === 'author' && key === 'Darrusunnat Library') return;
        }
        if(!groups[key]) groups[key] = 0; groups[key]++;
    });
    const keys = Object.keys(groups).sort();
    let html = '<div class="folder-grid">';
    keys.forEach(k => html += `<div class="folder" onclick="openFolder('${type}', '${k}')"><div class="folder-icon">${k}</div><div class="folder-label">${groups[k]} টি বই</div></div>`);
    html += '</div>';
    document.getElementById('app').innerHTML = html;
}

function openFolder(type, key) {
    let list = [];
    if(type === 'az') {
        list = db.filter(b => {
            const clean = b.title.replace(/^[\d\s\.\-\_\#\(\)\[\]]+/, '').trim();
            const match = clean.match(/^[a-zA-Z\u0980-\u09FF\u0600-\u06FF]/);
            return match && match[0].toUpperCase() === key;
        });
    } else { list = db.filter(b => b[type] === key); }
    const backBtn = `<div class="back-bar" onclick="goBack()"><i class="fas fa-arrow-left"></i> পেছনে যান</div>`;
    renderBooks(list, `${backBtn}<br>${key}`);
}

function loadMore() { CONFIG.displayLimit += 24; renderBooks(db.slice(0, CONFIG.displayLimit)); }

function toggleSave(e, id) {
    e.stopPropagation();
    if(saved.includes(id)) saved = saved.filter(x => x !== id); else saved.push(id);
    localStorage.setItem('saved', JSON.stringify(saved));
    if(currentTab === 'save') setTab('save'); else e.target.classList.toggle('active');
}

function toggleView() {
    viewMode = viewMode === 'grid' ? 'list' : 'grid';
    localStorage.setItem('viewMode', viewMode);
    // Update icons
    const icon = viewMode === 'grid' ? '<i class="fas fa-list"></i>' : '<i class="fas fa-th-large"></i>';
    if(document.getElementById('headerViewBtn')) document.getElementById('headerViewBtn').innerHTML = icon;
    
    if(document.querySelector('.grid') || document.querySelector('.list-view')) {
        if(document.getElementById('search').value) handleSearch();
        else if(currentTab === 'home') renderBooks(db.slice(0, CONFIG.displayLimit));
        else if(currentTab === 'save') setTab('save');
    }
}

function updateViewIcon() {
    const icon = viewMode === 'grid' ? '<i class="fas fa-list"></i>' : '<i class="fas fa-th-large"></i>';
    if(document.getElementById('headerViewBtn')) document.getElementById('headerViewBtn').innerHTML = icon;
}

function openModal(id) {
    const b = db.find(x => x.id === id); if(!b) return;
    currentLink = b.link;
    document.getElementById('mImg').src = b.image || '';
    document.getElementById('mTitle').innerText = b.title;
    document.getElementById('mAuth').innerText = b.author || 'অজ্ঞাত';
    document.getElementById('mRead').href = b.link;
    window.history.pushState({modal: true}, null, "");
    document.getElementById('modal').classList.add('active');
}

function closeModal() {
    document.getElementById('modal').classList.remove('active');
    if(history.state && history.state.modal) history.back();
}

window.onpopstate = function(e) {
    if(document.getElementById('modal').classList.contains('active')) closeModal();
    else goBack();
};

function shareBook() { navigator.clipboard.writeText(currentLink); alert("লিংক কপি হয়েছে!"); }
function joinGroup() { window.open(CONFIG.groupLink); }

function openRandom() {
    if(db.length) openModal(db[Math.floor(Math.random() * db.length)].id);
}

// --- BACK TO TOP LOGIC ---
const backToTopBtn = document.getElementById("backToTopBtn");

window.onscroll = function() {
    if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
        backToTopBtn.style.display = "block";
    } else {
        backToTopBtn.style.display = "none";
    }
};

backToTopBtn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
});
