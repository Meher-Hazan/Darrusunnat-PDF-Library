// =========================================
//  DARRUSUNNAT LIBRARY - LOGIC
// =========================================

document.addEventListener('DOMContentLoaded', () => {
    applyLanguage(); 
    applyViewMode(); 

    fetch(CONFIG.dbUrl)
        .then(res => res.json())
        .then(data => {
            db = data.sort((a, b) => b.id - a.id);
            
            // Initial History State
            if (!history.state) {
                history.replaceState({ page: 'home' }, '', '');
            }
            
            setTab('home', false); 
            renderChips();
        })
        .catch(() => {
            document.getElementById('app').innerHTML = `<div class="loading-state">Error loading library. Please refresh.</div>`;
        });
        
    window.addEventListener('scroll', () => {
        const btn = document.getElementById('backToTop');
        if (window.scrollY > 300) btn.classList.add('show');
        else btn.classList.remove('show');
    });
});

// --- BACK BUTTON LOGIC ---
window.onpopstate = function(event) {
    if (document.getElementById('modal').classList.contains('active')) {
        closeModal();
        return;
    }
    
    if (event.state) {
        if (event.state.page === 'folder') {
            openFolder(event.state.type, event.state.key, false);
        } else if (event.state.page === 'home' || event.state.page === 'save') {
            setTab(event.state.page, false);
        }
    } else {
        setTab('home', false);
    }
};

// --- NAVIGATION ---
function setTab(tab, pushToHistory = true) {
    currentTab = tab;
    CONFIG.displayLimit = 24;
    window.scrollTo(0, 0);
    
    if (pushToHistory) {
        history.pushState({ page: tab }, '', '');
    }
    
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    
    const hero = document.getElementById('heroSection');
    if (tab === 'home') hero.style.display = 'block';
    else hero.style.display = 'none';

    if (tab === 'home') {
        renderBooks(db.slice(0, CONFIG.displayLimit));
    } else if (tab === 'save') {
        renderBooks(db.filter(b => saved.includes(b.id)), getText('saved', 'সংরক্ষিত বই'));
    } else if (tab === 'az') renderFolders('az');
    else if (tab === 'auth') renderFolders('author');
    else if (tab === 'cat') renderFolders('category');
}

// --- VIEW TOGGLE ---
function toggleView() {
    viewMode = viewMode === 'grid' ? 'list' : 'grid';
    localStorage.setItem('viewMode', viewMode);
    applyViewMode();
}

function applyViewMode() {
    const icon = document.getElementById('viewIcon');
    if (viewMode === 'list') {
        if(icon) icon.className = 'fas fa-th-large';
    } else {
        if(icon) icon.className = 'fas fa-list';
    }
    if (document.querySelector('.book-grid')) {
        const grid = document.querySelector('.book-grid');
        if (viewMode === 'list') grid.classList.add('list-view');
        else grid.classList.remove('list-view');
    }
}

// --- RENDERERS ---
function renderBooks(list, title = '') {
    const app = document.getElementById('app');
    
    if (list.length === 0) {
        app.innerHTML = `<div class="loading-state">${getText('noBooks', 'কোনো বই পাওয়া যায়নি।')}</div>`;
        return;
    }

    let html = title ? `<h3 class="section-title" style="margin-bottom:24px; font-family:var(--font-serif); font-size:1.5rem;">${title}</h3>` : '';
    const viewClass = viewMode === 'list' ? 'list-view' : '';
    html += `<div class="book-grid ${viewClass}">`;
    
    list.forEach(b => {
        const img = b.image || 'https://via.placeholder.com/300x450?text=No+Cover';
        const isSaved = saved.includes(b.id) ? 'active' : '';
        
        html += `
        <div class="book-card" onclick="openModal(${b.id})">
            <div class="save-badge ${isSaved}" onclick="toggleSave(event, ${b.id})">
                <i class="fas fa-bookmark"></i>
            </div>
            <div class="card-image-wrap">
                <img src="${img}" class="card-image" loading="lazy" alt="${b.title}">
            </div>
            <div class="card-meta">
                <h3 class="card-title">${b.title}</h3>
                <p class="card-author">${b.author || getText('unknown', 'অজ্ঞাত')}</p>
                <span class="card-category">${b.category || getText('general', 'সাধারণ')}</span>
            </div>
        </div>`;
    });
    
    html += '</div>';
    
    if (currentTab === 'home' && list.length < db.length && !document.getElementById('search').value) {
        html += `<div style="text-align:center; margin-top:40px;">
            <button onclick="loadMore()" class="action-btn secondary-btn" style="margin:0 auto;">
                ${getText('loadMore', 'আরও দেখুন')}
            </button>
        </div>`;
    }
    app.innerHTML = html;
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
    let html = `<div class="book-grid" style="grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));">`;
    
    keys.forEach(k => {
        let icon = 'fas fa-folder';
        if (type === 'auth') icon = 'fas fa-user-edit';
        if (type === 'cat') icon = 'fas fa-layer-group';
        
        html += `
        <div class="folder-item" onclick="openFolder('${type}', '${k}')">
            <div class="folder-icon"><i class="${icon}"></i></div>
            <div class="folder-name">${k}</div>
            <div class="folder-count">${groups[k]} ${getText('booksCount', 'টি বই')}</div>
        </div>`;
    });
    
    html += '</div>';
    document.getElementById('app').innerHTML = html;
}

function openFolder(type, key, pushToHistory = true) {
    if (pushToHistory) {
        history.pushState({ page: 'folder', type: type, key: key }, '', '');
    }
    
    let list = db.filter(b => {
        if (type === 'az') return b.title.charAt(0).toUpperCase() === key;
        return b[type] === key;
    });
    renderBooks(list, `${key}`);
    window.scrollTo(0,0);
}

// --- SEARCH & CHIPS ---
function handleSearch() {
    const q = document.getElementById('search').value;
    clearTimeout(searchTimeout);
    
    searchTimeout = setTimeout(() => {
        if (!q) {
            if (currentTab === 'home') renderBooks(db.slice(0, CONFIG.displayLimit));
            return;
        }
        
        const fuse = new Fuse(db, { keys: ['title', 'author', 'category'], threshold: 0.3 });
        const results = fuse.search(q).map(r => r.item);
        renderBooks(results, `${getText('results', 'অনুসন্ধান ফলাফল')}: "${q}"`);
    }, 300);
}

function renderChips() {
    const categories = [...new Set(db.map(b => b.category))].filter(Boolean).slice(0, 8);
    const container = document.getElementById('chipContainer');
    let html = `<button class="chip active" onclick="setTab('home')">All</button>`;
    
    categories.forEach(c => {
        html += `<button class="chip" onclick="openFolder('category', '${c}')">${c}</button>`;
    });
    container.innerHTML = html;
}

// --- MODAL ---
function openModal(id) {
    const b = db.find(x => x.id === id);
    if (!b) return;
    
    history.pushState({ modal: true, id: id }, '', '');

    document.getElementById('mImg').src = b.image || '';
    document.getElementById('mTitle').innerText = b.title;
    document.getElementById('mAuth').innerText = b.author || getText('unknown', 'অজ্ঞাত');
    document.getElementById('mCat').innerText = b.category;
    
    // READ BUTTON
    document.getElementById('mRead').href = b.link;

    // 🔥 COMMENT BUTTON (Group Link) 🔥
    const commentBtn = document.getElementById('mComment');
    if (commentBtn) {
        commentBtn.href = CONFIG.groupLink;
    }
    
    document.querySelector('.modal-backdrop').classList.add('active');
}

function closeModal(e) {
    if (!e || e.target.classList.contains('modal-backdrop') || e.target.classList.contains('modal-close')) {
        document.querySelector('.modal-backdrop').classList.remove('active');
        if (history.state && history.state.modal) {
            history.back();
        }
    }
}

// --- UTILITIES ---
function toggleSave(e, id) {
    e.stopPropagation();
    if (saved.includes(id)) saved = saved.filter(x => x !== id);
    else saved.push(id);
    localStorage.setItem('saved', JSON.stringify(saved));
    
    if (currentTab === 'save') {
        renderBooks(db.filter(b => saved.includes(b.id)), getText('saved', 'সংরক্ষিত বই'));
    } else {
        e.target.classList.toggle('active');
    }
}

function shareBook() {
    const msg = document.getElementById('toast');
    msg.classList.add('show');
    setTimeout(() => msg.classList.remove('show'), 3000);
}

function openRandom() {
    if (db.length > 0) {
        const randomId = db[Math.floor(Math.random() * db.length)].id;
        openModal(randomId);
    }
}

function loadMore() {
    CONFIG.displayLimit += 24;
    renderBooks(db.slice(0, CONFIG.displayLimit));
}

function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function toggleLanguage() {
    currentLang = currentLang === 'bn' ? 'en' : 'bn';
    localStorage.setItem('lang', currentLang);
    location.reload(); 
}

function applyLanguage() {
    document.documentElement.lang = currentLang;
    document.querySelectorAll('[data-en]').forEach(el => {
        el.innerText = el.getAttribute(`data-${currentLang}`);
    });
    const searchInput = document.getElementById('search');
    if (searchInput) {
        searchInput.placeholder = getText('searchPlaceholder', 'বই, লেখক বা বিষয় খুঁজুন...');
    }
}

function toggleMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    menu.classList.toggle('active');
}