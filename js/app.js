// =========================================
//  DARRUSUNNAT LIBRARY - FINAL LOGIC
// =========================================

fetch(CONFIG.dbUrl)
    .then(res => res.json())
    .then(data => {
        // Sort books by ID (Newest first)
        db = data.sort((a, b) => b.id - a.id);
        
        // Initialize View
        window.history.replaceState({view: 'home'}, '', '');
        setTab('home', false);
        startClock();
        updateViewIcon();
        renderChips();
    })
    .catch(() => {
        document.getElementById('app').innerHTML = "<div class='loading'>ডেটা লোড হয়নি। দয়া করে পেজটি রিফ্রেশ করুন।</div>";
    });

// --- CLOCK WIDGET ---
function startClock() {
    setInterval(() => {
        const d = new Date();
        const t = d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
        const date = d.toLocaleDateString('bn-BD');
        
        if(document.getElementById('mobTime')) document.getElementById('mobTime').innerText = t;
        if(document.getElementById('pcTime')) document.getElementById('pcTime').innerText = t;
    }, 1000);
}

// --- CATEGORY CHIPS ---
function renderChips() {
    // These names match the 'EXTRA_CHANNELS' map in your Python script
    const chips = [
        'সব বই', 
        'তাফসির ও কুরআন', 
        'হাদিস ও সুন্নাহ', 
        'সিরাতুন্নবী (সা.)', 
        'ফিকহ ও ফতোয়া', 
        'ইতিহাস ও ঐতিহ্য', 
        'উপন্যাস ও সাহিত্য', 
        'নারী ও পর্দা', 
        'আকিদা ও বিশ্বাস',
        'বিজ্ঞান ও ইসলাম',
        'হোমিওপ্যাথিক চিকিৎসা',
        'ফুরফুরা শরীফ লাইব্রেরি',
        'ইলমে তাসাওউফ',
        'সালাত (নামায)',
        'সাওম (রোযা)',
        'দরূদ শরীফ',
        'আরবি ভাষা ও সাহিত্য'
    ];
    
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
        // Use Fuzzy Search to match category names accurately
        const fuse = new Fuse(db, { keys: ['category'], threshold: 0.3 });
        const results = fuse.search(cat).map(r => r.item);
        currentList = results;
        renderBooks(results, `${cat}`);
    }
}

// --- NAVIGATION ENGINE ---
function setTab(tab, pushHist = true) {
    if(pushHist) window.history.pushState({view: tab}, '', '');
    currentTab = tab;
    CONFIG.displayLimit = 24;
    
    // Update Menu Highlights
    document.querySelectorAll('.pc-link, .nav-item').forEach(el => el.classList.remove('active'));
    if(document.getElementById('pc-'+tab)) document.getElementById('pc-'+tab).classList.add('active');
    if(document.getElementById('mob-'+tab)) document.getElementById('mob-'+tab).classList.add('active');
    
    // Show/Hide Dashboard & Chips
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

    // Route Logic
    if (tab === 'home') {
        currentList = db;
        renderBooks(db.slice(0, CONFIG.displayLimit));
    } else if (tab === 'save') {
        renderBooks(db.filter(b => saved.includes(b.id)), "সংরক্ষিত বই");
    } else if (tab === 'az') renderFolders('az');
    else if (tab === 'auth') renderFolders('author');
    else if (tab === 'cat') renderFolders('category'); // Displays Channel Names as Folders
}

// Browser Back Button Handler
window.onpopstate = function(event) {
    if (event.state) {
        // Close Modal if Open
        if (document.getElementById('modal').classList.contains('active')) {
            document.getElementById('modal').classList.remove('active');
            return;
        }
        // Navigate Back
        if(event.state.view === 'folder') openFolder(event.state.type, event.state.key, false);
        else if (event.state.view) setTab(event.state.view, false);
        else setTab('home', false);
    }
};

function handleSearch() {
    const q = document.getElementById('search').value;
    clearTimeout(searchTimeout);
    
    // Debounce to prevent lag
    searchTimeout = setTimeout(() => {
        if(!q) { 
            if(currentTab === 'home') renderBooks(db.slice(0, CONFIG.displayLimit)); 
            return; 
        }
        const fuse = new Fuse(db, { keys: ['title', 'author', 'category'], threshold: 0.3 });
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
        const clickFn = `openModal(${b.id})`;
        const saveFn = `toggleSave(event, ${b.id})`;
        
        // Show Channel/Category Badge
        const categoryBadge = `<span style="font-size:0.65rem; color:#aaa; display:block; margin-top:3px;">📁 ${b.category}</span>`;
        
        if (viewMode === 'grid') {
            html += `
            <div class="card" onclick="${clickFn}">
                <div class="save-btn ${isSaved}" onclick="${saveFn}"><i class="fas fa-bookmark"></i></div>
                <div class="card-img-wrap"><img src="${img}" class="card-img" loading="lazy"></div>
                <div class="card-info">
                    <div class="card-title">${b.title}</div>
                    <div class="card-cat">${b.author || 'অজ্ঞাত'}</div>
                    ${categoryBadge}
                </div>
            </div>`;
        } else {
            html += `
            <div class="list-item" onclick="${clickFn}">
                <img src="${img}" class="list-thumb" loading="lazy">
                <div class="list-data">
                    <div class="list-title">${b.title}</div>
                    <div class="list-cat">${b.author || 'অজ্ঞাত'}</div>
                    ${categoryBadge}
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

// --- FOLDER SYSTEM ---
function renderFolders(type) {
    const groups = {};
    db.forEach(b => {
        let key = b[type] || 'অন্যান্য';
        if(type === 'az') key = b.title.charAt(0).toUpperCase();
        if(!groups[key]) groups[key] = 0; groups[key]++;
    });
    
    const keys = Object.keys(groups).sort();
    let html = '<div class="folder-grid">';
    
    keys.forEach(k => {
        let icon = k.charAt(0);
        if(type === 'cat') icon = '📁';
        if(type === 'auth') icon = '✒️';
        if(type === 'az') icon = k;

        html += `<div class="folder" onclick="openFolder('${type}', '${k}')">
            <div class="folder-icon">${icon}</div>
            <div class="folder-label">${k}</div>
            <div class="folder-count">${groups[k]} টি বই</div>
        </div>`;
    });
    html += '</div>';
    document.getElementById('app').innerHTML = html;
}

function openFolder(type, key, pushHist = true) {
    if(pushHist) window.history.pushState({view: 'folder', type: type, key: key}, '', '');
    
    let list = db.filter(b => {
        if(type === 'az') return b.title.charAt(0).toUpperCase() === key;
        return b[type] === key;
    });
    
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
    
    if(currentTab === 'save') renderBooks(db.filter(b => saved.includes(b.id)), "সংরক্ষিত বই");
    else e.target.classList.toggle('active');
}

function toggleView() {
    viewMode = viewMode === 'grid' ? 'list' : 'grid';
    localStorage.setItem('viewMode', viewMode);
    updateViewIcon();
    
    if(document.querySelector('.grid') || document.querySelector('.list-view')) {
        if(document.getElementById('search').value) handleSearch();
        else if(currentTab === 'home') renderBooks(db.slice(0, CONFIG.displayLimit));
        else if(currentTab === 'save') renderBooks(db.filter(b => saved.includes(b.id)), "সংরক্ষিত বই");
    }
}

function updateViewIcon() {
    const icon = viewMode === 'grid' ? '<i class="fas fa-list"></i>' : '<i class="fas fa-th-large"></i>';
    if(document.getElementById('headerViewBtn')) document.getElementById('headerViewBtn').innerHTML = icon;
}

function openModal(id) {
    const b = db.find(x => x.id === id);
    if(!b) return;
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

function shareBook() { 
    navigator.clipboard.writeText(currentLink); 
    showToast(); 
}

function showToast() { 
    const x = document.getElementById("toast"); 
    x.className = "toast show"; 
    setTimeout(function(){ x.className = x.className.replace("show", ""); }, 3000); 
}

function joinGroup() { window.open(CONFIG.groupLink); }

function openRandom() { 
    if(db.length) openModal(db[Math.floor(Math.random() * db.length)].id); 
}

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