// =========================================
//  DARRUSUNNAT LIBRARY - MAIN LOGIC
// =========================================

// STARTUP
fetch(CONFIG.dbUrl)
    .then(res => res.json())
    .then(data => {
        // Sort by ID (Newest first)
        db = data.sort((a, b) => b.id - a.id);
        
        // Initialize History State
        window.history.replaceState({view: 'home'}, '', '');
        
        setTab('home', false); // Initial load
        startClock();
        updateViewIcon();
        renderChips();
    })
    .catch(() => {
        document.getElementById('app').innerHTML = "<div class='loading'>ডেটা লোড হয়নি। দয়া করে রিফ্রেশ করুন।</div>";
    });

// --- CLOCK WIDGET ---
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

// --- CATEGORY CHIPS ---
function renderChips() {
    // You can add more specific categories here if you want
    const chips = ['সব বই', 'তাফসির', 'হাদিস', 'আকিদা', 'ফিকহ', 'ইতিহাস', 'সিরাত', 'উপন্যাস', 'নারী ও পর্দা', 'অন্যান্য'];
    const container = document.getElementById('chipContainer');
    if(!container) return;
    
    let html = '';
    chips.forEach(c => {
        html += `<div class="chip" onclick="filterByChip('${c}')">${c}</div>`;
    });
    container.innerHTML = html;
}

function filterByChip(cat) {
    window.scrollTo(0, 0);
    if(cat === 'সব বই') {
        currentList = db;
        renderBooks(db.slice(0, CONFIG.displayLimit), "সব বই");
    } else {
        const fuse = new Fuse(db, { keys: ['category'], threshold: 0.3 });
        const results = fuse.search(cat).map(r => r.item);
        currentList = results;
        renderBooks(results, `${cat} বিভাগের বই`);
    }
}

// --- NAVIGATION ENGINE ---
function setTab(tab, pushToHistory = true) {
    currentTab = tab;
    CONFIG.displayLimit = 24;
    
    // Update Browser History
    if(pushToHistory) {
        window.history.pushState({view: tab}, '', '');
    }
    
    // Update Active UI States
    document.querySelectorAll('.pc-link, .nav-item').forEach(el => el.classList.remove('active'));
    if(document.getElementById('pc-'+tab)) document.getElementById('pc-'+tab).classList.add('active');
    if(document.getElementById('mob-'+tab)) document.getElementById('mob-'+tab).classList.add('active');
    
    // Toggle Hero Section (Only show on Home)
    const hero = document.getElementById('heroSection');
    const chips = document.getElementById('chipContainer');
    
    if(tab === 'home') {
        hero.style.display = 'flex';
        if(chips) chips.style.display = 'flex';
        document.getElementById('search').value = "";
    } else {
        hero.style.display = 'none';
        if(chips) chips.style.display = 'none';
    }
    
    window.scrollTo(0, 0);

    // Route to correct renderer
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

// Browser Back Button Handler
window.onpopstate = function(event) {
    if (event.state) {
        // If modal is open, close it without changing page
        if (document.getElementById('modal').classList.contains('active')) {
            document.getElementById('modal').classList.remove('active');
            return;
        }

        if(event.state.view === 'folder') {
            openFolder(event.state.type, event.state.key, false);
        } else if (event.state.view) {
            setTab(event.state.view, false);
        } else {
            setTab('home', false);
        }
    }
};

function goBack() {
    if(historyStack.length > 0) setTab(historyStack.pop(), false);
    else window.history.back(); // Use browser back
}

// --- SEARCH ENGINE ---
function handleSearch() {
    const q = document.getElementById('search').value;
    
    // Debouncing (Wait 300ms before searching to stop lag)
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        if(!q) { 
            if(currentTab === 'home') renderBooks(db.slice(0, CONFIG.displayLimit)); 
            return; 
        }
        
        // Search across Title, Author, Category, and Source
        const fuse = new Fuse(db, { keys: ['title', 'author', 'category', 'source'], threshold: 0.3 });
        const results = fuse.search(q).map(r => r.item);
        currentList = results;
        renderBooks(results, `অনুসন্ধান: "${q}"`);
    }, 300);
}

// --- BOOK RENDERER ---
function renderBooks(list, title = '') {
    const app = document.getElementById('app');
    if(!list.length) { app.innerHTML = "<div class='loading'>কোনো বই পাওয়া যায়নি 😕</div>"; return; }

    let html = title ? `<h2 class='sec-title'>${title}</h2>` : '';
    html += viewMode === 'grid' ? '<div class="grid">' : '<div class="list-view">';
    
    list.forEach(b => {
        const img = b.image || 'https://via.placeholder.com/300x450/0f4c3a/ffffff?text=Book';
        const isSaved = saved.includes(b.id) ? 'active' : '';
        
        // If book has a specific source (not the main channel), show it
        const sourceTag = b.source ? `<div style="font-size:0.65rem; color:var(--gold-dim); margin-top:2px;">📍 ${b.source}</div>` : '';
        
        const clickFn = `openModal(${b.id})`;
        const saveFn = `toggleSave(event, ${b.id})`;
        
        if (viewMode === 'grid') {
            html += `
            <div class="card" onclick="${clickFn}">
                <div class="save-btn ${isSaved}" onclick="${saveFn}"><i class="fas fa-bookmark"></i></div>
                <div class="card-img-wrap"><img src="${img}" class="card-img" loading="lazy"></div>
                <div class="card-info">
                    <div class="card-title">${b.title}</div>
                    <div class="card-cat">${b.author || 'অজ্ঞাত'}</div>
                    ${sourceTag}
                </div>
            </div>`;
        } else {
            html += `
            <div class="list-item" onclick="${clickFn}">
                <img src="${img}" class="list-thumb" loading="lazy">
                <div class="list-data">
                    <div class="list-title">${b.title}</div>
                    <div class="list-cat">${b.author || 'অজ্ঞাত'} • ${b.category}</div>
                    ${sourceTag}
                </div>
            </div>`;
        }
    });
    html += '</div>';
    
    if(currentTab === 'home' && list.length < db.length && !document.getElementById('search').value) {
        html += `<button class="load-more" onclick="loadMore()">আরও দেখুন</button>`;
    }
    app.innerHTML = html;
}

// --- FOLDER SYSTEM (A-Z, Author, Category) ---
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
            // Optional: Skip unknown authors/categories to keep list clean
            if(key === 'অজ্ঞাত') return; 
        }
        if(!groups[key]) groups[key] = 0;
        groups[key]++;
    });

    const keys = Object.keys(groups).sort();
    let html = '<div class="folder-grid">';
    
    keys.forEach(k => {
        // Choose icon based on type
        let icon = k;
        if (type === 'auth') icon = '<i class="fas fa-pen-nib"></i>';
        if (type === 'cat') icon = '<i class="fas fa-book"></i>';
        
        html += `
        <div class="folder" onclick="openFolder('${type}', '${k}')">
            <div class="folder-icon">${type === 'az' ? k : icon}</div>
            <div class="folder-label">${k}</div>
            <div class="folder-count">${groups[k]} টি বই</div>
        </div>`;
    });
    html += '</div>';
    document.getElementById('app').innerHTML = html;
}

function openFolder(type, key, pushHist = true) {
    if(pushHist) {
        window.history.pushState({view: 'folder', type: type, key: key}, '', '');
    }

    let list = [];
    if(type === 'az') {
        list = db.filter(b => {
            const clean = b.title.replace(/^[\d\s\.\-\_\#\(\)\[\]]+/, '').trim();
            const match = clean.match(/^[a-zA-Z\u0980-\u09FF\u0600-\u06FF]/);
            return match && match[0].toUpperCase() === key;
        });
    } else {
        list = db.filter(b => b[type] === key);
    }
    
    const backBtn = `<div class="back-bar" onclick="window.history.back()"><i class="fas fa-arrow-left"></i> পেছনে যান</div>`;
    renderBooks(list, `${backBtn}<br>${key}`);
    window.scrollTo(0,0);
}

// --- UTILITIES ---
function loadMore() {
    CONFIG.displayLimit += 24;
    renderBooks(db.slice(0, CONFIG.displayLimit));
}

function toggleSave(e, id) {
    e.stopPropagation();
    if(saved.includes(id)) saved = saved.filter(x => x !== id);
    else saved.push(id);
    localStorage.setItem('saved', JSON.stringify(saved));
    
    // Refresh only if in saved tab
    if(currentTab === 'save') {
        renderBooks(db.filter(b => saved.includes(b.id)), "সংরক্ষিত বই");
    } else {
        e.target.classList.toggle('active');
    }
}

function toggleView() {
    viewMode = viewMode === 'grid' ? 'list' : 'grid';
    localStorage.setItem('viewMode', viewMode);
    updateViewIcon();
    
    // Re-render current view
    if(document.querySelector('.grid') || document.querySelector('.list-view')) {
        const title = document.querySelector('.sec-title')?.innerText || '';
        if(document.getElementById('search').value) handleSearch();
        else if(currentTab === 'home') renderBooks(db.slice(0, CONFIG.displayLimit));
        else if(currentTab === 'save') renderBooks(db.filter(b => saved.includes(b.id)), "সংরক্ষিত বই");
    }
}

function updateViewIcon() {
    const icon = viewMode === 'grid' ? '<i class="fas fa-list"></i>' : '<i class="fas fa-th-large"></i>';
    if(document.getElementById('headerViewBtn')) document.getElementById('headerViewBtn').innerHTML = icon;
}

// --- MODAL POPUP ---
function openModal(id) {
    const b = db.find(x => x.id === id);
    if(!b) return;
    
    currentLink = b.link;
    document.getElementById('mImg').src = b.image || '';
    document.getElementById('mTitle').innerText = b.title;
    document.getElementById('mAuth').innerText = b.author || 'অজ্ঞাত';
    document.getElementById('mRead').href = b.link;
    
    // Push history state to allow back button to close modal
    window.history.pushState({modal: true}, null, "");
    document.getElementById('modal').classList.add('active');
}

function closeModal() {
    document.getElementById('modal').classList.remove('active');
    // Go back in history to remove the modal state
    if(history.state && history.state.modal) history.back();
}

// --- SHARING ---
function shareBook() {
    navigator.clipboard.writeText(currentLink);
    showToast();
}

function showToast() {
    const x = document.getElementById("toast");
    x.className = "toast show";
    setTimeout(function(){ x.className = x.className.replace("show", ""); }, 3000);
}

function joinGroup() {
    window.open(CONFIG.groupLink);
}

// --- RANDOM BOOK ---
function openRandom() {
    if(db.length) openModal(db[Math.floor(Math.random() * db.length)].id);
}

// --- BACK TO TOP BUTTON ---
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