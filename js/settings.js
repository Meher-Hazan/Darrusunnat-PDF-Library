// =========================================
//  SETTINGS & CONFIGURATION
// =========================================

const CONFIG = {
    dbUrl: 'books_data.json?t=' + Date.now(), 
    displayLimit: 24,
    groupLink: 'https://t.me/SobBoiErPdf' // Change this to your actual chat group link
};

let db = [];
let saved = JSON.parse(localStorage.getItem('saved')) || [];
let currentLang = localStorage.getItem('lang') || 'bn';
let currentTab = 'home';
let viewMode = localStorage.getItem('viewMode') || 'grid'; // New state
let searchTimeout;

const TRANSLATIONS = {
    en: {
        home: "Home",
        az: "A-Z Index",
        authors: "Authors",
        subjects: "Subjects",
        saved: "Saved Books",
        searchPlaceholder: "Search books, authors...",
        readNow: "Read Now",
        share: "Share",
        comment: "Comment",
        unknown: "Unknown",
        general: "General",
        noBooks: "No books found.",
        loadMore: "Load More",
        others: "Others",
        booksCount: "Books",
        results: "Search Results",
        viewGrid: "Grid View",
        viewList: "List View",
        random: "Random Book"
    },
    bn: {
        home: "হোম",
        az: "বর্ণানুক্রমিক",
        authors: "লেখক",
        subjects: "বিষয়",
        saved: "সংরক্ষিত বই",
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
        results: "অনুসন্ধান ফলাফল",
        viewGrid: "গ্রিড ভিউ",
        viewList: "লিস্ট ভিউ",
        random: "র‍্যান্ডম বই"
    }
};

function getText(key, fallback) {
    if (TRANSLATIONS[currentLang] && TRANSLATIONS[currentLang][key]) {
        return TRANSLATIONS[currentLang][key];
    }
    return fallback;
}