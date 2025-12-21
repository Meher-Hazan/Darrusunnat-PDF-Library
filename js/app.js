// =========================================
//  DARRUSUNNAT LIBRARY - LOGIC
// =========================================

document.addEventListener('DOMContentLoaded', () => {
    applyLanguage(); 
    
    fetch(CONFIG.dbUrl)
        .then(res => res.json())
        .then(data => {
            db = data.sort((a, b) => b.id - a.id);
            setTab('home', false);
            renderChips();
        })
        .catch(() => {
            document.getElementById('app').innerHTML = `<div class="loading-state">Error loading library.</div>`;
        });
        
    window.addEventListener('scroll', () => {
        const btn = document.getElementById('backToTop');
        if (window.scrollY > 300) btn.classList.add('show');
        else btn.classList.remove('show');
    });
});

window.onpopstate = function(event) {
    if (document.querySelector('.modal-backdrop.active')) {
        closeModal();
        return;
    }
    if (event.state) {
        if (event.state.page === 'folder') openFolder(event.state.type, event.state.key, false);
        else setTab(event.state.page, false);
    } else {
        setTab('home', false);
    }
};

function setTab(tab, pushToHistory = true) {
    currentTab = tab;
    CONFIG.displayLimit = 30;
    window.scrollTo(0, 0);
    
    if (pushToHistory) history.pushState({ page: tab }, '', '');
    
    const hero = document.getElementById('heroSection');
    if (tab === 'home') hero.style.display = 'block';
    else hero.style.display = 'none';

    if (tab === 'home') {
        renderHomePage();
    } else if (tab === 'save') {
        renderGrid(db.filter(b => saved.includes(b.id)), getText('saved', 'সংরক্ষিত'));
    } else if (tab === 'az') renderFolders('az');
    else if (tab === 'auth') renderFolders('author');
    else if (tab === 'cat') renderFolders('category');
}

// --- HOME PAGE (SHELF + GRID) ---
function renderHomePage() {
    const app = document.getElementById('app');
    
    // 1. Featured (Random 10)
    const featured = [...db].sort(() => 0.5 - Math.random()).slice(0, 10);
    // 2. Recent (Grid)
    const recent = db.slice(0, CONFIG.displayLimit);

    let html = `
        <div class="section-header">
            <h3>🔥 ${getText('featured', 'জনপ্রিয় কিতাব')}</h3>
        </div>
        <div class="horizontal-shelf">
            ${generateCards(featured, true)}
        </div>

        <div class="section-header">
            <h3>📚 ${getText('recent', 'নতুন সংযোজন')}</h3>
        </div>
        <div class="book-grid">
            ${generateCards(recent, false)}
        </div>
        
        <button onclick="loadMore()" class="load-more">${getText('loadMore', 'আরও দেখুন')}</button>
    `;
    
    app.innerHTML = html;
}

// Helper
function generateCards(list, isHorizontal) {
    if (!list.length) return `<div style="padding:10px;">${getText('noBooks', 'বই নেই')}</div>`;
    
    return list.map(b => {
        const img = b.image || 'https://via.placeholder.com/300x450?text=No+Cover';
        const isSaved = saved.includes(b.id) ? 'active' : '';
        const cardClass = isHorizontal ? 'book-card-horizontal' : 'book-card';
        
        return `
        <div class="${cardClass}" onclick="openModal(${b.id})">
            <div class="save-badge ${isSaved}" onclick="toggleSave(event, ${b.id})">
                <i class="fas fa-bookmark"></i>
            </div>
            <div class="card-image-wrap">
                <img src="${img}" class="card-image" loading="lazy">
            </div>
            <div class="card-meta">
                <div class="card-title">${b.title}</div>
                <div class="card-author">${b.author || getText('unknown', 'অজ্ঞাত')}</div>
            </div>
        </div>`;
    }).join('');
}

function renderGrid(list, title) {
    const app = document.getElementById('app');
    let html = `<h3 class="section-title">${title}</h3><div class="book-grid">${generateCards(list, false)}</div>`;
    app.innerHTML = html;
}

function handleSearch() {
    const q = document.getElementById('search').value;
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        if (!q) { setTab('home', false); return; }
        const fuse = new Fuse(db, { keys: ['title', 'author', 'category'], threshold: 0.3 });
        const results = fuse.search(q).map(r => r.item);
        renderGrid(results, `${getText('results', 'ফলাফল')}: "${q}"`);
    }, 300);
}

function renderFolders(type) {
    const groups = {};
    db.forEach(b => {
        let key = b[type] || getText('others', 'অন্যান্য');
        if (type === 'az') key = b.title.charAt(0).toUpperCase();
        if (!groups[key]) groups[key] = 0;
        groups[key]++;
    });
    const keys = Object.keys(groups).sort();
    let html = `<div class="folder-grid">`;
    keys.forEach(k => {
        html += `
        <div class="folder-item" onclick="openFolder('${type}', '${k}')">
            <div class="folder-icon"><i class="fas fa-folder"></i></div>
            <div class="folder-name">${k}</div>
            <div class="folder-count">${groups[k]} ${getText('booksCount', 'টি বই')}</div>
        </div>`;
    });
    html += '</div>';
    document.getElementById('app').innerHTML = html;
}

function openFolder(type, key, pushToHistory = true) {
    if (pushToHistory) history.pushState({ page: 'folder', type: type, key: key }, '', '');
    let list = db.filter(b => {
        if (type === 'az') return b.title.charAt(0).toUpperCase() === key;
        return b[type] === key;
    });
    renderGrid(list, key);
}

function openModal(id) {
    const b = db.find(x => x.id === id);
    if (!b) return;
    history.pushState({ modal: true, id: id }, '', '');
    document.getElementById('mImg').src = b.image || '';
    document.getElementById('mTitle').innerText = b.title;
    document.getElementById('mAuth').innerText = b.author || getText('unknown', 'অজ্ঞাত');
    document.getElementById('mCat').innerText = b.category;
    document.getElementById('mRead').href = b.link;
    // ✅ CORRECT LINK IS PULLED FROM CONFIG
    document.getElementById('mComment').href = CONFIG.groupLink; 
    document.querySelector('.modal-backdrop').classList.add('active');
}

function closeModal() {
    document.querySelector('.modal-backdrop').classList.remove('active');
    if (history.state && history.state.modal) history.back();
}

function renderChips() {
    const categories = [...new Set(db.map(b => b.category))].filter(Boolean).slice(0, 8);
    const container = document.getElementById('chipContainer');
    let html = `<button class="chip" onclick="setTab('home')">All</button>`;
    categories.forEach(c => html += `<button class="chip" onclick="openFolder('category', '${c}')">${c}</button>`);
    container.innerHTML = html;
}

function toggleSave(e, id) {
    e.stopPropagation();
    if (saved.includes(id)) saved = saved.filter(x => x !== id);
    else saved.push(id);
    localStorage.setItem('saved', JSON.stringify(saved));
    if (currentTab === 'save') renderGrid(db.filter(b => saved.includes(b.id)), getText('saved', 'সংরক্ষিত'));
    else e.target.classList.toggle('active');
}

function loadMore() { CONFIG.displayLimit += 30; renderHomePage(); }
function toggleLanguage() {
    currentLang = currentLang === 'bn' ? 'en' : 'bn';
    localStorage.setItem('lang', currentLang);
    location.reload(); 
}
function applyLanguage() {
    document.documentElement.lang = currentLang;
    document.querySelectorAll('[data-en]').forEach(el => el.innerText = el.getAttribute(`data-${currentLang}`));
    const s = document.getElementById('search');
    if(s) s.placeholder = getText('searchPlaceholder', '...');
}
function toggleMobileMenu() { document.getElementById('mobileMenu').classList.toggle('active'); }
function shareBook() { document.getElementById('toast').classList.add('show'); setTimeout(()=>document.getElementById('toast').classList.remove('show'), 3000); }
function openRandom() { if(db.length) openModal(db[Math.floor(Math.random()*db.length)].id); }
function scrollToTop() { window.scrollTo({ top: 0, behavior: 'smooth' }); }