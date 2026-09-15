"""
One-off script: add a reciprocal "Our Network" footer block to every page.

syllabustldr.com is one of 9 EIGHTFINITY LTD platforms, and every sibling
site already links to syllabustldr.com in its own footer -- but
syllabustldr.com never linked back to any of them. This adds the same
8-site reciprocal list eightfinity.net's own homepage "Platforms we
operate" section uses (every other platform, not itself), inserted right
before the "operated by EIGHTFINITY LTD" line in the footer.

Applies uniformly across all languages (proper-noun links, so no
translation needed) -- including the 9 gen_i18n.py-generated homepages,
which is safe: this script also patches the English master index.html, so
a future gen_i18n.py re-run will carry this block forward automatically.

Idempotent: files that already contain the network block are skipped.

Usage: python scripts/add_network_footer.py
"""
import glob

MARKER = 'href="https://propertyalert.uk"'

NETWORK_BLOCK = (
    '        <div class="flex flex-wrap items-center justify-center gap-x-3 gap-y-1 mb-2 text-[11px]">\n'
    '            <span class="text-zinc-700">Also part of the EIGHTFINITY network:</span>\n'
    '            <a href="https://propertyalert.uk" target="_blank" rel="noopener" class="text-zinc-600 hover:text-zinc-400 transition">PropertyAlert.uk</a>\n'
    '            <span class="text-zinc-800">\xb7</span>\n'
    '            <a href="https://propertybrain.uk" target="_blank" rel="noopener" class="text-zinc-600 hover:text-zinc-400 transition">PropertyBrain.uk</a>\n'
    '            <span class="text-zinc-800">\xb7</span>\n'
    '            <a href="https://howmuchismyhomeworth.uk" target="_blank" rel="noopener" class="text-zinc-600 hover:text-zinc-400 transition">HowMuchIsMyHomeWorth.uk</a>\n'
    '            <span class="text-zinc-800">\xb7</span>\n'
    '            <a href="https://groundlayer.co.uk" target="_blank" rel="noopener" class="text-zinc-600 hover:text-zinc-400 transition">Groundlayer.co.uk</a>\n'
    '            <span class="text-zinc-800">\xb7</span>\n'
    '            <a href="https://bestgiftsfor.net" target="_blank" rel="noopener" class="text-zinc-600 hover:text-zinc-400 transition">BestGiftsFor.net</a>\n'
    '            <span class="text-zinc-800">\xb7</span>\n'
    '            <a href="https://lawcheck.co.uk" target="_blank" rel="noopener" class="text-zinc-600 hover:text-zinc-400 transition">LawCheck.co.uk</a>\n'
    '            <span class="text-zinc-800">\xb7</span>\n'
    '            <a href="https://legalroute.co.uk" target="_blank" rel="noopener" class="text-zinc-600 hover:text-zinc-400 transition">LegalRoute.co.uk</a>\n'
    '            <span class="text-zinc-800">\xb7</span>\n'
    '            <a href="https://ukimmigrationadvice.co.uk" target="_blank" rel="noopener" class="text-zinc-600 hover:text-zinc-400 transition">UKImmigrationAdvice.co.uk</a>\n'
    '            <span class="text-zinc-800">\xb7</span>\n'
    '            <a href="https://eightfinity.net" target="_blank" rel="noopener" class="text-zinc-600 hover:text-zinc-400 transition">EIGHTFINITY.net</a>\n'
    '        </div>\n'
)

ANCHOR = '        <p class="text-[11px] text-zinc-600">'


def process(path):
    with open(path, encoding='utf-8') as f:
        content = f.read()

    if '<footer' not in content:
        return False
    if MARKER in content:
        print('SKIP (already has network block):', path)
        return False
    if ANCHOR not in content:
        print('SKIP (anchor not found -- check manually):', path)
        return False

    content = content.replace(ANCHOR, NETWORK_BLOCK + ANCHOR, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Added network block:', path)
    return True


def main():
    files = sorted(glob.glob('**/*.html', recursive=True))
    files = [f for f in files if 'node_modules' not in f and 'syllabus from google' not in f]
    changed = 0
    for f in files:
        if process(f):
            changed += 1
    print(f'Updated {changed}/{len(files)} files')


if __name__ == '__main__':
    main()
