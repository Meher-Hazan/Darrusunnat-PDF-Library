// CONFIGURATION
const CONFIG = {
    dbUrl: 'books_data.json?t=' + Date.now(),
    displayLimit: 24
};

// STATE
let db = [];
let saved = JSON.parse(localStorage.getItem('saved')) || [];
let currentLang = localStorage.getItem('lang') || 'bn'; // 'bn' or 'en'
let currentTab = 'home';
let searchTimeout;

// INIT
document.addEventListener('DOMContentLoaded', () => {
    applyLanguage(); // Apply saved language
    
    fetch(CONFIG.dbUrl)
        .then(res => res.json())
        .then(data => {
            db = data.sort((a, b) => b.id - a.id);
            setTab('home');
            renderChips();
        })
        .catch(() => {
            document.getElementById('app').innerHTML = `<div class="loading-state">Error loading library. Please refresh.</div>`;
        });
        
    // Scroll listener for Back to Top
    window.addEventListener('scroll', () => {
        const btn = document.getElementById('backToTop');
        if (window.scrollY > 300) btn.classList.add('show');
        else btn.classList.remove('show');
    });
});

// --- NAVIGATION ---
function setTab(tab) {
    currentTab = tab;
    CONFIG.displayLimit = 24;
    window.scrollTo(0, 0);
    
    // Update Active Link UI
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    // (Simple logic to highlight active link would go here if IDs matched exactly)
    
    // Manage Hero Visibility
    const hero = document.getElementById('heroSection');
    if (tab === 'home') hero.style.display = 'block';
    else hero.style.display = 'none';

    // Route
    if (tab === 'home') {
        renderBooks(db.slice(0, CONFIG.displayLimit));
    } else if (tab === 'save') {
        renderBooks(db.filter(b => saved.includes(b.id)), getText('Saved Books', 'সংরক্ষিত বই'));
    } else if (tab === 'az') {
        renderFolders('az');
    } else if (tab === 'auth') {
        renderFolders('author');
    } else if (tab === 'cat') {
        renderFolders('category');
    }
}

// --- RENDERERS ---
function renderBooks(list, title = '') {
    const app = document.getElementById('app');
    
    if (list.length === 0) {
        app.innerHTML = `<div class="loading-state">${getText('No books found.', 'কোনো বই পাওয়া যায়নি।')}</div>`;
        return;
    }

    let html = title ? `<h3 class="section-title" style="margin-bottom:24px; font-family:var(--font-serif); font-size:1.5rem;">${title}</h3>` : '';
    html += '<div class="book-grid">';
    
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
                <p class="card-author">${b.author || getText('Unknown', 'অজ্ঞাত')}</p>
                <span class="card-category">${b.category || getText('General', 'সাধারণ')}</span>
            </div>
        </div>`;
    });
    
    html += '</div>';
    
    // Load More Button
    if (currentTab === 'home' && list.length < db.length && !document.getElementById('search').value) {
        html += `<div style="text-align:center; margin-top:40px;">
            <button onclick="loadMore()" class="action-btn secondary-btn" style="margin:0 auto;">
                ${getText('Load More', 'আরও দেখুন')}
            </button>
        </div>`;
    }
    
    app.innerHTML = html;
}

function renderFolders(type) {
    const groups = {};
    db.forEach(b => {
        let key = b[type] || getText('Others', 'অন্যান্য');
        if (type === 'az') key = b.title.charAt(0).toUpperCase(); // First letter
        if (!groups[key]) groups[key] = 0;
        groups[key]++;
    });
    
    const keys = Object.keys(groups).sort();
    let html = `<div class="book-grid" style="grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));">`;
    
    keys.forEach(k => {
        // Icon logic
        let icon = 'fas fa-folder';
        if (type === 'auth') icon = 'fas fa-user-edit';
        if (type === 'cat') icon = 'fas fa-layer-group';
        
        html += `
        <div class="folder-item" onclick="openFolder('${type}', '${k}')">
            <div class="folder-icon"><i class="${icon}"></i></div>
            <div class="folder-name">${k}</div>
            <div class="folder-count">${groups[k]} ${getText('Books', 'টি বই')}</div>
        </div>`;
    });
    
    html += '</div>';
    document.getElementById('app').innerHTML = html;
}

function openFolder(type, key) {
    let list = db.filter(b => {
        if (type === 'az') return b.title.charAt(0).toUpperCase() === key;
        return b[type] === key;
    });
    renderBooks(list, `${key}`);
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
        renderBooks(results, `${getText('Search Results', 'অনুসন্ধান ফলাফল')}: "${q}"`);
    }, 300);
}

function renderChips() {
    // Collect unique categories dynamically or use static list
    const categories = [...new Set(db.map(b => b.category))].filter(Boolean).slice(0, 8); // Top 8
    const container = document.getElementById('chipContainer');
    let html = `<button class="chip active" onclick="setTab('home')">${getText('All', 'সব')}</button>`;
    
    categories.forEach(c => {
        html += `<button class="chip" onclick="openFolder('category', '${c}')">${c}</button>`;
    });
    container.innerHTML = html;
}

// --- MODAL ---
function openModal(id) {
    const b = db.find(x => x.id === id);
    if (!b) return;
    
    document.getElementById('mImg').src = b.image || '';
    document.getElementById('mTitle').innerText = b.title;
    document.getElementById('mAuth').innerText = b.author || getText('Unknown', 'অজ্ঞাত');
    document.getElementById('mCat').innerText = b.category;
    document.getElementById('mRead').href = b.link;
    
    document.getElementById('modal').classList.add('active');
}

function closeModal(e) {
    // Close if clicked on backdrop or button
    if (!e || e.target === document.getElementById('modal') || e.target.classList.contains('modal-close')) {
        document.getElementById('modal').classList.remove('active');
    }
}

// --- UTILITIES ---
function toggleSave(e, id) {
    e.stopPropagation();
    if (saved.includes(id)) saved = saved.filter(x => x !== id);
    else saved.push(id);
    localStorage.setItem('saved', JSON.stringify(saved));
    
    if (currentTab === 'save') {
        renderBooks(db.filter(b => saved.includes(b.id)), getText('Saved Books', 'সংরক্ষিত বই'));
    } else {
        // Re-render to update icon state
        e.target.classList.toggle('active');
    }
}

function shareBook() {
    // In a real app, copy link. For now just toast.
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

// --- LANGUAGE TOGGLE SYSTEM ---
function toggleLanguage() {
    currentLang = currentLang === 'bn' ? 'en' : 'bn';
    localStorage.setItem('lang', currentLang);
    location.reload(); // Simple reload to apply changes globally
}

function applyLanguage() {
    document.documentElement.lang = currentLang;
    
    // Find all elements with data-en and data-bn attributes
    document.querySelectorAll('[data-en]').forEach(el => {
        el.innerText = el.getAttribute(`data-${currentLang}`);
    });
    
    // Update Placeholder
    const searchInput = document.getElementById('search');
    if (searchInput) {
        searchInput.placeholder = currentLang === 'en' ? 'Search books, authors...' : 'বই, লেখক বা বিষয় খুঁজুন...';
    }
}

// Helper to get text based on current lang
function getText(en, bn) {
    return currentLang === 'en' ? en : bn;
}

// Mobile Menu
function toggleMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    menu.classList.toggle('active');
}