let db = [];

document.addEventListener('DOMContentLoaded', () => {
    // 1. Setup Link
    document.getElementById('navJoin').href = CONFIG.channel;
    
    // 2. Load Data
    fetch(CONFIG.dbUrl).then(r=>r.json()).then(data => {
        db = data.sort((a,b) => b.id - a.id);
        render(db.slice(0, CONFIG.limit));
    });
});

function render(list) {
    const grid = document.getElementById('grid');
    if(!list.length) { grid.innerHTML = '<div style="grid-column:1/-1; text-align:center;">No books found.</div>'; return; }
    
    grid.innerHTML = list.map(b => `
        <div class="book" onclick="openModal(${b.id})">
            <div class="cover-wrap">
                <img src="${b.image || 'https://via.placeholder.com/300x450'}" class="cover-img" loading="lazy">
            </div>
            <div class="book-title">${b.title}</div>
        </div>
    `).join('');
}

function handleSearch(e) {
    const q = e.value.toLowerCase();
    const res = db.filter(b => b.title.toLowerCase().includes(q) || (b.author && b.author.toLowerCase().includes(q)));
    render(res);
}

function openModal(id) {
    const b = db.find(x => x.id === id);
    if(!b) return;
    document.getElementById('mImg').src = b.image;
    document.getElementById('mTitle').innerText = b.title;
    document.getElementById('mRead').href = b.link;
    document.getElementById('mComment').href = CONFIG.group;
    document.getElementById('modal').classList.add('active');
}

function closeModal() { document.getElementById('modal').classList.remove('active'); }