// =========================================
//  SETTINGS & CONFIGURATION
// =========================================

// 1. Core Configuration
const CONFIG = {
    // Adds a timestamp to force fresh data load every time
    dbUrl: 'books_data.json?t=' + Date.now(), 
    displayLimit: 24,
    groupLink: 'https://t.me/SobBoiErPdf'
};

// 2. Global State Variables
let db = []; // Will hold all books
let saved = JSON.parse(localStorage.getItem('saved')) || [];
let currentLang = localStorage.getItem('lang') || 'bn'; // Default to Bengali
let currentTab = 'home';
let searchTimeout;

// 3. Translation Dictionary
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
        unknown: "Unknown",
        general: "General",
        noBooks: "No books found.",
        loadMore: "Load More",
        others: "Others",
        booksCount: "Books",
        results: "Search Results"
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
        unknown: "অজ্ঞাত",
        general: "সাধারণ",
        noBooks: "কোনো বই পাওয়া যায়নি।",
        loadMore: "আরও দেখুন",
        others: "অন্যান্য",
        booksCount: "টি বই",
        results: "অনুসন্ধান ফলাফল"
    }
};

// 4. Helper to get text
function getText(key, fallback) {
    if (TRANSLATIONS[currentLang] && TRANSLATIONS[currentLang][key]) {
        return TRANSLATIONS[currentLang][key];
    }
    return fallback;
}