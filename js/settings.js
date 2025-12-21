// =========================================
//  SETTINGS & CONFIGURATION
// =========================================

const CONFIG = {
    dbUrl: 'books_data.json?t=' + Date.now(), 
    displayLimit: 24,
    // 🔥 UPDATED LINK TO GROUP 🔥
    groupLink: 'https://t.me/Darussunnat_Library' 
};

let db = [];
let saved = JSON.parse(localStorage.getItem('saved')) || [];
let currentLang = localStorage.getItem('lang') || 'bn';
let currentTab = 'home';
let viewMode = localStorage.getItem('viewMode') || 'grid';
let searchTimeout;

const TRANSLATIONS = {
    en: {
        home: "Home",
        az: "A-Z",
        authors: "Authors",
        subjects: "Subjects",
        saved: "Saved",
        searchPlaceholder: "Search...",
        readNow: "Read Now",
        share: "Share",
        comment: "Comment",
        unknown: "Unknown",
        general: "General",
        noBooks: "No books found.",
        loadMore: "Load More",
        others: "Others",
        booksCount: "Books",
        results: "Results",
        viewGrid: "Grid",
        viewList: "List",
        random: "Random"
    },
    bn: {
        home: "হোম",
        az: "বর্ণানুক্রমিক",
        authors: "লেখক",
        subjects: "বিষয়",
        saved: "সংরক্ষিত",
        searchPlaceholder: "বই, লেখক বা বিষয় খুঁজুন...",
        readNow: "পড়ুন",
        share: "শেয়ার",
        comment: "মন্তব্য করুন",
        unknown: "অজ্ঞাত",
        general: "সাধারণ",
        noBooks: "কোনো বই পাওয়া যায়নি।",
        loadMore: "আরও দেখুন",
        others: "অন্যান্য",
        booksCount: "টি বই",
        results: "ফলাফল",
        viewGrid: "গ্রিড",
        viewList: "লিস্ট",
        random: "র‍্যান্ডম"
    }
};

function getText(key, fallback) {
    if (TRANSLATIONS[currentLang] && TRANSLATIONS[currentLang][key]) {
        return TRANSLATIONS[currentLang][key];
    }
    return fallback;
}