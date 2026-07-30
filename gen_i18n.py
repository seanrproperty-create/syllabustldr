#!/usr/bin/env python3
"""
Generates /es/, /fr/, /pt/, /zh/, /de/, /hi/, /ar/, /ko/, /vi/ index.html files
from the canonical English index.html (this project's single-page app), and
regenerates index.html's own hreflang block + language switcher to include
all 10 languages.

How it works (matches the pattern already used for es/fr/pt/zh before this
script was rebuilt from scratch — see CLAUDE session notes):
  1. The parser engine block — from `const GRADE_KEYWORDS` down to (but not
     including) `function renderDashboard` — is excised from the master
     template BEFORE any text replacement happens, and spliced back in
     byte-identical at the end. This block must always match English
     syllabus text regardless of UI language, so it is structurally
     impossible for the static-replace or T-injection steps to touch it.
  2. Every other static UI string (headings, buttons, placeholders, footer
     links, the cookie-consent banner, etc.) is swapped via literal
     find-and-replace, using the EXISTING_STATIC_* / NEW_STATIC_* tables
     below.
  3. A translated `window.T = {...}` object is injected right before the
     shared engine's <script> tag (after the consent-banner script), so
     `window.T = window.T || {...}` inside the shared script becomes a
     no-op and the translated object wins.
  4. The hreflang <link> block and the language-switcher <a> menu are fully
     regenerated (not string-replaced) from LANG_META, for every language
     including English itself, so adding a language only means adding one
     LANG_META entry + one translation table entry.

Run: python gen_i18n.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
MASTER = ROOT / 'index.html'

LANG_ORDER = ['en', 'es', 'fr', 'pt', 'zh', 'de', 'hi', 'ar', 'ko', 'vi']

LANG_META = {
    'en': {'hreflang': 'en',      'home': '/',     'flag': '🇺🇸', 'name': 'English',     'og_locale': 'en_US', 'dir': 'ltr'},
    'es': {'hreflang': 'es',      'home': '/es/',  'flag': '🇪🇸', 'name': 'Español',     'og_locale': 'es_ES', 'dir': 'ltr'},
    'fr': {'hreflang': 'fr',      'home': '/fr/',  'flag': '🇫🇷', 'name': 'Français',    'og_locale': 'fr_FR', 'dir': 'ltr'},
    'pt': {'hreflang': 'pt',      'home': '/pt/',  'flag': '🇧🇷', 'name': 'Português',   'og_locale': 'pt_BR', 'dir': 'ltr'},
    'zh': {'hreflang': 'zh-Hans', 'home': '/zh/',  'flag': '🇨🇳', 'name': '中文',         'og_locale': 'zh_CN', 'dir': 'ltr'},
    'de': {'hreflang': 'de',      'home': '/de/',  'flag': '🇩🇪', 'name': 'Deutsch',     'og_locale': 'de_DE', 'dir': 'ltr'},
    'hi': {'hreflang': 'hi',      'home': '/hi/',  'flag': '🇮🇳', 'name': 'हिन्दी',      'og_locale': 'hi_IN', 'dir': 'ltr'},
    'ar': {'hreflang': 'ar',      'home': '/ar/',  'flag': '🇸🇦', 'name': 'العربية',     'og_locale': 'ar_AR', 'dir': 'rtl'},
    'ko': {'hreflang': 'ko',      'home': '/ko/',  'flag': '🇰🇷', 'name': '한국어',       'og_locale': 'ko_KR', 'dir': 'ltr'},
    'vi': {'hreflang': 'vi',      'home': '/vi/',  'flag': '🇻🇳', 'name': 'Tiếng Việt',  'og_locale': 'vi_VN', 'dir': 'ltr'},
}

PROTECTED_START_RE = re.compile(r'^  const GRADE_KEYWORDS', re.M)
PROTECTED_END_RE = re.compile(r'^  function renderDashboard', re.M)

# ---------------------------------------------------------------------------
# FLAG_SVGS — small inline flag icons (viewBox 0 0 20 14), used instead of
# Unicode flag emoji. Windows Chrome/Edge has no color-flag glyphs and falls
# back to showing the raw two-letter region code as text (e.g. "US", "ES")
# instead of a flag — these render identically on every OS since they're
# plain SVG shapes baked into the page, no font or network dependency.
# ---------------------------------------------------------------------------
FLAG_SVGS = {
    'en': '<svg viewBox="0 0 20 14" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#B22234"/><rect y="1.08" width="20" height="1.08" fill="#fff"/><rect y="3.23" width="20" height="1.08" fill="#fff"/><rect y="5.38" width="20" height="1.08" fill="#fff"/><rect y="7.54" width="20" height="1.08" fill="#fff"/><rect y="9.69" width="20" height="1.08" fill="#fff"/><rect y="11.85" width="20" height="1.08" fill="#fff"/><rect width="8" height="7.54" fill="#3C3B6E"/></svg>',
    'es': '<svg viewBox="0 0 20 14" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#AA151B"/><rect y="3.5" width="20" height="7" fill="#F1BF00"/></svg>',
    'fr': '<svg viewBox="0 0 20 14" xmlns="http://www.w3.org/2000/svg"><rect width="6.67" height="14" fill="#0055A4"/><rect x="6.67" width="6.67" height="14" fill="#fff"/><rect x="13.33" width="6.67" height="14" fill="#EF4135"/></svg>',
    'pt': '<svg viewBox="0 0 20 14" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#009739"/><polygon points="10,1.5 18,7 10,12.5 2,7" fill="#FEDD00"/><circle cx="10" cy="7" r="3.2" fill="#012169"/></svg>',
    'zh': '<svg viewBox="0 0 20 14" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#DE2910"/><polygon points="4,2 4.7,3.9 6.7,3.9 5.1,5.1 5.7,7 4,5.8 2.3,7 2.9,5.1 1.3,3.9 3.3,3.9" fill="#FFDE00"/></svg>',
    'de': '<svg viewBox="0 0 20 14" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="4.67" fill="#000"/><rect y="4.67" width="20" height="4.67" fill="#DD0000"/><rect y="9.33" width="20" height="4.67" fill="#FFCE00"/></svg>',
    'hi': '<svg viewBox="0 0 20 14" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="4.67" fill="#FF9933"/><rect y="4.67" width="20" height="4.67" fill="#fff"/><rect y="9.33" width="20" height="4.67" fill="#138808"/><circle cx="10" cy="7" r="1.6" fill="none" stroke="#000080" stroke-width="0.3"/></svg>',
    'ar': '<svg viewBox="0 0 20 14" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#006C35"/><rect y="9.5" width="20" height="1" fill="#fff"/></svg>',
    'ko': '<svg viewBox="0 0 20 14" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#fff"/><circle cx="10" cy="7" r="3.2" fill="#CD2E3A"/><path d="M10,3.8 a3.2,3.2 0 0,0 0,6.4 a1.6,1.6 0 0,1 0,-3.2 a1.6,1.6 0 0,0 0,-3.2 z" fill="#0047A0"/></svg>',
    'vi': '<svg viewBox="0 0 20 14" xmlns="http://www.w3.org/2000/svg"><rect width="20" height="14" fill="#DA251D"/><polygon points="10,3 10.9,5.8 13.9,5.8 11.5,7.5 12.4,10.3 10,8.6 7.6,10.3 8.5,7.5 6.1,5.8 9.1,5.8" fill="#FFFF00"/></svg>',
}
for _lang in ['en', 'es', 'fr', 'pt', 'zh', 'de', 'hi', 'ar', 'ko', 'vi']:
    assert _lang in FLAG_SVGS, f'missing FLAG_SVGS for {_lang}'

# ---------------------------------------------------------------------------
# EXISTING_STATIC_EN / EXISTING_STATIC_TR — the 45 UI strings that already
# had es/fr/pt/zh translations before this script was rebuilt. Extracted
# losslessly from the previously-generated es/fr/pt/zh/index.html files by
# diffing them against the pre-Milestone-1 English snapshot (git HEAD~1),
# then hand-translated for de/hi/ar/ko/vi following the same phrasing/tone.
# ---------------------------------------------------------------------------
EXISTING_STATIC_EN = [
    '<html lang="en">',
    '<title>SyllabusTLDR — Instantly Simplify Your Course Outline</title>',
    '<meta name="description" content="Drop your syllabus, get a pocket-sized dashboard. Grade weights, deadlines, and calendar sync in 2 seconds. 100% free, no login.">',
    '<meta property="og:title" content="SyllabusTLDR — Instantly Simplify Your Course Outline">',
    '<meta property="og:description" content="Drop your syllabus, get a pocket-sized dashboard. Grade weights, deadlines, and calendar sync in 2 seconds. 100% free, no login.">',
    '<meta property="og:url" content="https://syllabustldr.com/">',
    '<meta property="og:locale" content="en_US">',
    '            <a href="/" class="flex items-center gap-2.5">',
    '                    <p class="text-xs text-zinc-500">Zero logins • 2-second summary</p>',
    '                    100% Free',
    '                <h2 class="font-display text-3xl font-bold tracking-tight leading-tight">Drop the <span class="bg-gradient-to-r from-orange-400 to-pink-500 bg-clip-text text-transparent">Text Wall.</span></h2>',
    '                <p class="text-zinc-400 text-sm max-w-xs mx-auto text-pretty">Convert complex multi-page syllabi into a clean, pocket-sized dashboard instantly.</p>',
    '                        <p id="drop-title" class="font-bold text-sm">Upload Syllabus PDF</p>',
    '                        <p id="drop-subtitle" class="text-xs text-zinc-500 mt-1">Tap to select or drop file here</p>',
    '                <span class="px-3 text-[11px] text-zinc-500 font-semibold uppercase tracking-widest">OR PASTE TEXT</span>',
    '                <textarea id="paste-box" rows="5" class="w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-3.5 text-sm focus:outline-none focus:border-pink-500 focus:ring-4 focus:ring-pink-500/10 placeholder-zinc-600 text-zinc-200 transition" placeholder="Paste your messy syllabus text block here..."></textarea>',
    '                    <span>Simplify Instantly</span>',
    '                <p class="font-display font-bold text-lg text-zinc-100">Shredding the policy clauses...</p>',
    '                <p class="text-xs text-zinc-500">Isolating grade weights, rules and due dates</p>',
    '                    Sync to Calendar (.ics)',
    '                    Share Smart-Card',
    '                    <span class="text-[10px] font-bold tracking-[.15em] text-orange-400 uppercase">Course Snapshot</span>',
    '                    <h3 id="render-course-title" class="font-display text-lg font-bold text-white mt-0.5 tracking-tight">Loading Title...</h3>',
    '                <!-- Grade Weight Breakdown -->',
    '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Grade Weight Breakdown</span>',
    '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Core Milestones &amp; Deadlines</span>',
    '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Late Policies &amp; Contact</span>',
    '                        <p class="text-[10.5px] text-white/85 font-medium mt-0.5">Skip the text wall. Screenshot &amp; share ✂️</p>',
    '                        Sync to Calendar (.ics)',
    '                        Share Smart-Card',
    '                Clear and summarize another syllabus',
    '                <h3 class="font-display text-lg font-bold text-white">Add to Your Calendar</h3>',
    '                <button id="calendar-modal-close" aria-label="Close" class="w-8 h-8 rounded-full flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-800 transition">',
    '                    Apple Calendar / Other (.ics)',
    '            <a href="/terms-of-service.html" class="text-zinc-600 hover:text-zinc-400 transition">Terms of Service</a>',
    '            <a href="/privacy-policy.html" class="text-zinc-600 hover:text-zinc-400 transition">Privacy Policy</a>',
    '        <p class="text-[11px] text-zinc-600">© 2026 SyllabusTLDR • Built for fast mobile execution.</p>',
    "    dropTitleDefault: 'Upload Syllabus PDF',",
    "    dropSubtitleDefault: 'Tap to select or drop file here',",
    '    // There are two Share Smart-Card buttons on the page (one above the',
]

EXISTING_STATIC_TR = {
    'es': [
        '<html lang="es">',
        '<title>SyllabusTLDR — Simplifica tu Sílabo Universitario al Instante</title>',
        '<meta name="description" content="Sube tu sílabo y obtén un panel visual al instante: ponderaciones de calificación, fechas límite y sincronización con calendario en 2 segundos. 100% gratis, sin inicio de sesión.">',
        '<meta property="og:title" content="SyllabusTLDR — Simplifica tu Sílabo Universitario al Instante">',
        '<meta property="og:description" content="Sube tu sílabo y obtén un panel visual al instante: ponderaciones de calificación, fechas límite y sincronización con calendario en 2 segundos. 100% gratis, sin inicio de sesión.">',
        '<meta property="og:url" content="https://syllabustldr.com/es/">',
        '<meta property="og:locale" content="es_ES">',
        '            <a href="/es/" class="flex items-center gap-2.5">',
        '                    <p class="text-xs text-zinc-500">Sin inicio de sesión • Resumen en 2 segundos</p>',
        '                    100% Gratis',
        '                <h2 class="font-display text-3xl font-bold tracking-tight leading-tight">Olvídate del <span class="bg-gradient-to-r from-orange-400 to-pink-500 bg-clip-text text-transparent">Muro de Texto.</span></h2>',
        '                <p class="text-zinc-400 text-sm max-w-xs mx-auto text-pretty">Convierte sílabos complejos de varias páginas en un panel limpio y de bolsillo al instante.</p>',
        '                        <p id="drop-title" class="font-bold text-sm">Sube el PDF del Sílabo</p>',
        '                        <p id="drop-subtitle" class="text-xs text-zinc-500 mt-1">Toca para seleccionar o suelta el archivo aquí</p>',
        '                <span class="px-3 text-[11px] text-zinc-500 font-semibold uppercase tracking-widest">O PEGA EL TEXTO</span>',
        '                <textarea id="paste-box" rows="5" class="w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-3.5 text-sm focus:outline-none focus:border-pink-500 focus:ring-4 focus:ring-pink-500/10 placeholder-zinc-600 text-zinc-200 transition" placeholder="Pega aquí el texto desordenado de tu sílabo..."></textarea>',
        '                    <span>Simplificar al Instante</span>',
        '                <p class="font-display font-bold text-lg text-zinc-100">Analizando las cláusulas del curso...</p>',
        '                <p class="text-xs text-zinc-500">Aislando ponderaciones, reglas y fechas límite</p>',
        '                    Sincronizar con Calendario (.ics)',
        '                    Compartir Tarjeta',
        '                    <span class="text-[10px] font-bold tracking-[.15em] text-orange-400 uppercase">Resumen del Curso</span>',
        '                    <h3 id="render-course-title" class="font-display text-lg font-bold text-white mt-0.5 tracking-tight">Cargando título...</h3>',
        '                <!-- Ponderación de Calificaciones -->',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Ponderación de Calificaciones</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Hitos y Fechas Límite</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Políticas de Retraso y Contacto</span>',
        '                        <p class="text-[10.5px] text-white/85 font-medium mt-0.5">Olvídate del muro de texto. Captura y comparte ✂️</p>',
        '                        Sincronizar con Calendario (.ics)',
        '                        Compartir Tarjeta',
        '                Borrar y resumir otro sílabo',
        '                <h3 class="font-display text-lg font-bold text-white">Agregar a tu Calendario</h3>',
        '                <button id="calendar-modal-close" aria-label="Cerrar" class="w-8 h-8 rounded-full flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-800 transition">',
        '                    Calendario de Apple / Otro (.ics)',
        '            <a href="/terms-of-service.html" class="text-zinc-600 hover:text-zinc-400 transition">Términos de Servicio</a>',
        '            <a href="/privacy-policy.html" class="text-zinc-600 hover:text-zinc-400 transition">Política de Privacidad</a>',
        '        <p class="text-[11px] text-zinc-600">© 2026 SyllabusTLDR • Hecho para máxima velocidad móvil.</p>',
        "    dropTitleDefault: 'Sube el PDF del Sílabo',",
        "    dropSubtitleDefault: 'Toca para seleccionar o suelta el archivo aquí',",
        '    // There are two Compartir Tarjeta buttons on the page (one above the',
    ],
    'fr': [
        '<html lang="fr">',
        '<title>SyllabusTLDR — Simplifiez Votre Syllabus Universitaire Instantanément</title>',
        '<meta name="description" content="Déposez votre syllabus, obtenez un tableau de bord compact. Pondérations des notes, échéances et synchronisation du calendrier en 2 secondes. 100% gratuit, sans connexion.">',
        '<meta property="og:title" content="SyllabusTLDR — Simplifiez Votre Syllabus Universitaire Instantanément">',
        '<meta property="og:description" content="Déposez votre syllabus, obtenez un tableau de bord compact. Pondérations des notes, échéances et synchronisation du calendrier en 2 secondes. 100% gratuit, sans connexion.">',
        '<meta property="og:url" content="https://syllabustldr.com/fr/">',
        '<meta property="og:locale" content="fr_FR">',
        '            <a href="/fr/" class="flex items-center gap-2.5">',
        '                    <p class="text-xs text-zinc-500">Sans connexion • Résumé en 2 secondes</p>',
        '                    100% Gratuit',
        '                <h2 class="font-display text-3xl font-bold tracking-tight leading-tight">Oubliez le <span class="bg-gradient-to-r from-orange-400 to-pink-500 bg-clip-text text-transparent">Mur de Texte.</span></h2>',
        '                <p class="text-zinc-400 text-sm max-w-xs mx-auto text-pretty">Transformez un syllabus complexe de plusieurs pages en un tableau de bord clair et compact, instantanément.</p>',
        '                        <p id="drop-title" class="font-bold text-sm">Importer le PDF du Syllabus</p>',
        '                        <p id="drop-subtitle" class="text-xs text-zinc-500 mt-1">Touchez pour sélectionner ou déposez le fichier ici</p>',
        '                <span class="px-3 text-[11px] text-zinc-500 font-semibold uppercase tracking-widest">OU COLLEZ LE TEXTE</span>',
        '                <textarea id="paste-box" rows="5" class="w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-3.5 text-sm focus:outline-none focus:border-pink-500 focus:ring-4 focus:ring-pink-500/10 placeholder-zinc-600 text-zinc-200 transition" placeholder="Collez ici le texte brouillon de votre syllabus..."></textarea>',
        '                    <span>Simplifier Instantanément</span>',
        '                <p class="font-display font-bold text-lg text-zinc-100">Analyse des clauses du cours...</p>',
        '                <p class="text-xs text-zinc-500">Extraction des pondérations, règles et échéances</p>',
        '                    Synchroniser avec le Calendrier (.ics)',
        '                    Partager la Fiche',
        '                    <span class="text-[10px] font-bold tracking-[.15em] text-orange-400 uppercase">Aperçu du Cours</span>',
        '                    <h3 id="render-course-title" class="font-display text-lg font-bold text-white mt-0.5 tracking-tight">Chargement du titre...</h3>',
        '                <!-- Répartition des Notes -->',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Répartition des Notes</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Étapes Clés et Échéances</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Politique de Retard et Contact</span>',
        '                        <p class="text-[10.5px] text-white/85 font-medium mt-0.5">Oubliez le mur de texte. Capturez et partagez ✂️</p>',
        '                        Synchroniser avec le Calendrier (.ics)',
        '                        Partager la Fiche',
        '                Effacer et résumer un autre syllabus',
        '                <h3 class="font-display text-lg font-bold text-white">Ajouter à votre Calendrier</h3>',
        '                <button id="calendar-modal-close" aria-label="Fermer" class="w-8 h-8 rounded-full flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-800 transition">',
        '                    Calendrier Apple / Autre (.ics)',
        '            <a href="/terms-of-service.html" class="text-zinc-600 hover:text-zinc-400 transition">Conditions d\'Utilisation</a>',
        '            <a href="/privacy-policy.html" class="text-zinc-600 hover:text-zinc-400 transition">Politique de Confidentialité</a>',
        '        <p class="text-[11px] text-zinc-600">© 2026 SyllabusTLDR • Conçu pour une exécution mobile rapide.</p>',
        "    dropTitleDefault: 'Importer le PDF du Syllabus',",
        "    dropSubtitleDefault: 'Touchez pour sélectionner ou déposez le fichier ici',",
        '    // There are two Partager la Fiche buttons on the page (one above the',
    ],
    'pt': [
        '<html lang="pt">',
        '<title>SyllabusTLDR — Simplifique sua Ementa Universitária Instantaneamente</title>',
        '<meta name="description" content="Envie sua ementa e receba um painel visual na hora: pesos das notas, prazos e sincronização de calendário em 2 segundos. 100% grátis, sem login.">',
        '<meta property="og:title" content="SyllabusTLDR — Simplifique sua Ementa Universitária Instantaneamente">',
        '<meta property="og:description" content="Envie sua ementa e receba um painel visual na hora: pesos das notas, prazos e sincronização de calendário em 2 segundos. 100% grátis, sem login.">',
        '<meta property="og:url" content="https://syllabustldr.com/pt/">',
        '<meta property="og:locale" content="pt_BR">',
        '            <a href="/pt/" class="flex items-center gap-2.5">',
        '                    <p class="text-xs text-zinc-500">Sem login • Resumo em 2 segundos</p>',
        '                    100% Grátis',
        '                <h2 class="font-display text-3xl font-bold tracking-tight leading-tight">Chega de <span class="bg-gradient-to-r from-orange-400 to-pink-500 bg-clip-text text-transparent">Muro de Texto.</span></h2>',
        '                <p class="text-zinc-400 text-sm max-w-xs mx-auto text-pretty">Transforme ementas complexas de várias páginas em um painel limpo e compacto, instantaneamente.</p>',
        '                        <p id="drop-title" class="font-bold text-sm">Enviar PDF da Ementa</p>',
        '                        <p id="drop-subtitle" class="text-xs text-zinc-500 mt-1">Toque para selecionar ou solte o arquivo aqui</p>',
        '                <span class="px-3 text-[11px] text-zinc-500 font-semibold uppercase tracking-widest">OU COLE O TEXTO</span>',
        '                <textarea id="paste-box" rows="5" class="w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-3.5 text-sm focus:outline-none focus:border-pink-500 focus:ring-4 focus:ring-pink-500/10 placeholder-zinc-600 text-zinc-200 transition" placeholder="Cole aqui o texto bagunçado da sua ementa..."></textarea>',
        '                    <span>Simplificar Agora</span>',
        '                <p class="font-display font-bold text-lg text-zinc-100">Analisando as cláusulas do curso...</p>',
        '                <p class="text-xs text-zinc-500">Isolando pesos de notas, regras e prazos</p>',
        '                    Sincronizar com Calendário (.ics)',
        '                    Compartilhar Cartão',
        '                    <span class="text-[10px] font-bold tracking-[.15em] text-orange-400 uppercase">Resumo da Disciplina</span>',
        '                    <h3 id="render-course-title" class="font-display text-lg font-bold text-white mt-0.5 tracking-tight">Carregando título...</h3>',
        '                <!-- Distribuição das Notas -->',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Distribuição das Notas</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Marcos e Prazos Principais</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Política de Atraso e Contato</span>',
        '                        <p class="text-[10.5px] text-white/85 font-medium mt-0.5">Chega de muro de texto. Capture a tela e compartilhe ✂️</p>',
        '                        Sincronizar com Calendário (.ics)',
        '                        Compartilhar Cartão',
        '                Limpar e resumir outra ementa',
        '                <h3 class="font-display text-lg font-bold text-white">Adicionar ao seu Calendário</h3>',
        '                <button id="calendar-modal-close" aria-label="Fechar" class="w-8 h-8 rounded-full flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-800 transition">',
        '                    Calendário da Apple / Outro (.ics)',
        '            <a href="/terms-of-service.html" class="text-zinc-600 hover:text-zinc-400 transition">Termos de Serviço</a>',
        '            <a href="/privacy-policy.html" class="text-zinc-600 hover:text-zinc-400 transition">Política de Privacidade</a>',
        '        <p class="text-[11px] text-zinc-600">© 2026 SyllabusTLDR • Feito para máxima velocidade no celular.</p>',
        "    dropTitleDefault: 'Enviar PDF da Ementa',",
        "    dropSubtitleDefault: 'Toque para selecionar ou solte o arquivo aqui',",
        '    // There are two Compartilhar Cartão buttons on the page (one above the',
    ],
    'zh': [
        '<html lang="zh">',
        '<title>SyllabusTLDR — 秒懂教学大纲，即刻简化</title>',
        '<meta name="description" content="上传你的教学大纲，秒速生成口袋仪表盘：成绩权重、截止日期与日历同步，2秒完成。100% 免费，无需登录。">',
        '<meta property="og:title" content="SyllabusTLDR — 秒懂教学大纲，即刻简化">',
        '<meta property="og:description" content="上传你的教学大纲，秒速生成口袋仪表盘：成绩权重、截止日期与日历同步，2秒完成。100% 免费，无需登录。">',
        '<meta property="og:url" content="https://syllabustldr.com/zh/">',
        '<meta property="og:locale" content="zh_CN">',
        '            <a href="/zh/" class="flex items-center gap-2.5">',
        '                    <p class="text-xs text-zinc-500">无需登录 • 2秒生成摘要</p>',
        '                    100% 免费',
        '                <h2 class="font-display text-3xl font-bold tracking-tight leading-tight">告别<span class="bg-gradient-to-r from-orange-400 to-pink-500 bg-clip-text text-transparent">文字墙。</span></h2>',
        '                <p class="text-zinc-400 text-sm max-w-xs mx-auto text-pretty">瞬间将冗长复杂的多页教学大纲转换成简洁的口袋仪表盘。</p>',
        '                        <p id="drop-title" class="font-bold text-sm">上传教学大纲 PDF</p>',
        '                        <p id="drop-subtitle" class="text-xs text-zinc-500 mt-1">点击选择或将文件拖放到此处</p>',
        '                <span class="px-3 text-[11px] text-zinc-500 font-semibold uppercase tracking-widest">或粘贴文本</span>',
        '                <textarea id="paste-box" rows="5" class="w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-3.5 text-sm focus:outline-none focus:border-pink-500 focus:ring-4 focus:ring-pink-500/10 placeholder-zinc-600 text-zinc-200 transition" placeholder="在此粘贴杂乱的教学大纲文本..."></textarea>',
        '                    <span>立即简化</span>',
        '                <p class="font-display font-bold text-lg text-zinc-100">正在解析课程条款...</p>',
        '                <p class="text-xs text-zinc-500">提取成绩权重、规则和截止日期</p>',
        '                    同步到日历 (.ics)',
        '                    分享卡片',
        '                    <span class="text-[10px] font-bold tracking-[.15em] text-orange-400 uppercase">课程概览</span>',
        '                    <h3 id="render-course-title" class="font-display text-lg font-bold text-white mt-0.5 tracking-tight">加载标题中...</h3>',
        '                <!-- 成绩权重分布 -->',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">成绩权重分布</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">重要节点与截止日期</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">迟交政策与联系方式</span>',
        '                        <p class="text-[10.5px] text-white/85 font-medium mt-0.5">告别文字墙。截图并分享 ✂️</p>',
        '                        同步到日历 (.ics)',
        '                        分享卡片',
        '                清除并总结另一份大纲',
        '                <h3 class="font-display text-lg font-bold text-white">添加到你的日历</h3>',
        '                <button id="calendar-modal-close" aria-label="关闭" class="w-8 h-8 rounded-full flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-800 transition">',
        '                    Apple 日历 / 其他 (.ics)',
        '            <a href="/terms-of-service.html" class="text-zinc-600 hover:text-zinc-400 transition">服务条款</a>',
        '            <a href="/privacy-policy.html" class="text-zinc-600 hover:text-zinc-400 transition">隐私政策</a>',
        '        <p class="text-[11px] text-zinc-600">© 2026 SyllabusTLDR • 为极速移动端体验而生。</p>',
        "    dropTitleDefault: '上传教学大纲 PDF',",
        "    dropSubtitleDefault: '点击选择或将文件拖放到此处',",
        '    // There are two 分享卡片 buttons on the page (one above the',
    ],
    'de': [
        '<html lang="de">',
        '<title>SyllabusTLDR — Deinen Studienplan sofort vereinfachen</title>',
        '<meta name="description" content="Lade deinen Studienplan hoch und erhalte sofort ein kompaktes Dashboard: Notengewichtung, Fristen und Kalendersync in 2 Sekunden. 100% kostenlos, keine Anmeldung.">',
        '<meta property="og:title" content="SyllabusTLDR — Deinen Studienplan sofort vereinfachen">',
        '<meta property="og:description" content="Lade deinen Studienplan hoch und erhalte sofort ein kompaktes Dashboard: Notengewichtung, Fristen und Kalendersync in 2 Sekunden. 100% kostenlos, keine Anmeldung.">',
        '<meta property="og:url" content="https://syllabustldr.com/de/">',
        '<meta property="og:locale" content="de_DE">',
        '            <a href="/de/" class="flex items-center gap-2.5">',
        '                    <p class="text-xs text-zinc-500">Keine Anmeldung • Zusammenfassung in 2 Sekunden</p>',
        '                    100% Kostenlos',
        '                <h2 class="font-display text-3xl font-bold tracking-tight leading-tight">Schluss mit der <span class="bg-gradient-to-r from-orange-400 to-pink-500 bg-clip-text text-transparent">Textwand.</span></h2>',
        '                <p class="text-zinc-400 text-sm max-w-xs mx-auto text-pretty">Verwandle komplexe, mehrseitige Studienpläne sofort in ein übersichtliches, kompaktes Dashboard.</p>',
        '                        <p id="drop-title" class="font-bold text-sm">Studienplan-PDF hochladen</p>',
        '                        <p id="drop-subtitle" class="text-xs text-zinc-500 mt-1">Tippen zum Auswählen oder Datei hier ablegen</p>',
        '                <span class="px-3 text-[11px] text-zinc-500 font-semibold uppercase tracking-widest">ODER TEXT EINFÜGEN</span>',
        '                <textarea id="paste-box" rows="5" class="w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-3.5 text-sm focus:outline-none focus:border-pink-500 focus:ring-4 focus:ring-pink-500/10 placeholder-zinc-600 text-zinc-200 transition" placeholder="Füge hier den unübersichtlichen Text deines Studienplans ein..."></textarea>',
        '                    <span>Sofort vereinfachen</span>',
        '                <p class="font-display font-bold text-lg text-zinc-100">Klauseln werden zerlegt...</p>',
        '                <p class="text-xs text-zinc-500">Notengewichtung, Regeln und Fristen werden extrahiert</p>',
        '                    Mit Kalender synchronisieren (.ics)',
        '                    Karte teilen',
        '                    <span class="text-[10px] font-bold tracking-[.15em] text-orange-400 uppercase">Kursübersicht</span>',
        '                    <h3 id="render-course-title" class="font-display text-lg font-bold text-white mt-0.5 tracking-tight">Titel wird geladen...</h3>',
        '                <!-- Notengewichtung -->',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Notengewichtung</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Wichtige Termine &amp; Fristen</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Verspätungsregeln &amp; Kontakt</span>',
        '                        <p class="text-[10.5px] text-white/85 font-medium mt-0.5">Keine Textwand mehr. Screenshot &amp; teilen ✂️</p>',
        '                        Mit Kalender synchronisieren (.ics)',
        '                        Karte teilen',
        '                Löschen und weiteren Studienplan zusammenfassen',
        '                <h3 class="font-display text-lg font-bold text-white">Zu deinem Kalender hinzufügen</h3>',
        '                <button id="calendar-modal-close" aria-label="Schließen" class="w-8 h-8 rounded-full flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-800 transition">',
        '                    Apple Kalender / Andere (.ics)',
        '            <a href="/terms-of-service.html" class="text-zinc-600 hover:text-zinc-400 transition">Nutzungsbedingungen</a>',
        '            <a href="/privacy-policy.html" class="text-zinc-600 hover:text-zinc-400 transition">Datenschutzerklärung</a>',
        '        <p class="text-[11px] text-zinc-600">© 2026 SyllabusTLDR • Für schnelle mobile Nutzung entwickelt.</p>',
        "    dropTitleDefault: 'Studienplan-PDF hochladen',",
        "    dropSubtitleDefault: 'Tippen zum Auswählen oder Datei hier ablegen',",
        '    // There are two Karte teilen buttons on the page (one above the',
    ],
    'vi': [
        '<html lang="vi">',
        '<title>SyllabusTLDR — Đơn Giản Hóa Đề Cương Môn Học Ngay Lập Tức</title>',
        '<meta name="description" content="Tải đề cương môn học lên, nhận bảng tổng quan gọn nhẹ ngay lập tức: trọng số điểm, hạn chót và đồng bộ lịch trong 2 giây. Hoàn toàn miễn phí, không cần đăng nhập.">',
        '<meta property="og:title" content="SyllabusTLDR — Đơn Giản Hóa Đề Cương Môn Học Ngay Lập Tức">',
        '<meta property="og:description" content="Tải đề cương môn học lên, nhận bảng tổng quan gọn nhẹ ngay lập tức: trọng số điểm, hạn chót và đồng bộ lịch trong 2 giây. Hoàn toàn miễn phí, không cần đăng nhập.">',
        '<meta property="og:url" content="https://syllabustldr.com/vi/">',
        '<meta property="og:locale" content="vi_VN">',
        '            <a href="/vi/" class="flex items-center gap-2.5">',
        '                    <p class="text-xs text-zinc-500">Không cần đăng nhập • Tóm tắt trong 2 giây</p>',
        '                    100% Miễn Phí',
        '                <h2 class="font-display text-3xl font-bold tracking-tight leading-tight">Bỏ Qua <span class="bg-gradient-to-r from-orange-400 to-pink-500 bg-clip-text text-transparent">Bức Tường Chữ.</span></h2>',
        '                <p class="text-zinc-400 text-sm max-w-xs mx-auto text-pretty">Chuyển đổi đề cương môn học phức tạp, nhiều trang thành bảng tổng quan gọn gàng, súc tích ngay lập tức.</p>',
        '                        <p id="drop-title" class="font-bold text-sm">Tải Lên PDF Đề Cương</p>',
        '                        <p id="drop-subtitle" class="text-xs text-zinc-500 mt-1">Chạm để chọn hoặc kéo thả tệp vào đây</p>',
        '                <span class="px-3 text-[11px] text-zinc-500 font-semibold uppercase tracking-widest">HOẶC DÁN VĂN BẢN</span>',
        '                <textarea id="paste-box" rows="5" class="w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-3.5 text-sm focus:outline-none focus:border-pink-500 focus:ring-4 focus:ring-pink-500/10 placeholder-zinc-600 text-zinc-200 transition" placeholder="Dán đoạn văn bản lộn xộn của đề cương môn học vào đây..."></textarea>',
        '                    <span>Đơn Giản Hóa Ngay</span>',
        '                <p class="font-display font-bold text-lg text-zinc-100">Đang phân tích các điều khoản...</p>',
        '                <p class="text-xs text-zinc-500">Đang trích xuất trọng số điểm, quy định và hạn chót</p>',
        '                    Đồng Bộ Với Lịch (.ics)',
        '                    Chia Sẻ Thẻ Tóm Tắt',
        '                    <span class="text-[10px] font-bold tracking-[.15em] text-orange-400 uppercase">Tổng Quan Môn Học</span>',
        '                    <h3 id="render-course-title" class="font-display text-lg font-bold text-white mt-0.5 tracking-tight">Đang tải tiêu đề...</h3>',
        '                <!-- Phân Bổ Trọng Số Điểm -->',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Phân Bổ Trọng Số Điểm</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Mốc Quan Trọng &amp; Hạn Chót</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">Quy Định Trễ Hạn &amp; Liên Hệ</span>',
        '                        <p class="text-[10.5px] text-white/85 font-medium mt-0.5">Bỏ qua bức tường chữ. Chụp màn hình &amp; chia sẻ ✂️</p>',
        '                        Đồng Bộ Với Lịch (.ics)',
        '                        Chia Sẻ Thẻ Tóm Tắt',
        '                Xóa và tóm tắt đề cương khác',
        '                <h3 class="font-display text-lg font-bold text-white">Thêm Vào Lịch Của Bạn</h3>',
        '                <button id="calendar-modal-close" aria-label="Đóng" class="w-8 h-8 rounded-full flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-800 transition">',
        '                    Lịch Apple / Khác (.ics)',
        '            <a href="/terms-of-service.html" class="text-zinc-600 hover:text-zinc-400 transition">Điều Khoản Dịch Vụ</a>',
        '            <a href="/privacy-policy.html" class="text-zinc-600 hover:text-zinc-400 transition">Chính Sách Bảo Mật</a>',
        '        <p class="text-[11px] text-zinc-600">© 2026 SyllabusTLDR • Được xây dựng để thực thi nhanh trên di động.</p>',
        "    dropTitleDefault: 'Tải Lên PDF Đề Cương',",
        "    dropSubtitleDefault: 'Chạm để chọn hoặc kéo thả tệp vào đây',",
        '    // There are two Chia Sẻ Thẻ Tóm Tắt buttons on the page (one above the',
    ],
    'ko': [
        '<html lang="ko">',
        '<title>SyllabusTLDR — 강의계획서를 즉시 간단하게</title>',
        '<meta name="description" content="강의계획서를 업로드하면 포켓 크기의 대시보드를 받아보세요. 성적 비중, 마감일, 캘린더 동기화까지 2초 만에. 100% 무료, 로그인 불필요.">',
        '<meta property="og:title" content="SyllabusTLDR — 강의계획서를 즉시 간단하게">',
        '<meta property="og:description" content="강의계획서를 업로드하면 포켓 크기의 대시보드를 받아보세요. 성적 비중, 마감일, 캘린더 동기화까지 2초 만에. 100% 무료, 로그인 불필요.">',
        '<meta property="og:url" content="https://syllabustldr.com/ko/">',
        '<meta property="og:locale" content="ko_KR">',
        '            <a href="/ko/" class="flex items-center gap-2.5">',
        '                    <p class="text-xs text-zinc-500">로그인 불필요 • 2초 요약</p>',
        '                    100% 무료',
        '                <h2 class="font-display text-3xl font-bold tracking-tight leading-tight">이제 그만, <span class="bg-gradient-to-r from-orange-400 to-pink-500 bg-clip-text text-transparent">텍스트 벽.</span></h2>',
        '                <p class="text-zinc-400 text-sm max-w-xs mx-auto text-pretty">복잡한 여러 페이지의 강의계획서를 깔끔하고 간편한 대시보드로 즉시 변환하세요.</p>',
        '                        <p id="drop-title" class="font-bold text-sm">강의계획서 PDF 업로드</p>',
        '                        <p id="drop-subtitle" class="text-xs text-zinc-500 mt-1">탭하여 선택하거나 파일을 여기로 끌어다 놓으세요</p>',
        '                <span class="px-3 text-[11px] text-zinc-500 font-semibold uppercase tracking-widest">또는 텍스트 붙여넣기</span>',
        '                <textarea id="paste-box" rows="5" class="w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-3.5 text-sm focus:outline-none focus:border-pink-500 focus:ring-4 focus:ring-pink-500/10 placeholder-zinc-600 text-zinc-200 transition" placeholder="여기에 강의계획서의 텍스트를 붙여넣으세요..."></textarea>',
        '                    <span>즉시 간단하게</span>',
        '                <p class="font-display font-bold text-lg text-zinc-100">세부 조항을 분석하는 중...</p>',
        '                <p class="text-xs text-zinc-500">성적 비중, 규정, 마감일을 추출하는 중</p>',
        '                    캘린더에 동기화 (.ics)',
        '                    카드 공유하기',
        '                    <span class="text-[10px] font-bold tracking-[.15em] text-orange-400 uppercase">강의 요약</span>',
        '                    <h3 id="render-course-title" class="font-display text-lg font-bold text-white mt-0.5 tracking-tight">제목 불러오는 중...</h3>',
        '                <!-- 성적 비중 분석 -->',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">성적 비중 분석</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">주요 일정 &amp; 마감일</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">지각 정책 &amp; 연락처</span>',
        '                        <p class="text-[10.5px] text-white/85 font-medium mt-0.5">텍스트 벽은 건너뛰고. 캡처해서 공유하세요 ✂️</p>',
        '                        캘린더에 동기화 (.ics)',
        '                        카드 공유하기',
        '                지우고 다른 강의계획서 요약하기',
        '                <h3 class="font-display text-lg font-bold text-white">캘린더에 추가</h3>',
        '                <button id="calendar-modal-close" aria-label="닫기" class="w-8 h-8 rounded-full flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-800 transition">',
        '                    Apple 캘린더 / 기타 (.ics)',
        '            <a href="/terms-of-service.html" class="text-zinc-600 hover:text-zinc-400 transition">이용약관</a>',
        '            <a href="/privacy-policy.html" class="text-zinc-600 hover:text-zinc-400 transition">개인정보처리방침</a>',
        '        <p class="text-[11px] text-zinc-600">© 2026 SyllabusTLDR • 빠른 모바일 사용을 위해 제작되었습니다.</p>',
        "    dropTitleDefault: '강의계획서 PDF 업로드',",
        "    dropSubtitleDefault: '탭하여 선택하거나 파일을 여기로 끌어다 놓으세요',",
        '    // There are two 카드 공유하기 buttons on the page (one above the',
    ],
    'hi': [
        '<html lang="hi">',
        '<title>SyllabusTLDR — अपने पाठ्यक्रम को तुरंत सरल बनाएं</title>',
        '<meta name="description" content="अपना पाठ्यक्रम डालें, तुरंत एक कॉम्पैक्ट डैशबोर्ड पाएं। ग्रेड वेटेज, डेडलाइन और कैलेंडर सिंक — सिर्फ 2 सेकंड में। 100% मुफ़्त, कोई लॉगिन नहीं।">',
        '<meta property="og:title" content="SyllabusTLDR — अपने पाठ्यक्रम को तुरंत सरल बनाएं">',
        '<meta property="og:description" content="अपना पाठ्यक्रम डालें, तुरंत एक कॉम्पैक्ट डैशबोर्ड पाएं। ग्रेड वेटेज, डेडलाइन और कैलेंडर सिंक — सिर्फ 2 सेकंड में। 100% मुफ़्त, कोई लॉगिन नहीं।">',
        '<meta property="og:url" content="https://syllabustldr.com/hi/">',
        '<meta property="og:locale" content="hi_IN">',
        '            <a href="/hi/" class="flex items-center gap-2.5">',
        '                    <p class="text-xs text-zinc-500">कोई लॉगिन नहीं • 2-सेकंड सारांश</p>',
        '                    100% मुफ़्त',
        '                <h2 class="font-display text-3xl font-bold tracking-tight leading-tight">टेक्स्ट की <span class="bg-gradient-to-r from-orange-400 to-pink-500 bg-clip-text text-transparent">दीवार को भूल जाइए।</span></h2>',
        '                <p class="text-zinc-400 text-sm max-w-xs mx-auto text-pretty">जटिल, कई पन्नों वाले पाठ्यक्रम को तुरंत एक साफ़, कॉम्पैक्ट डैशबोर्ड में बदलें।</p>',
        '                        <p id="drop-title" class="font-bold text-sm">पाठ्यक्रम PDF अपलोड करें</p>',
        '                        <p id="drop-subtitle" class="text-xs text-zinc-500 mt-1">चुनने के लिए टैप करें या फ़ाइल यहाँ छोड़ें</p>',
        '                <span class="px-3 text-[11px] text-zinc-500 font-semibold uppercase tracking-widest">या टेक्स्ट पेस्ट करें</span>',
        '                <textarea id="paste-box" rows="5" class="w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-3.5 text-sm focus:outline-none focus:border-pink-500 focus:ring-4 focus:ring-pink-500/10 placeholder-zinc-600 text-zinc-200 transition" placeholder="अपने पाठ्यक्रम का अव्यवस्थित टेक्स्ट यहाँ पेस्ट करें..."></textarea>',
        '                    <span>तुरंत सरल बनाएं</span>',
        '                <p class="font-display font-bold text-lg text-zinc-100">नियम-शर्तों का विश्लेषण हो रहा है...</p>',
        '                <p class="text-xs text-zinc-500">ग्रेड वेटेज, नियम और डेडलाइन निकाली जा रही हैं</p>',
        '                    कैलेंडर से सिंक करें (.ics)',
        '                    कार्ड शेयर करें',
        '                    <span class="text-[10px] font-bold tracking-[.15em] text-orange-400 uppercase">कोर्स सारांश</span>',
        '                    <h3 id="render-course-title" class="font-display text-lg font-bold text-white mt-0.5 tracking-tight">शीर्षक लोड हो रहा है...</h3>',
        '                <!-- ग्रेड वेटेज विवरण -->',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">ग्रेड वेटेज विवरण</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">मुख्य माइलस्टोन और डेडलाइन</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">विलंब नीति और संपर्क</span>',
        '                        <p class="text-[10.5px] text-white/85 font-medium mt-0.5">टेक्स्ट की दीवार को छोड़ें। स्क्रीनशॉट लें और शेयर करें ✂️</p>',
        '                        कैलेंडर से सिंक करें (.ics)',
        '                        कार्ड शेयर करें',
        '                साफ़ करें और दूसरा पाठ्यक्रम सारांशित करें',
        '                <h3 class="font-display text-lg font-bold text-white">अपने कैलेंडर में जोड़ें</h3>',
        '                <button id="calendar-modal-close" aria-label="बंद करें" class="w-8 h-8 rounded-full flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-800 transition">',
        '                    Apple कैलेंडर / अन्य (.ics)',
        '            <a href="/terms-of-service.html" class="text-zinc-600 hover:text-zinc-400 transition">सेवा की शर्तें</a>',
        '            <a href="/privacy-policy.html" class="text-zinc-600 hover:text-zinc-400 transition">गोपनीयता नीति</a>',
        '        <p class="text-[11px] text-zinc-600">© 2026 SyllabusTLDR • तेज़ मोबाइल अनुभव के लिए बनाया गया।</p>',
        "    dropTitleDefault: 'पाठ्यक्रम PDF अपलोड करें',",
        "    dropSubtitleDefault: 'चुनने के लिए टैप करें या फ़ाइल यहाँ छोड़ें',",
        '    // There are two कार्ड शेयर करें buttons on the page (one above the',
    ],
    'ar': [
        '<html lang="ar" dir="rtl">',
        '<title>SyllabusTLDR — بسّط مخطط مقررك الدراسي فورًا</title>',
        '<meta name="description" content="ألصق مخطط مقررك الدراسي واحصل على لوحة معلومات مختصرة فورًا: أوزان الدرجات، المواعيد النهائية، ومزامنة التقويم خلال ثانيتين. مجاني 100%، دون تسجيل دخول.">',
        '<meta property="og:title" content="SyllabusTLDR — بسّط مخطط مقررك الدراسي فورًا">',
        '<meta property="og:description" content="ألصق مخطط مقررك الدراسي واحصل على لوحة معلومات مختصرة فورًا: أوزان الدرجات، المواعيد النهائية، ومزامنة التقويم خلال ثانيتين. مجاني 100%، دون تسجيل دخول.">',
        '<meta property="og:url" content="https://syllabustldr.com/ar/">',
        '<meta property="og:locale" content="ar_AR">',
        '            <a href="/ar/" class="flex items-center gap-2.5">',
        '                    <p class="text-xs text-zinc-500">بدون تسجيل دخول • ملخص خلال ثانيتين</p>',
        '                    100% مجاني',
        '                <h2 class="font-display text-3xl font-bold tracking-tight leading-tight">انسَ <span class="bg-gradient-to-r from-orange-400 to-pink-500 bg-clip-text text-transparent">جدار النص.</span></h2>',
        '                <p class="text-zinc-400 text-sm max-w-xs mx-auto text-pretty">حوّل مخططات المقررات المعقدة متعددة الصفحات إلى لوحة معلومات نظيفة ومختصرة، فورًا.</p>',
        '                        <p id="drop-title" class="font-bold text-sm">رفع ملف PDF لمخطط المقرر</p>',
        '                        <p id="drop-subtitle" class="text-xs text-zinc-500 mt-1">اضغط للاختيار أو أفلت الملف هنا</p>',
        '                <span class="px-3 text-[11px] text-zinc-500 font-semibold uppercase tracking-widest">أو الصق النص</span>',
        '                <textarea id="paste-box" rows="5" class="w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-3.5 text-sm focus:outline-none focus:border-pink-500 focus:ring-4 focus:ring-pink-500/10 placeholder-zinc-600 text-zinc-200 transition" placeholder="الصق هنا نص مخطط المقرر غير المنظم..."></textarea>',
        '                    <span>بسّط فورًا</span>',
        '                <p class="font-display font-bold text-lg text-zinc-100">جارٍ تحليل بنود السياسة...</p>',
        '                <p class="text-xs text-zinc-500">جارٍ استخراج أوزان الدرجات والقواعد والمواعيد النهائية</p>',
        '                    مزامنة مع التقويم (.ics)',
        '                    مشاركة البطاقة',
        '                    <span class="text-[10px] font-bold tracking-[.15em] text-orange-400 uppercase">ملخص المقرر</span>',
        '                    <h3 id="render-course-title" class="font-display text-lg font-bold text-white mt-0.5 tracking-tight">جارٍ تحميل العنوان...</h3>',
        '                <!-- توزيع أوزان الدرجات -->',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">توزيع أوزان الدرجات</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">أهم المحطات والمواعيد النهائية</span>',
        '                        <span class="text-[11px] font-bold tracking-[.12em] text-zinc-300 uppercase">سياسات التأخير وجهة الاتصال</span>',
        '                        <p class="text-[10.5px] text-white/85 font-medium mt-0.5">تجاوز جدار النص. التقط صورة للشاشة وشارك ✂️</p>',
        '                        مزامنة مع التقويم (.ics)',
        '                        مشاركة البطاقة',
        '                مسح وتلخيص مخطط مقرر آخر',
        '                <h3 class="font-display text-lg font-bold text-white">أضف إلى تقويمك</h3>',
        '                <button id="calendar-modal-close" aria-label="إغلاق" class="w-8 h-8 rounded-full flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-800 transition">',
        '                    تقويم Apple / آخر (.ics)',
        '            <a href="/terms-of-service.html" class="text-zinc-600 hover:text-zinc-400 transition">شروط الخدمة</a>',
        '            <a href="/privacy-policy.html" class="text-zinc-600 hover:text-zinc-400 transition">سياسة الخصوصية</a>',
        '        <p class="text-[11px] text-zinc-600">© 2026 SyllabusTLDR • صُمم للأداء السريع على الجوال.</p>',
        "    dropTitleDefault: 'رفع ملف PDF لمخطط المقرر',",
        "    dropSubtitleDefault: 'اضغط للاختيار أو أفلت الملف هنا',",
        '    // There are two مشاركة البطاقة buttons on the page (one above the',
    ],
}

# ---------------------------------------------------------------------------
# NEW_STATIC_EN / NEW_STATIC_TR — strings added in Milestone 1 (footer nav
# links, EIGHTFINITY LTD legal line, cookie-consent banner) that didn't
# exist when es/fr/pt/zh were last generated. Needed for ALL 9 non-English
# languages, not just the 5 new ones.
# ---------------------------------------------------------------------------
NEW_STATIC_EN = [
    '            <a href="/about/" class="text-zinc-600 hover:text-zinc-400 transition">About</a>',
    '            <a href="/contact/" class="text-zinc-600 hover:text-zinc-400 transition">Contact</a>',
    '            <a href="/blog/" class="text-zinc-600 hover:text-zinc-400 transition">Blog</a>',
    '        <p class="text-[11px] text-zinc-700 mt-1">SyllabusTLDR is operated by EIGHTFINITY LTD, a registered company in the United Kingdom.</p>',
    '                We use cookies for analytics and, once ads are enabled, to show relevant ads. Read our',
    '                <button id="consent-reject" type="button" class="btn-press flex-1 sm:flex-none bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold px-4 py-2 rounded-full border border-zinc-700">Reject</button>',
    '                <button id="consent-accept" type="button" class="btn-press flex-1 sm:flex-none bg-gradient-to-br from-orange-500 to-pink-600 hover:brightness-110 text-white text-xs font-semibold px-4 py-2 rounded-full shadow-lg shadow-orange-600/30">Accept All</button>',
]

NEW_STATIC_TR = {
    'es': [
        '            <a href="/about/" class="text-zinc-600 hover:text-zinc-400 transition">Acerca de</a>',
        '            <a href="/contact/" class="text-zinc-600 hover:text-zinc-400 transition">Contacto</a>',
        '            <a href="/blog/" class="text-zinc-600 hover:text-zinc-400 transition">Blog</a>',
        '        <p class="text-[11px] text-zinc-700 mt-1">SyllabusTLDR está operado por EIGHTFINITY LTD, una empresa registrada en el Reino Unido.</p>',
        '                Usamos cookies para análisis y, una vez habilitados los anuncios, para mostrar anuncios relevantes. Lee nuestra',
        '                <button id="consent-reject" type="button" class="btn-press flex-1 sm:flex-none bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold px-4 py-2 rounded-full border border-zinc-700">Rechazar</button>',
        '                <button id="consent-accept" type="button" class="btn-press flex-1 sm:flex-none bg-gradient-to-br from-orange-500 to-pink-600 hover:brightness-110 text-white text-xs font-semibold px-4 py-2 rounded-full shadow-lg shadow-orange-600/30">Aceptar Todo</button>',
    ],
    'fr': [
        '            <a href="/about/" class="text-zinc-600 hover:text-zinc-400 transition">À propos</a>',
        '            <a href="/contact/" class="text-zinc-600 hover:text-zinc-400 transition">Contact</a>',
        '            <a href="/blog/" class="text-zinc-600 hover:text-zinc-400 transition">Blog</a>',
        '        <p class="text-[11px] text-zinc-700 mt-1">SyllabusTLDR est exploité par EIGHTFINITY LTD, une société enregistrée au Royaume-Uni.</p>',
        '                Nous utilisons des cookies à des fins d\'analyse et, une fois les publicités activées, pour afficher des publicités pertinentes. Lisez notre',
        '                <button id="consent-reject" type="button" class="btn-press flex-1 sm:flex-none bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold px-4 py-2 rounded-full border border-zinc-700">Refuser</button>',
        '                <button id="consent-accept" type="button" class="btn-press flex-1 sm:flex-none bg-gradient-to-br from-orange-500 to-pink-600 hover:brightness-110 text-white text-xs font-semibold px-4 py-2 rounded-full shadow-lg shadow-orange-600/30">Tout Accepter</button>',
    ],
    'pt': [
        '            <a href="/about/" class="text-zinc-600 hover:text-zinc-400 transition">Sobre</a>',
        '            <a href="/contact/" class="text-zinc-600 hover:text-zinc-400 transition">Contato</a>',
        '            <a href="/blog/" class="text-zinc-600 hover:text-zinc-400 transition">Blog</a>',
        '        <p class="text-[11px] text-zinc-700 mt-1">O SyllabusTLDR é operado pela EIGHTFINITY LTD, uma empresa registrada no Reino Unido.</p>',
        '                Usamos cookies para análise e, quando os anúncios forem ativados, para exibir anúncios relevantes. Leia nossa',
        '                <button id="consent-reject" type="button" class="btn-press flex-1 sm:flex-none bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold px-4 py-2 rounded-full border border-zinc-700">Rejeitar</button>',
        '                <button id="consent-accept" type="button" class="btn-press flex-1 sm:flex-none bg-gradient-to-br from-orange-500 to-pink-600 hover:brightness-110 text-white text-xs font-semibold px-4 py-2 rounded-full shadow-lg shadow-orange-600/30">Aceitar Tudo</button>',
    ],
    'zh': [
        '            <a href="/about/" class="text-zinc-600 hover:text-zinc-400 transition">关于我们</a>',
        '            <a href="/contact/" class="text-zinc-600 hover:text-zinc-400 transition">联系我们</a>',
        '            <a href="/blog/" class="text-zinc-600 hover:text-zinc-400 transition">博客</a>',
        '        <p class="text-[11px] text-zinc-700 mt-1">SyllabusTLDR 由 EIGHTFINITY LTD 运营，该公司在英国注册。</p>',
        '                我们使用 Cookie 进行数据分析，广告功能启用后也将用于展示相关广告。请阅读我们的',
        '                <button id="consent-reject" type="button" class="btn-press flex-1 sm:flex-none bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold px-4 py-2 rounded-full border border-zinc-700">拒绝</button>',
        '                <button id="consent-accept" type="button" class="btn-press flex-1 sm:flex-none bg-gradient-to-br from-orange-500 to-pink-600 hover:brightness-110 text-white text-xs font-semibold px-4 py-2 rounded-full shadow-lg shadow-orange-600/30">全部接受</button>',
    ],
    'de': [
        '            <a href="/about/" class="text-zinc-600 hover:text-zinc-400 transition">Über uns</a>',
        '            <a href="/contact/" class="text-zinc-600 hover:text-zinc-400 transition">Kontakt</a>',
        '            <a href="/blog/" class="text-zinc-600 hover:text-zinc-400 transition">Blog</a>',
        '        <p class="text-[11px] text-zinc-700 mt-1">SyllabusTLDR wird von EIGHTFINITY LTD betrieben, einem im Vereinigten Königreich eingetragenen Unternehmen.</p>',
        '                Wir verwenden Cookies für Analysen und, sobald Werbung aktiviert ist, zur Anzeige relevanter Werbung. Lies unsere',
        '                <button id="consent-reject" type="button" class="btn-press flex-1 sm:flex-none bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold px-4 py-2 rounded-full border border-zinc-700">Ablehnen</button>',
        '                <button id="consent-accept" type="button" class="btn-press flex-1 sm:flex-none bg-gradient-to-br from-orange-500 to-pink-600 hover:brightness-110 text-white text-xs font-semibold px-4 py-2 rounded-full shadow-lg shadow-orange-600/30">Alle akzeptieren</button>',
    ],
    'vi': [
        '            <a href="/about/" class="text-zinc-600 hover:text-zinc-400 transition">Giới Thiệu</a>',
        '            <a href="/contact/" class="text-zinc-600 hover:text-zinc-400 transition">Liên Hệ</a>',
        '            <a href="/blog/" class="text-zinc-600 hover:text-zinc-400 transition">Blog</a>',
        '        <p class="text-[11px] text-zinc-700 mt-1">SyllabusTLDR được vận hành bởi EIGHTFINITY LTD, một công ty đã đăng ký tại Vương quốc Anh.</p>',
        '                Chúng tôi sử dụng cookie để phân tích và, khi quảng cáo được bật, để hiển thị quảng cáo phù hợp. Đọc',
        '                <button id="consent-reject" type="button" class="btn-press flex-1 sm:flex-none bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold px-4 py-2 rounded-full border border-zinc-700">Từ Chối</button>',
        '                <button id="consent-accept" type="button" class="btn-press flex-1 sm:flex-none bg-gradient-to-br from-orange-500 to-pink-600 hover:brightness-110 text-white text-xs font-semibold px-4 py-2 rounded-full shadow-lg shadow-orange-600/30">Chấp Nhận Tất Cả</button>',
    ],
    'ko': [
        '            <a href="/about/" class="text-zinc-600 hover:text-zinc-400 transition">소개</a>',
        '            <a href="/contact/" class="text-zinc-600 hover:text-zinc-400 transition">문의하기</a>',
        '            <a href="/blog/" class="text-zinc-600 hover:text-zinc-400 transition">블로그</a>',
        '        <p class="text-[11px] text-zinc-700 mt-1">SyllabusTLDR는 영국에 등록된 회사인 EIGHTFINITY LTD가 운영합니다.</p>',
        '                당사는 분석을 위해 쿠키를 사용하며, 광고가 활성화되면 관련 광고를 표시하는 데에도 사용합니다. 자세히 알아보려면 다음을 확인하세요:',
        '                <button id="consent-reject" type="button" class="btn-press flex-1 sm:flex-none bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold px-4 py-2 rounded-full border border-zinc-700">거부</button>',
        '                <button id="consent-accept" type="button" class="btn-press flex-1 sm:flex-none bg-gradient-to-br from-orange-500 to-pink-600 hover:brightness-110 text-white text-xs font-semibold px-4 py-2 rounded-full shadow-lg shadow-orange-600/30">모두 동의</button>',
    ],
    'hi': [
        '            <a href="/about/" class="text-zinc-600 hover:text-zinc-400 transition">हमारे बारे में</a>',
        '            <a href="/contact/" class="text-zinc-600 hover:text-zinc-400 transition">संपर्क करें</a>',
        '            <a href="/blog/" class="text-zinc-600 hover:text-zinc-400 transition">ब्लॉग</a>',
        '        <p class="text-[11px] text-zinc-700 mt-1">SyllabusTLDR का संचालन EIGHTFINITY LTD द्वारा किया जाता है, जो यूनाइटेड किंगडम में पंजीकृत एक कंपनी है।</p>',
        '                हम विश्लेषण के लिए कुकीज़ का उपयोग करते हैं, और विज्ञापन चालू होने के बाद प्रासंगिक विज्ञापन दिखाने के लिए भी। अधिक जानकारी के लिए देखें:',
        '                <button id="consent-reject" type="button" class="btn-press flex-1 sm:flex-none bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold px-4 py-2 rounded-full border border-zinc-700">अस्वीकार करें</button>',
        '                <button id="consent-accept" type="button" class="btn-press flex-1 sm:flex-none bg-gradient-to-br from-orange-500 to-pink-600 hover:brightness-110 text-white text-xs font-semibold px-4 py-2 rounded-full shadow-lg shadow-orange-600/30">सभी स्वीकार करें</button>',
    ],
    'ar': [
        '            <a href="/about/" class="text-zinc-600 hover:text-zinc-400 transition">من نحن</a>',
        '            <a href="/contact/" class="text-zinc-600 hover:text-zinc-400 transition">تواصل معنا</a>',
        '            <a href="/blog/" class="text-zinc-600 hover:text-zinc-400 transition">المدونة</a>',
        '        <p class="text-[11px] text-zinc-700 mt-1">يُدار SyllabusTLDR بواسطة EIGHTFINITY LTD، وهي شركة مسجّلة في المملكة المتحدة.</p>',
        '                نستخدم ملفات تعريف الارتباط (كوكيز) لأغراض التحليل، وبمجرد تفعيل الإعلانات، لعرض إعلانات ذات صلة. اقرأ',
        '                <button id="consent-reject" type="button" class="btn-press flex-1 sm:flex-none bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold px-4 py-2 rounded-full border border-zinc-700">رفض</button>',
        '                <button id="consent-accept" type="button" class="btn-press flex-1 sm:flex-none bg-gradient-to-br from-orange-500 to-pink-600 hover:brightness-110 text-white text-xs font-semibold px-4 py-2 rounded-full shadow-lg shadow-orange-600/30">قبول الكل</button>',
    ],
}

for _lang in LANG_ORDER:
    if _lang == 'en':
        continue
    assert _lang in EXISTING_STATIC_TR, f'missing EXISTING_STATIC_TR for {_lang}'
    assert _lang in NEW_STATIC_TR, f'missing NEW_STATIC_TR for {_lang}'
    assert len(EXISTING_STATIC_TR[_lang]) == len(EXISTING_STATIC_EN), f'{_lang} EXISTING_STATIC_TR length mismatch'
    assert len(NEW_STATIC_TR[_lang]) == len(NEW_STATIC_EN), f'{_lang} NEW_STATIC_TR length mismatch'

# ---------------------------------------------------------------------------
# T_BLOCKS — the translated `window.T = {...};` object body for each
# non-English language (no <script> wrapper; that's added at generation
# time). es/fr/pt/zh copied verbatim from the previously-generated files.
# de/hi/ar/ko/vi composed fresh, same 35 keys, same structure/placeholders.
# ---------------------------------------------------------------------------
T_BLOCKS = {}

T_BLOCKS['es'] = r'''window.T = {
  untitledCourse: "Curso sin título",
  courseDetailsUnavailable: "Detalles del curso no disponibles",
  referToProfessor: "Consulta al profesor",
  gradesEmptyState: "Consulta al profesor para la ponderación exacta.",
  deadlinesEmptyState: "Consulta al profesor para las fechas clave.",
  flagLabels: { "Due": "Entrega", "Submission": "Entrega", "Test": "Examen", "Exam": "Examen", "Midterm": "Parcial", "Final": "Final", "Quiz": "Quiz", "Project Due": "Entrega de Proyecto", "Presentation": "Presentación", "Paper Due": "Entrega de Ensayo" },
  gradeCategoryLabels: {"Final Exam": "Examen Final", "Midterm": "Parcial", "Exams": "Exámenes", "Quizzes": "Quizzes", "Projects": "Proyectos", "Assignments": "Tareas", "Homework": "Tareas", "Participation": "Participación", "Attendance": "Asistencia", "Papers": "Ensayos", "Labs": "Laboratorios", "Presentations": "Presentaciones", "Discussion": "Discusión", "Essays": "Ensayos"},
  termSeasonLabels: {"Fall": "Otoño", "Spring": "Primavera", "Summer": "Verano", "Winter": "Invierno"},
  weekLabelTemplate: (n) => `Semana ${n}`,
  preparingLabel: "Preparando…",
  toastNoExactDates: "Las fechas límite solo indican número de semana — no hay fechas exactas para sincronizar aún.",
  toastNoDatesFound: "No se encontraron fechas específicas — nada que sincronizar aún.",
  toastICSDownloaded: "Archivo de calendario descargado — tócalo para importarlo.",
  shareGradesSummarized: "Calificaciones resumidas",
  shareDeadlinesOrganized: "Fechas límite organizadas",
  shareCaptionTemplate: (title, topGrade, nextDue) => `📚 ${title} — simplificado en 2 segundos.\n${topGrade}. ${nextDue}.\n\nOlvídate del muro de texto:`,
  shareTopGradeTemplate: (label, weight) => `${label} vale el ${weight}% de tu calificación`,
  shareNextDueTemplate: (label, display) => `Próximo: ${label} el ${display}`,
  toastSharedCopied: "¡Compartido! El texto también se copió — pégalo si no aparece automáticamente.",
  toastShareCancelled: "Compartir cancelado.",
  toastImageDownloadedCopied: "¡Imagen descargada y texto copiado — adjúntalo y pégalo para compartir!",
  toastShareUnsupportedCopied: "No se puede compartir aquí — se copió el texto en su lugar.",
  toastImageDownloadedClipboardFailed: "Imagen descargada — no se pudo copiar el texto.",
  toastShareUnsupportedDevice: "No se puede compartir en este dispositivo.",
  toastImageDownloaded: "Imagen descargada en tu dispositivo.",
  toastShareUnsupportedAtAll: "Compartir no es compatible con este dispositivo.",
  errTooShort: "Escribe más texto del sílabo — eso parece demasiado corto para analizar.",
  errParseFailed: "Algo salió mal al analizar el documento. Intenta pegar el texto en su lugar.",
  errNotPDF: "Por favor suelta un archivo .pdf.",
  errPDFNoText: "No se pudo leer el texto de ese PDF — intenta pegar el texto del sílabo.",
  errPDFReadFailed: "No se pudo leer ese PDF. Intenta pegar el texto del sílabo.",
  dropTitleDefault: "Sube el PDF del Sílabo",
  dropSubtitleDefault: "Toca para seleccionar o suelta el archivo aquí",
  dropTitleReading: "Leyendo PDF…",
  calendarModalSubtitleMulti: (label, display, count) => `Google, Outlook y Yahoo agregan rápidamente tu próxima fecha — "${label}" (${display}). Apple/.ics incluye las ${count} fechas.`,
  calendarModalSubtitleSingle: (label, display) => `Agrega "${label}" (${display}) a tu calendario.`,
};'''

T_BLOCKS['fr'] = r'''window.T = {
  untitledCourse: "Cours sans titre",
  courseDetailsUnavailable: "Détails du cours indisponibles",
  referToProfessor: "Consultez le professeur",
  gradesEmptyState: "Consultez le professeur pour la pondération exacte.",
  deadlinesEmptyState: "Consultez le professeur pour les dates clés.",
  flagLabels: { "Due": "À rendre", "Submission": "Remise", "Test": "Examen", "Exam": "Examen", "Midterm": "Mi-session", "Final": "Final", "Quiz": "Quiz", "Project Due": "Projet à Rendre", "Presentation": "Présentation", "Paper Due": "Dissertation à Rendre" },
  gradeCategoryLabels: {"Final Exam": "Examen Final", "Midterm": "Mi-session", "Exams": "Examens", "Quizzes": "Quiz", "Projects": "Projets", "Assignments": "Devoirs", "Homework": "Devoirs", "Participation": "Participation", "Attendance": "Présence", "Papers": "Dissertations", "Labs": "Laboratoires", "Presentations": "Présentations", "Discussion": "Discussion", "Essays": "Dissertations"},
  termSeasonLabels: {"Fall": "Automne", "Spring": "Printemps", "Summer": "Été", "Winter": "Hiver"},
  weekLabelTemplate: (n) => `Semaine ${n}`,
  preparingLabel: "Préparation…",
  toastNoExactDates: "Les échéances ne mentionnent que des numéros de semaine — aucune date exacte à synchroniser pour l'instant.",
  toastNoDatesFound: "Aucune date précise trouvée — rien à synchroniser pour l'instant.",
  toastICSDownloaded: "Fichier calendrier téléchargé — appuyez dessus pour l'importer.",
  shareGradesSummarized: "Notes résumées",
  shareDeadlinesOrganized: "Échéances organisées",
  shareCaptionTemplate: (title, topGrade, nextDue) => `📚 ${title} — simplifié en 2 secondes.\n${topGrade}. ${nextDue}.\n\nOubliez le mur de texte :`,
  shareTopGradeTemplate: (label, weight) => `${label} compte pour ${weight}% de la note`,
  shareNextDueTemplate: (label, display) => `À venir : ${label} le ${display}`,
  toastSharedCopied: "Partagé ! Le texte a aussi été copié — collez-le s'il n'apparaît pas automatiquement.",
  toastShareCancelled: "Partage annulé.",
  toastImageDownloadedCopied: "Image téléchargée et texte copié — joignez-la et collez le texte pour partager !",
  toastShareUnsupportedCopied: "Partage non pris en charge ici — texte copié à la place.",
  toastImageDownloadedClipboardFailed: "Image téléchargée — la copie du texte a échoué.",
  toastShareUnsupportedDevice: "Partage non pris en charge sur cet appareil.",
  toastImageDownloaded: "Image téléchargée sur votre appareil.",
  toastShareUnsupportedAtAll: "Partage non pris en charge sur cet appareil.",
  errTooShort: "Fournissez plus de texte du syllabus — cela semble trop court à analyser.",
  errParseFailed: "Une erreur s'est produite lors de l'analyse du document. Essayez de coller le texte à la place.",
  errNotPDF: "Veuillez déposer un fichier .pdf.",
  errPDFNoText: "Impossible de lire le texte de ce PDF — essayez de coller le texte du syllabus.",
  errPDFReadFailed: "Échec de la lecture de ce PDF. Essayez de coller le texte du syllabus.",
  dropTitleDefault: "Importer le PDF du Syllabus",
  dropSubtitleDefault: "Touchez pour sélectionner ou déposez le fichier ici",
  dropTitleReading: "Lecture du PDF…",
  calendarModalSubtitleMulti: (label, display, count) => `Google, Outlook et Yahoo ajoutent rapidement votre prochaine échéance — « ${label} » (${display}). Apple/.ics inclut les ${count} échéances.`,
  calendarModalSubtitleSingle: (label, display) => `Ajoute « ${label} » (${display}) à votre calendrier.`,
};'''

T_BLOCKS['pt'] = r'''window.T = {
  untitledCourse: "Disciplina sem título",
  courseDetailsUnavailable: "Detalhes da disciplina indisponíveis",
  referToProfessor: "Consulte o professor",
  gradesEmptyState: "Consulte o professor para o peso exato das notas.",
  deadlinesEmptyState: "Consulte o professor para as datas principais.",
  flagLabels: { "Due": "Entrega", "Submission": "Entrega", "Test": "Prova", "Exam": "Prova", "Midterm": "Prova Parcial", "Final": "Prova Final", "Quiz": "Quiz", "Project Due": "Entrega de Projeto", "Presentation": "Apresentação", "Paper Due": "Entrega de Trabalho" },
  gradeCategoryLabels: {"Final Exam": "Prova Final", "Midterm": "Prova Parcial", "Exams": "Provas", "Quizzes": "Quizzes", "Projects": "Projetos", "Assignments": "Trabalhos", "Homework": "Tarefas", "Participation": "Participação", "Attendance": "Frequência", "Papers": "Trabalhos Escritos", "Labs": "Laboratórios", "Presentations": "Apresentações", "Discussion": "Discussão", "Essays": "Redações"},
  termSeasonLabels: {"Fall": "Outono", "Spring": "Primavera", "Summer": "Verão", "Winter": "Inverno"},
  weekLabelTemplate: (n) => `Semana ${n}`,
  preparingLabel: "Preparando…",
  toastNoExactDates: "Os prazos indicam apenas número da semana — ainda não há datas exatas para sincronizar.",
  toastNoDatesFound: "Nenhuma data específica encontrada — nada para sincronizar ainda.",
  toastICSDownloaded: "Arquivo de calendário baixado — toque para importar.",
  shareGradesSummarized: "Notas resumidas",
  shareDeadlinesOrganized: "Prazos organizados",
  shareCaptionTemplate: (title, topGrade, nextDue) => `📚 ${title} — simplificado em 2 segundos.\n${topGrade}. ${nextDue}.\n\nChega de muro de texto:`,
  shareTopGradeTemplate: (label, weight) => `${label} vale ${weight}% da nota`,
  shareNextDueTemplate: (label, display) => `Próximo: ${label} em ${display}`,
  toastSharedCopied: "Compartilhado! O texto também foi copiado — cole se não aparecer automaticamente.",
  toastShareCancelled: "Compartilhamento cancelado.",
  toastImageDownloadedCopied: "Imagem baixada e texto copiado — anexe e cole para compartilhar!",
  toastShareUnsupportedCopied: "Compartilhamento não suportado aqui — texto copiado.",
  toastImageDownloadedClipboardFailed: "Imagem baixada — falha ao copiar o texto.",
  toastShareUnsupportedDevice: "Compartilhamento não suportado neste dispositivo.",
  toastImageDownloaded: "Imagem baixada no seu dispositivo.",
  toastShareUnsupportedAtAll: "Compartilhamento não suportado neste dispositivo.",
  errTooShort: "Forneça mais texto da ementa — pareceu curto demais para analisar.",
  errParseFailed: "Algo deu errado ao analisar o documento. Tente colar o texto.",
  errNotPDF: "Solte um arquivo .pdf.",
  errPDFNoText: "Não foi possível ler o texto desse PDF — tente colar o texto da ementa.",
  errPDFReadFailed: "Falha ao ler esse PDF. Tente colar o texto da ementa.",
  dropTitleDefault: "Enviar PDF da Ementa",
  dropSubtitleDefault: "Toque para selecionar ou solte o arquivo aqui",
  dropTitleReading: "Lendo PDF…",
  calendarModalSubtitleMulti: (label, display, count) => `Google, Outlook e Yahoo adicionam rapidamente seu próximo prazo — "${label}" (${display}). Apple/.ics inclui os ${count} prazos.`,
  calendarModalSubtitleSingle: (label, display) => `Adiciona "${label}" (${display}) ao seu calendário.`,
};'''

T_BLOCKS['zh'] = r'''window.T = {
  untitledCourse: "未命名课程",
  courseDetailsUnavailable: "课程详情不可用",
  referToProfessor: "请咨询教授",
  gradesEmptyState: "请咨询教授以获取准确的成绩权重。",
  deadlinesEmptyState: "请咨询教授以获取关键日期。",
  flagLabels: { "Due": "截止", "Submission": "提交", "Test": "测验", "Exam": "考试", "Midterm": "期中考试", "Final": "期末考试", "Quiz": "小测验", "Project Due": "项目截止", "Presentation": "展示", "Paper Due": "论文截止" },
  gradeCategoryLabels: {"Final Exam": "期末考试", "Midterm": "期中考试", "Exams": "考试", "Quizzes": "小测验", "Projects": "项目", "Assignments": "作业", "Homework": "作业", "Participation": "课堂参与", "Attendance": "出勤", "Papers": "论文", "Labs": "实验", "Presentations": "展示", "Discussion": "讨论", "Essays": "论文"},
  termSeasonLabels: {"Fall": "秋季", "Spring": "春季", "Summer": "夏季", "Winter": "冬季"},
  weekLabelTemplate: (n) => `第${n}周`,
  preparingLabel: "准备中…",
  toastNoExactDates: "截止日期仅显示第几周 — 暂无具体日期可同步。",
  toastNoDatesFound: "未找到具体日期 — 暂无内容可同步。",
  toastICSDownloaded: "日历文件已下载 — 点击以导入。",
  shareGradesSummarized: "成绩已汇总",
  shareDeadlinesOrganized: "截止日期已整理",
  shareCaptionTemplate: (title, topGrade, nextDue) => `📚 ${title} — 2秒完成简化。\n${topGrade}。${nextDue}。\n\n告别文字墙：`,
  shareTopGradeTemplate: (label, weight) => `${label} 占总成绩的 ${weight}%`,
  shareNextDueTemplate: (label, display) => `下一项：${label}，${display}`,
  toastSharedCopied: "已分享！文案也已复制 — 如未自动填入，请手动粘贴。",
  toastShareCancelled: "已取消分享。",
  toastImageDownloadedCopied: "图片已下载，文案已复制 — 附加图片并粘贴文案即可分享！",
  toastShareUnsupportedCopied: "此处不支持分享 — 已改为复制文案。",
  toastImageDownloadedClipboardFailed: "图片已下载 — 复制文案失败。",
  toastShareUnsupportedDevice: "此设备不支持分享。",
  toastImageDownloaded: "图片已下载到你的设备。",
  toastShareUnsupportedAtAll: "此设备不支持分享。",
  errTooShort: "请提供更多大纲文本 — 当前内容太短，无法解析。",
  errParseFailed: "解析该文档时出错。请尝试改为粘贴文本。",
  errNotPDF: "请拖放一个 .pdf 文件。",
  errPDFNoText: "无法读取该 PDF 中的文本 — 请尝试粘贴大纲文本。",
  errPDFReadFailed: "读取该 PDF 失败。请尝试粘贴大纲文本。",
  dropTitleDefault: "上传教学大纲 PDF",
  dropSubtitleDefault: "点击选择或将文件拖放到此处",
  dropTitleReading: "正在读取 PDF…",
  calendarModalSubtitleMulti: (label, display, count) => `Google、Outlook 和 Yahoo 将快速添加你的下一个截止日期 — "${label}"（${display}）。Apple/.ics 将包含全部 ${count} 个截止日期。`,
  calendarModalSubtitleSingle: (label, display) => `将"${label}"（${display}）添加到你的日历。`,
};'''

T_BLOCKS['de'] = r'''window.T = {
  untitledCourse: "Unbenannter Kurs",
  courseDetailsUnavailable: "Kursdetails nicht verfügbar",
  referToProfessor: "Frag deinen Dozenten",
  gradesEmptyState: "Frag deinen Dozenten nach der genauen Gewichtung.",
  deadlinesEmptyState: "Frag deinen Dozenten nach den wichtigen Terminen.",
  flagLabels: { "Due": "Abgabe", "Submission": "Abgabe", "Test": "Test", "Exam": "Prüfung", "Midterm": "Zwischenprüfung", "Final": "Abschlussprüfung", "Quiz": "Quiz", "Project Due": "Projektabgabe", "Presentation": "Präsentation", "Paper Due": "Hausarbeit fällig" },
  gradeCategoryLabels: {"Final Exam": "Abschlussprüfung", "Midterm": "Zwischenprüfung", "Exams": "Prüfungen", "Quizzes": "Quizze", "Projects": "Projekte", "Assignments": "Aufgaben", "Homework": "Hausaufgaben", "Participation": "Mitarbeit", "Attendance": "Anwesenheit", "Papers": "Hausarbeiten", "Labs": "Praktika", "Presentations": "Präsentationen", "Discussion": "Diskussion", "Essays": "Aufsätze"},
  termSeasonLabels: {"Fall": "Herbst", "Spring": "Frühling", "Summer": "Sommer", "Winter": "Winter"},
  weekLabelTemplate: (n) => `Woche ${n}`,
  preparingLabel: "Wird vorbereitet…",
  toastNoExactDates: "Die Fristen geben nur Wochennummern an — noch keine genauen Daten zum Synchronisieren.",
  toastNoDatesFound: "Keine konkreten Daten gefunden — noch nichts zu synchronisieren.",
  toastICSDownloaded: "Kalenderdatei heruntergeladen — zum Importieren antippen.",
  shareGradesSummarized: "Noten zusammengefasst",
  shareDeadlinesOrganized: "Fristen organisiert",
  shareCaptionTemplate: (title, topGrade, nextDue) => `📚 ${title} — in 2 Sekunden vereinfacht.\n${topGrade}. ${nextDue}.\n\nKeine Textwand mehr:`,
  shareTopGradeTemplate: (label, weight) => `${label} zählt ${weight}% der Note`,
  shareNextDueTemplate: (label, display) => `Als Nächstes: ${label} am ${display}`,
  toastSharedCopied: "Geteilt! Der Text wurde ebenfalls kopiert — füge ihn ein, falls er nicht automatisch erscheint.",
  toastShareCancelled: "Teilen abgebrochen.",
  toastImageDownloadedCopied: "Bild heruntergeladen und Text kopiert — anhängen und Text einfügen zum Teilen!",
  toastShareUnsupportedCopied: "Teilen hier nicht unterstützt — Text stattdessen kopiert.",
  toastImageDownloadedClipboardFailed: "Bild heruntergeladen — Text konnte nicht kopiert werden.",
  toastShareUnsupportedDevice: "Teilen wird auf diesem Gerät nicht unterstützt.",
  toastImageDownloaded: "Bild auf deinem Gerät gespeichert.",
  toastShareUnsupportedAtAll: "Teilen wird auf diesem Gerät nicht unterstützt.",
  errTooShort: "Gib mehr Text aus dem Studienplan ein — das scheint zu kurz zum Analysieren.",
  errParseFailed: "Beim Analysieren des Dokuments ist etwas schiefgelaufen. Versuche stattdessen, den Text einzufügen.",
  errNotPDF: "Bitte lege eine .pdf-Datei ab.",
  errPDFNoText: "Der Text aus diesem PDF konnte nicht gelesen werden — versuche, den Text des Studienplans einzufügen.",
  errPDFReadFailed: "Dieses PDF konnte nicht gelesen werden. Versuche, den Text des Studienplans einzufügen.",
  dropTitleDefault: "Studienplan-PDF hochladen",
  dropSubtitleDefault: "Tippen zum Auswählen oder Datei hier ablegen",
  dropTitleReading: "PDF wird gelesen…",
  calendarModalSubtitleMulti: (label, display, count) => `Google, Outlook und Yahoo fügen schnell deinen nächsten Termin hinzu — "${label}" (${display}). Apple/.ics enthält alle ${count} Termine.`,
  calendarModalSubtitleSingle: (label, display) => `Füge "${label}" (${display}) zu deinem Kalender hinzu.`,
};'''

T_BLOCKS['vi'] = r'''window.T = {
  untitledCourse: "Môn học chưa có tiêu đề",
  courseDetailsUnavailable: "Không có thông tin chi tiết môn học",
  referToProfessor: "Hỏi giảng viên của bạn",
  gradesEmptyState: "Hỏi giảng viên để biết trọng số điểm chính xác.",
  deadlinesEmptyState: "Hỏi giảng viên để biết các ngày quan trọng.",
  flagLabels: { "Due": "Hạn nộp", "Submission": "Nộp bài", "Test": "Kiểm tra", "Exam": "Thi", "Midterm": "Giữa kỳ", "Final": "Cuối kỳ", "Quiz": "Trắc nghiệm", "Project Due": "Hạn Nộp Dự Án", "Presentation": "Thuyết Trình", "Paper Due": "Hạn Nộp Bài Luận" },
  gradeCategoryLabels: {"Final Exam": "Thi Cuối Kỳ", "Midterm": "Giữa Kỳ", "Exams": "Các Kỳ Thi", "Quizzes": "Bài Trắc Nghiệm", "Projects": "Dự Án", "Assignments": "Bài Tập", "Homework": "Bài Tập Về Nhà", "Participation": "Tham Gia", "Attendance": "Điểm Danh", "Papers": "Bài Luận", "Labs": "Thực Hành", "Presentations": "Thuyết Trình", "Discussion": "Thảo Luận", "Essays": "Bài Luận"},
  termSeasonLabels: {"Fall": "Thu", "Spring": "Xuân", "Summer": "Hè", "Winter": "Đông"},
  weekLabelTemplate: (n) => `Tuần ${n}`,
  preparingLabel: "Đang chuẩn bị…",
  toastNoExactDates: "Các hạn chót chỉ ghi số tuần — chưa có ngày cụ thể để đồng bộ.",
  toastNoDatesFound: "Không tìm thấy ngày cụ thể — chưa có gì để đồng bộ.",
  toastICSDownloaded: "Đã tải xuống tệp lịch — chạm để nhập.",
  shareGradesSummarized: "Đã tóm tắt điểm số",
  shareDeadlinesOrganized: "Đã sắp xếp hạn chót",
  shareCaptionTemplate: (title, topGrade, nextDue) => `📚 ${title} — đơn giản hóa trong 2 giây.\n${topGrade}. ${nextDue}.\n\nBỏ qua bức tường chữ:`,
  shareTopGradeTemplate: (label, weight) => `${label} chiếm ${weight}% điểm số`,
  shareNextDueTemplate: (label, display) => `Tiếp theo: ${label} vào ${display}`,
  toastSharedCopied: "Đã chia sẻ! Văn bản cũng đã được sao chép — dán nếu không tự động xuất hiện.",
  toastShareCancelled: "Đã hủy chia sẻ.",
  toastImageDownloadedCopied: "Đã tải hình ảnh và sao chép văn bản — đính kèm và dán để chia sẻ!",
  toastShareUnsupportedCopied: "Không hỗ trợ chia sẻ ở đây — đã sao chép văn bản thay thế.",
  toastImageDownloadedClipboardFailed: "Đã tải hình ảnh — không thể sao chép văn bản.",
  toastShareUnsupportedDevice: "Thiết bị này không hỗ trợ chia sẻ.",
  toastImageDownloaded: "Đã tải hình ảnh xuống thiết bị của bạn.",
  toastShareUnsupportedAtAll: "Thiết bị này không hỗ trợ chia sẻ.",
  errTooShort: "Nhập thêm văn bản đề cương — nội dung này có vẻ quá ngắn để phân tích.",
  errParseFailed: "Đã xảy ra lỗi khi phân tích tài liệu. Hãy thử dán văn bản thay thế.",
  errNotPDF: "Vui lòng thả một tệp .pdf.",
  errPDFNoText: "Không thể đọc văn bản từ tệp PDF đó — hãy thử dán văn bản đề cương.",
  errPDFReadFailed: "Không thể đọc tệp PDF đó. Hãy thử dán văn bản đề cương.",
  dropTitleDefault: "Tải Lên PDF Đề Cương",
  dropSubtitleDefault: "Chạm để chọn hoặc kéo thả tệp vào đây",
  dropTitleReading: "Đang đọc PDF…",
  calendarModalSubtitleMulti: (label, display, count) => `Google, Outlook và Yahoo nhanh chóng thêm hạn chót tiếp theo của bạn — "${label}" (${display}). Apple/.ics bao gồm cả ${count} hạn chót.`,
  calendarModalSubtitleSingle: (label, display) => `Thêm "${label}" (${display}) vào lịch của bạn.`,
};'''

T_BLOCKS['ko'] = r'''window.T = {
  untitledCourse: "제목 없는 강의",
  courseDetailsUnavailable: "강의 세부 정보를 사용할 수 없습니다",
  referToProfessor: "교수님께 문의하세요",
  gradesEmptyState: "정확한 성적 비중은 교수님께 문의하세요.",
  deadlinesEmptyState: "주요 일정은 교수님께 문의하세요.",
  flagLabels: { "Due": "마감", "Submission": "제출", "Test": "시험", "Exam": "시험", "Midterm": "중간고사", "Final": "기말고사", "Quiz": "퀴즈", "Project Due": "프로젝트 마감", "Presentation": "발표", "Paper Due": "과제 마감" },
  gradeCategoryLabels: {"Final Exam": "기말고사", "Midterm": "중간고사", "Exams": "시험", "Quizzes": "퀴즈", "Projects": "프로젝트", "Assignments": "과제", "Homework": "숙제", "Participation": "참여도", "Attendance": "출석", "Papers": "리포트", "Labs": "실습", "Presentations": "발표", "Discussion": "토론", "Essays": "에세이"},
  termSeasonLabels: {"Fall": "가을학기", "Spring": "봄학기", "Summer": "여름학기", "Winter": "겨울학기"},
  weekLabelTemplate: (n) => `${n}주차`,
  preparingLabel: "준비 중…",
  toastNoExactDates: "마감일에 주차 번호만 표시되어 있습니다 — 아직 동기화할 정확한 날짜가 없습니다.",
  toastNoDatesFound: "구체적인 날짜를 찾을 수 없습니다 — 아직 동기화할 내용이 없습니다.",
  toastICSDownloaded: "캘린더 파일이 다운로드되었습니다 — 탭하여 가져오세요.",
  shareGradesSummarized: "성적 요약 완료",
  shareDeadlinesOrganized: "마감일 정리 완료",
  shareCaptionTemplate: (title, topGrade, nextDue) => `📚 ${title} — 2초 만에 간단하게.\n${topGrade}. ${nextDue}.\n\n텍스트 벽은 이제 그만:`,
  shareTopGradeTemplate: (label, weight) => `${label}이(가) 성적의 ${weight}%를 차지합니다`,
  shareNextDueTemplate: (label, display) => `다음 일정: ${label}, ${display}`,
  toastSharedCopied: "공유되었습니다! 텍스트도 복사되었습니다 — 자동으로 입력되지 않으면 붙여넣으세요.",
  toastShareCancelled: "공유가 취소되었습니다.",
  toastImageDownloadedCopied: "이미지가 다운로드되고 텍스트가 복사되었습니다 — 첨부하고 텍스트를 붙여넣어 공유하세요!",
  toastShareUnsupportedCopied: "여기서는 공유가 지원되지 않습니다 — 대신 텍스트가 복사되었습니다.",
  toastImageDownloadedClipboardFailed: "이미지가 다운로드되었습니다 — 텍스트 복사에 실패했습니다.",
  toastShareUnsupportedDevice: "이 기기에서는 공유가 지원되지 않습니다.",
  toastImageDownloaded: "이미지가 기기에 다운로드되었습니다.",
  toastShareUnsupportedAtAll: "이 기기에서는 공유가 지원되지 않습니다.",
  errTooShort: "강의계획서 텍스트를 더 입력해 주세요 — 분석하기에 너무 짧습니다.",
  errParseFailed: "문서를 분석하는 중 문제가 발생했습니다. 대신 텍스트를 붙여넣어 보세요.",
  errNotPDF: ".pdf 파일을 놓아 주세요.",
  errPDFNoText: "해당 PDF에서 텍스트를 읽을 수 없습니다 — 강의계획서 텍스트를 붙여넣어 보세요.",
  errPDFReadFailed: "해당 PDF를 읽지 못했습니다. 강의계획서 텍스트를 붙여넣어 보세요.",
  dropTitleDefault: "강의계획서 PDF 업로드",
  dropSubtitleDefault: "탭하여 선택하거나 파일을 여기로 끌어다 놓으세요",
  dropTitleReading: "PDF 읽는 중…",
  calendarModalSubtitleMulti: (label, display, count) => `Google, Outlook, Yahoo는 다음 마감일 "${label}"(${display})을 빠르게 추가합니다. Apple/.ics에는 ${count}개의 마감일이 모두 포함됩니다.`,
  calendarModalSubtitleSingle: (label, display) => `"${label}"(${display})을 캘린더에 추가합니다.`,
};'''

T_BLOCKS['hi'] = r'''window.T = {
  untitledCourse: "बिना शीर्षक वाला कोर्स",
  courseDetailsUnavailable: "कोर्स विवरण उपलब्ध नहीं है",
  referToProfessor: "अपने प्रोफेसर से पूछें",
  gradesEmptyState: "सटीक ग्रेड वेटेज के लिए प्रोफेसर से पूछें।",
  deadlinesEmptyState: "मुख्य तारीखों के लिए प्रोफेसर से पूछें।",
  flagLabels: { "Due": "देय तिथि", "Submission": "सबमिशन", "Test": "टेस्ट", "Exam": "परीक्षा", "Midterm": "मिडटर्म", "Final": "फाइनल", "Quiz": "क्विज़", "Project Due": "प्रोजेक्ट देय तिथि", "Presentation": "प्रेजेंटेशन", "Paper Due": "पेपर देय तिथि" },
  gradeCategoryLabels: {"Final Exam": "फाइनल परीक्षा", "Midterm": "मिडटर्म", "Exams": "परीक्षाएं", "Quizzes": "क्विज़", "Projects": "प्रोजेक्ट्स", "Assignments": "असाइनमेंट्स", "Homework": "होमवर्क", "Participation": "सहभागिता", "Attendance": "उपस्थिति", "Papers": "पेपर्स", "Labs": "लैब्स", "Presentations": "प्रेजेंटेशन", "Discussion": "चर्चा", "Essays": "निबंध"},
  termSeasonLabels: {"Fall": "फॉल", "Spring": "स्प्रिंग", "Summer": "समर", "Winter": "विंटर"},
  weekLabelTemplate: (n) => `सप्ताह ${n}`,
  preparingLabel: "तैयार हो रहा है…",
  toastNoExactDates: "डेडलाइन में केवल सप्ताह संख्या दी गई है — अभी सिंक करने के लिए कोई सटीक तारीख नहीं है।",
  toastNoDatesFound: "कोई विशिष्ट तारीख नहीं मिली — अभी सिंक करने के लिए कुछ नहीं है।",
  toastICSDownloaded: "कैलेंडर फ़ाइल डाउनलोड हो गई — इम्पोर्ट करने के लिए टैप करें।",
  shareGradesSummarized: "ग्रेड सारांशित",
  shareDeadlinesOrganized: "डेडलाइन व्यवस्थित",
  shareCaptionTemplate: (title, topGrade, nextDue) => `📚 ${title} — 2 सेकंड में सरल बनाया गया।\n${topGrade}। ${nextDue}।\n\nटेक्स्ट की दीवार को भूल जाइए:`,
  shareTopGradeTemplate: (label, weight) => `${label} आपके ग्रेड का ${weight}% है`,
  shareNextDueTemplate: (label, display) => `अगला: ${label}, ${display}`,
  toastSharedCopied: "शेयर हो गया! टेक्स्ट भी कॉपी हो गया — अगर अपने आप न आए तो पेस्ट करें।",
  toastShareCancelled: "शेयर करना रद्द किया गया।",
  toastImageDownloadedCopied: "इमेज डाउनलोड हो गई और टेक्स्ट कॉपी हो गया — शेयर करने के लिए अटैच करें और पेस्ट करें!",
  toastShareUnsupportedCopied: "यहाँ शेयर करना समर्थित नहीं है — इसके बजाय टेक्स्ट कॉपी किया गया।",
  toastImageDownloadedClipboardFailed: "इमेज डाउनलोड हो गई — टेक्स्ट कॉपी नहीं हो सका।",
  toastShareUnsupportedDevice: "इस डिवाइस पर शेयर करना समर्थित नहीं है।",
  toastImageDownloaded: "इमेज आपके डिवाइस पर डाउनलोड हो गई।",
  toastShareUnsupportedAtAll: "इस डिवाइस पर शेयर करना समर्थित नहीं है।",
  errTooShort: "पाठ्यक्रम का और अधिक टेक्स्ट दें — यह विश्लेषण के लिए बहुत छोटा लगता है।",
  errParseFailed: "दस्तावेज़ का विश्लेषण करते समय कुछ गलत हो गया। इसके बजाय टेक्स्ट पेस्ट करने का प्रयास करें।",
  errNotPDF: "कृपया एक .pdf फ़ाइल छोड़ें।",
  errPDFNoText: "उस PDF से टेक्स्ट नहीं पढ़ा जा सका — पाठ्यक्रम का टेक्स्ट पेस्ट करने का प्रयास करें।",
  errPDFReadFailed: "उस PDF को पढ़ने में विफल। पाठ्यक्रम का टेक्स्ट पेस्ट करने का प्रयास करें।",
  dropTitleDefault: "पाठ्यक्रम PDF अपलोड करें",
  dropSubtitleDefault: "चुनने के लिए टैप करें या फ़ाइल यहाँ छोड़ें",
  dropTitleReading: "PDF पढ़ा जा रहा है…",
  calendarModalSubtitleMulti: (label, display, count) => `Google, Outlook और Yahoo आपकी अगली डेडलाइन — "${label}" (${display}) — जल्दी से जोड़ देते हैं। Apple/.ics में सभी ${count} डेडलाइन शामिल हैं।`,
  calendarModalSubtitleSingle: (label, display) => `"${label}" (${display}) को अपने कैलेंडर में जोड़ें।`,
};'''

T_BLOCKS['ar'] = r'''window.T = {
  untitledCourse: "مقرر بدون عنوان",
  courseDetailsUnavailable: "تفاصيل المقرر غير متوفرة",
  referToProfessor: "راجع أستاذك",
  gradesEmptyState: "راجع أستاذك لمعرفة الأوزان الدقيقة.",
  deadlinesEmptyState: "راجع أستاذك لمعرفة التواريخ المهمة.",
  flagLabels: { "Due": "الاستحقاق", "Submission": "التسليم", "Test": "اختبار", "Exam": "امتحان", "Midterm": "امتحان منتصف الفصل", "Final": "الامتحان النهائي", "Quiz": "اختبار قصير", "Project Due": "تسليم المشروع", "Presentation": "عرض تقديمي", "Paper Due": "تسليم البحث" },
  gradeCategoryLabels: {"Final Exam": "الامتحان النهائي", "Midterm": "امتحان منتصف الفصل", "Exams": "الامتحانات", "Quizzes": "الاختبارات القصيرة", "Projects": "المشاريع", "Assignments": "الواجبات", "Homework": "الواجبات المنزلية", "Participation": "المشاركة", "Attendance": "الحضور", "Papers": "الأبحاث", "Labs": "المعامل", "Presentations": "العروض التقديمية", "Discussion": "المناقشة", "Essays": "المقالات"},
  termSeasonLabels: {"Fall": "الخريف", "Spring": "الربيع", "Summer": "الصيف", "Winter": "الشتاء"},
  weekLabelTemplate: (n) => `الأسبوع ${n}`,
  preparingLabel: "جارٍ التحضير…",
  toastNoExactDates: "المواعيد النهائية تذكر رقم الأسبوع فقط — لا توجد تواريخ دقيقة للمزامنة بعد.",
  toastNoDatesFound: "لم يتم العثور على تواريخ محددة — لا يوجد شيء للمزامنة بعد.",
  toastICSDownloaded: "تم تنزيل ملف التقويم — اضغط لاستيراده.",
  shareGradesSummarized: "تم تلخيص الدرجات",
  shareDeadlinesOrganized: "تم تنظيم المواعيد النهائية",
  shareCaptionTemplate: (title, topGrade, nextDue) => `📚 ${title} — تم التبسيط خلال ثانيتين.\n${topGrade}. ${nextDue}.\n\nتجاوز جدار النص:`,
  shareTopGradeTemplate: (label, weight) => `${label} يمثل ${weight}% من درجتك`,
  shareNextDueTemplate: (label, display) => `القادم: ${label} في ${display}`,
  toastSharedCopied: "تمت المشاركة! تم نسخ النص أيضًا — الصقه إذا لم يظهر تلقائيًا.",
  toastShareCancelled: "تم إلغاء المشاركة.",
  toastImageDownloadedCopied: "تم تنزيل الصورة ونسخ النص — أرفقهما والصق النص للمشاركة!",
  toastShareUnsupportedCopied: "المشاركة غير مدعومة هنا — تم نسخ النص بدلاً من ذلك.",
  toastImageDownloadedClipboardFailed: "تم تنزيل الصورة — تعذّر نسخ النص.",
  toastShareUnsupportedDevice: "المشاركة غير مدعومة على هذا الجهاز.",
  toastImageDownloaded: "تم تنزيل الصورة على جهازك.",
  toastShareUnsupportedAtAll: "المشاركة غير مدعومة على هذا الجهاز.",
  errTooShort: "أدخل المزيد من نص المقرر — يبدو هذا قصيرًا جدًا للتحليل.",
  errParseFailed: "حدث خطأ أثناء تحليل المستند. حاول لصق النص بدلاً من ذلك.",
  errNotPDF: "يرجى إسقاط ملف .pdf.",
  errPDFNoText: "تعذّرت قراءة النص من ملف PDF هذا — حاول لصق نص المقرر.",
  errPDFReadFailed: "فشلت قراءة ملف PDF هذا. حاول لصق نص المقرر.",
  dropTitleDefault: "رفع ملف PDF لمخطط المقرر",
  dropSubtitleDefault: "اضغط للاختيار أو أفلت الملف هنا",
  dropTitleReading: "جارٍ قراءة PDF…",
  calendarModalSubtitleMulti: (label, display, count) => `يضيف Google وOutlook وYahoo موعدك النهائي القادم بسرعة — "${label}" (${display}). يتضمن Apple/.ics جميع المواعيد الـ ${count}.`,
  calendarModalSubtitleSingle: (label, display) => `أضف "${label}" (${display}) إلى تقويمك.`,
};'''

for _lang in LANG_ORDER:
    if _lang == 'en':
        continue
    assert _lang in T_BLOCKS, f'missing T_BLOCKS for {_lang}'

# ---------------------------------------------------------------------------
# Core generation logic
# ---------------------------------------------------------------------------

def extract_protected_block(text):
    """Splits the master template into (before, protected, after).
    `protected` runs from `const GRADE_KEYWORDS` up to (not including)
    `function renderDashboard` and must never be touched by translation."""
    start_m = PROTECTED_START_RE.search(text)
    end_m = PROTECTED_END_RE.search(text)
    if not start_m or not end_m or end_m.start() <= start_m.start():
        raise RuntimeError('could not locate the protected parser-engine block')
    return text[:start_m.start()], text[start_m.start():end_m.start()], text[end_m.start():]


def replace_between_markers(text, start_marker, end_marker, new_inner):
    pattern = re.compile(re.escape(start_marker) + r'.*?' + re.escape(end_marker), re.S)
    new_block = start_marker + '\n' + new_inner + '\n' + end_marker
    new_text, count = pattern.subn(lambda m, b=new_block: b, text, count=1)
    if count != 1:
        raise RuntimeError(f'marker block not found or duplicated: {start_marker}')
    return new_text


def apply_static_replacements(text, en_list, tr_list, lang, label):
    # Some buttons are legitimately duplicated verbatim in two places on the
    # page (e.g. "Sync to Calendar (.ics)" / "Share Smart-Card" each appear
    # above and below the summary card — see the source comment about the
    # two Share Smart-Card buttons). Both instances always want the same
    # translation, so replace every occurrence rather than requiring exactly
    # one; only a zero-count (a truly missing/renamed string) is an error.
    # Pairs are applied longest-EN-string-first so a more-specific/longer
    # match (e.g. the 24-space-indented button) is consumed before a
    # shorter one that happens to be a whitespace-prefixed substring of it
    # (e.g. the 20-space-indented duplicate of the same button text).
    for en, tr in sorted(zip(en_list, tr_list), key=lambda pair: -len(pair[0])):
        count = text.count(en)
        if count < 1:
            raise RuntimeError(
                f'[{lang}] {label}: expected at least 1 occurrence of {en!r}, found 0'
            )
        text = text.replace(en, tr)
    return text


def build_hreflang_block(lang):
    home = LANG_META[lang]['home']
    canonical_url = 'https://syllabustldr.com' + home
    lines = [f'<link rel="canonical" href="{canonical_url}">']
    for code in LANG_ORDER:
        h = LANG_META[code]['hreflang']
        url = 'https://syllabustldr.com' + LANG_META[code]['home']
        lines.append(f'<link rel="alternate" hreflang="{h}" href="{url}">')
    lines.append('<link rel="alternate" hreflang="x-default" href="https://syllabustldr.com/">')
    return '\n'.join(lines)


def flag_span(code, extra_class=''):
    cls = f'inline-block w-5 h-3.5 rounded-[2px] overflow-hidden shrink-0{extra_class}'
    return f'<span aria-hidden="true" class="{cls}">{FLAG_SVGS[code]}</span>'


def build_switcher_block(current_lang):
    lines = []
    for code in LANG_ORDER:
        meta = LANG_META[code]
        url = 'https://syllabustldr.com' + meta['home']
        active = code == current_lang
        cls = 'text-white bg-zinc-800/70' if active else 'text-zinc-300 hover:bg-zinc-800 hover:text-white transition'
        lines.append(f'                        <a href="{url}" class="flex items-center justify-between gap-2.5 px-3.5 py-2.5 text-xs font-semibold {cls}">')
        lines.append(f'                            <span>{meta["name"]}</span> {flag_span(code)}')
        lines.append('                        </a>')
    return '\n'.join(lines)


def build_switcher_button(current_lang):
    code_label = LANG_META[current_lang]['hreflang'].split('-')[0].upper()
    return (
        f'                        <span class="sr-only sm:not-sr-only">{code_label}</span>\n'
        f'                        {flag_span(current_lang)}'
    )


MAIN_SCRIPT_ANCHOR_RE = re.compile(
    r"\n<script>\n\(function \(\) \{\n  'use strict';\n\n  // -+\n  // TRANSLATIONS"
)


def inject_t_block(text, lang):
    """Inserts a translated `<script>window.T = {...};</script>` right
    before the shared engine's <script> tag, so that block's own
    `window.T = window.T || {...}` (English defaults) becomes a no-op."""
    m = MAIN_SCRIPT_ANCHOR_RE.search(text)
    if not m:
        raise RuntimeError(f'[{lang}] could not find main engine <script> anchor to inject T block before')
    script_tag = f'<script>\n{T_BLOCKS[lang]}\n</script>\n'
    insert_at = m.start()
    return text[:insert_at] + '\n' + script_tag + text[insert_at:]


PROTECTED_PLACEHOLDER = '@@PROTECTED_PARSER_BLOCK_PLACEHOLDER@@'


def generate(lang, master_text):
    before, protected, after = extract_protected_block(master_text)
    # A placeholder token stands in for the protected block through every
    # transformation below, so the splice point never depends on tracking
    # byte offsets across length-changing edits (hreflang/switcher block
    # regeneration and static-string substitution both change length).
    combined = before + PROTECTED_PLACEHOLDER + after

    combined = replace_between_markers(
        combined, '<!-- HREFLANG_BLOCK_START -->', '<!-- HREFLANG_BLOCK_END -->', build_hreflang_block(lang)
    )
    combined = replace_between_markers(
        combined, '<!-- LANG_SWITCHER_MENU_START -->', '<!-- LANG_SWITCHER_MENU_END -->', build_switcher_block(lang)
    )
    combined = replace_between_markers(
        combined, '<!-- LANG_SWITCHER_BUTTON_START -->', '<!-- LANG_SWITCHER_BUTTON_END -->', build_switcher_button(lang)
    )

    if lang != 'en':
        combined = apply_static_replacements(combined, EXISTING_STATIC_EN, EXISTING_STATIC_TR[lang], lang, 'existing-static')
        combined = apply_static_replacements(combined, NEW_STATIC_EN, NEW_STATIC_TR[lang], lang, 'new-static')
        combined = inject_t_block(combined, lang)

    count = combined.count(PROTECTED_PLACEHOLDER)
    if count != 1:
        raise RuntimeError(f'[{lang}] protected-block placeholder found {count} times, expected 1')
    return combined.replace(PROTECTED_PLACEHOLDER, protected, 1)


def main():
    master_text = MASTER.read_text(encoding='utf-8')

    for lang in LANG_ORDER:
        out = generate(lang, master_text)
        if lang == 'en':
            out_path = MASTER
        else:
            out_dir = ROOT / lang
            out_dir.mkdir(exist_ok=True)
            out_path = out_dir / 'index.html'
        out_path.write_text(out, encoding='utf-8', newline='\n')
        print(f'wrote {out_path.relative_to(ROOT)} ({len(out)} bytes)')


if __name__ == '__main__':
    main()
