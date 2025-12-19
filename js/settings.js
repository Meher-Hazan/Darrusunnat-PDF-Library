// Settings File - Change these values easily
const CONFIG = {
    displayLimit: 24,
    dbUrl: 'books_data.json?t=' + Date.now(),
    telegramLink: 'https://t.me/SobBoiErPdf',
    groupLink: 'https://t.me/IslamicBooks_us'
};

// Global State
let db = [];
let saved = JSON.parse(localStorage.getItem('saved')) || [];
let viewMode = localStorage.getItem('viewMode') || 'grid';
let currentTab = 'home';
let currentList = [];
let currentLink = "";
let historyStack = [];
let searchTimeout = null;
