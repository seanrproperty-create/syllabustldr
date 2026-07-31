// Mirrors LANG_ORDER / LANG_META in gen_i18n.py (project root). Kept as a
// separate hand-synced copy because that file is Python and this pipeline
// is Node — if you add a language to one, add it to the other.

const LANG_ORDER = ['en', 'es', 'fr', 'pt', 'zh', 'de', 'hi', 'ar', 'ko', 'vi'];

const LANG_META = {
  en: { hreflang: 'en',      homePrefix: '',    name: 'English',    og_locale: 'en_US', dir: 'ltr', googleCode: 'en' },
  es: { hreflang: 'es',      homePrefix: '/es',  name: 'Español',    og_locale: 'es_ES', dir: 'ltr', googleCode: 'es' },
  fr: { hreflang: 'fr',      homePrefix: '/fr',  name: 'Français',   og_locale: 'fr_FR', dir: 'ltr', googleCode: 'fr' },
  pt: { hreflang: 'pt',      homePrefix: '/pt',  name: 'Português',  og_locale: 'pt_BR', dir: 'ltr', googleCode: 'pt' },
  zh: { hreflang: 'zh-Hans', homePrefix: '/zh',  name: '中文',        og_locale: 'zh_CN', dir: 'ltr', googleCode: 'zh-CN' },
  de: { hreflang: 'de',      homePrefix: '/de',  name: 'Deutsch',    og_locale: 'de_DE', dir: 'ltr', googleCode: 'de' },
  hi: { hreflang: 'hi',      homePrefix: '/hi',  name: 'हिन्दी',      og_locale: 'hi_IN', dir: 'ltr', googleCode: 'hi' },
  ar: { hreflang: 'ar',      homePrefix: '/ar',  name: 'العربية',    og_locale: 'ar_AR', dir: 'rtl', googleCode: 'ar' },
  ko: { hreflang: 'ko',      homePrefix: '/ko',  name: '한국어',      og_locale: 'ko_KR', dir: 'ltr', googleCode: 'ko' },
  vi: { hreflang: 'vi',      homePrefix: '/vi',  name: 'Tiếng Việt', og_locale: 'vi_VN', dir: 'ltr', googleCode: 'vi' },
};

const SITE_ORIGIN = 'https://syllabustldr.com';

function articleUrl(lang, slug) {
  return `${SITE_ORIGIN}${LANG_META[lang].homePrefix}/blog/${slug}/`;
}

function homeUrl(lang) {
  return `${SITE_ORIGIN}${LANG_META[lang].homePrefix}/`;
}

export { LANG_ORDER, LANG_META, SITE_ORIGIN, articleUrl, homeUrl };
