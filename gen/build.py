#!/usr/bin/env python3
"""Builds kroky.nakolini.com: every page in all 49 of the app's languages, plus sitemap, robots.txt and llms.txt.

Python 3.9+ standard library only. Run from anywhere: python3 gen/build.py
Copy is in i18n/<lang>.json (en.json is the source), the App Store names and the screenshot captions are in data/,
and the output is written to the repo root, which GitHub Pages serves as is.
"""
import decimal, hashlib, html, json, os, re, shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASE_URL = "https://kroky.nakolini.com"
APP_ID = "6824215298"
# App Store Connect provider token (the pt= of a campaign link). Without it the App Store ignores ct= in Analytics.
PROVIDER_TOKEN = ""
STUDIO_URL = "https://nakolini.com/"
STUDIO_LOGO = "https://nakolini.com/assets/logo/nakolini-mark-tile.png"
EMAIL = "support@kroky.nakolini.com"
EULA_URL = "https://www.apple.com/legal/internet-services/itunes/dev/stdeula/"
OTHER_APPS = [("footer.anonimo", "https://anonimo.nakolini.com/"),
              ("footer.expenny", "https://expenny.nakolini.com/"),
              ("footer.prospekt", "https://prospekt.nakolini.com/")]
# Bump when the pages change meaningfully: sitemap lastmod and JSON-LD dateModified.
SITE_UPDATED = "2026-10-25"

# (code: hreflang, <html lang> and the app's language code; URL segment; name in that language)
LANGUAGES = [
    ("en", "", "English"),
    ("ar", "ar", "العربية"),
    ("bn", "bn", "বাংলা"),
    ("ca", "ca", "Català"),
    ("cs", "cs", "Čeština"),
    ("da", "da", "Dansk"),
    ("de", "de", "Deutsch"),
    ("el", "el", "Ελληνικά"),
    ("en-AU", "en-au", "English (Australia)"),
    ("en-GB", "en-gb", "English (UK)"),
    ("es", "es", "Español (España)"),
    ("es-419", "es-419", "Español (Latinoamérica)"),
    ("fi", "fi", "Suomi"),
    ("fr", "fr", "Français"),
    ("fr-CA", "fr-ca", "Français (Canada)"),
    ("gu", "gu", "ગુજરાતી"),
    ("he", "he", "עברית"),
    ("hi", "hi", "हिन्दी"),
    ("hr", "hr", "Hrvatski"),
    ("hu", "hu", "Magyar"),
    ("id", "id", "Bahasa Indonesia"),
    ("it", "it", "Italiano"),
    ("ja", "ja", "日本語"),
    ("kn", "kn", "ಕನ್ನಡ"),
    ("ko", "ko", "한국어"),
    ("ml", "ml", "മലയാളം"),
    ("mr", "mr", "मराठी"),
    ("ms", "ms", "Bahasa Melayu"),
    ("nb", "nb", "Norsk bokmål"),
    ("nl", "nl", "Nederlands"),
    ("or", "or", "ଓଡ଼ିଆ"),
    ("pa", "pa", "ਪੰਜਾਬੀ"),
    ("pl", "pl", "Polski"),
    ("pt-BR", "pt-br", "Português (Brasil)"),
    ("pt-PT", "pt-pt", "Português (Portugal)"),
    ("ro", "ro", "Română"),
    ("ru", "ru", "Русский"),
    ("sk", "sk", "Slovenčina"),
    ("sl", "sl", "Slovenščina"),
    ("sv", "sv", "Svenska"),
    ("ta", "ta", "தமிழ்"),
    ("te", "te", "తెలుగు"),
    ("th", "th", "ไทย"),
    ("tr", "tr", "Türkçe"),
    ("uk", "uk", "Українська"),
    ("ur", "ur", "اردو"),
    ("vi", "vi", "Tiếng Việt"),
    ("zh-Hans", "zh-hans", "简体中文"),
    ("zh-Hant", "zh-hant", "繁體中文"),
]
RTL = {"ar", "he", "ur"}
# Open Graph wants language_TERRITORY.
OG_LOCALE = {"en": "en_US", "en-GB": "en_GB", "en-AU": "en_AU", "es": "es_ES", "es-419": "es_LA", "fr": "fr_FR",
             "fr-CA": "fr_CA", "pt-BR": "pt_BR", "pt-PT": "pt_PT", "zh-Hans": "zh_CN", "zh-Hant": "zh_TW", "ar": "ar_AR",
             "bn": "bn_IN", "ca": "ca_ES", "cs": "cs_CZ", "da": "da_DK", "de": "de_DE", "el": "el_GR", "fi": "fi_FI",
             "gu": "gu_IN", "he": "he_IL", "hi": "hi_IN", "hr": "hr_HR", "hu": "hu_HU", "id": "id_ID", "it": "it_IT",
             "ja": "ja_JP", "kn": "kn_IN", "ko": "ko_KR", "ml": "ml_IN", "mr": "mr_IN", "ms": "ms_MY", "nb": "nb_NO",
             "nl": "nl_NL", "or": "or_IN", "pa": "pa_IN", "pl": "pl_PL", "ro": "ro_RO", "ru": "ru_RU", "sk": "sk_SK",
             "sl": "sl_SI", "sv": "sv_SE", "ta": "ta_IN", "te": "te_IN", "th": "th_TH", "tr": "tr_TR", "uk": "uk_UA",
             "ur": "ur_PK", "vi": "vi_VN"}
# Distance units as each language writes them after a number.
UNITS = {
    "ja": ("m", "km"), "ko": ("m", "km"), "zh-Hans": ("\u00a0米", "\u00a0公里"), "zh-Hant": ("\u00a0公尺", "\u00a0公里"),
    "ru": ("\u00a0м", "\u00a0км"), "uk": ("\u00a0м", "\u00a0км"), "el": ("\u00a0μ.", "\u00a0χλμ."),
    "ar": ("\u00a0م", "\u00a0كم"), "ur": ("\u00a0میٹر", "\u00a0کلومیٹر"), "he": ("\u00a0מ׳", "\u00a0ק״מ"),
    "hi": ("\u00a0मी", "\u00a0किमी"), "mr": ("\u00a0मी", "\u00a0किमी"), "bn": ("\u00a0মি", "\u00a0কিমি"),
    "gu": ("\u00a0મી", "\u00a0કિમી"), "kn": ("\u00a0ಮೀ", "\u00a0ಕಿ.ಮೀ"), "ml": ("\u00a0മീ.", "\u00a0കി.മീ."),
    "or": ("\u00a0ମି", "\u00a0କିମି"), "pa": ("\u00a0ਮੀ.", "\u00a0ਕਿ.ਮੀ."), "ta": ("\u00a0மீ", "\u00a0கிமீ"),
    "te": ("\u00a0మీ", "\u00a0కి.మీ"), "th": ("\u00a0ม.", "\u00a0กม."),
}
# Languages whose copy writes numbers in their own digits.
NATIVE_DIGITS = {"bn": str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")}
# Languages that end a sentence with a danda.
DANDA = {"hi", "bn", "pa", "or"}
CJK_STOP = {"ja", "zh-Hans", "zh-Hant"}
# Thousands and decimal separators. Spanish, Polish and European Portuguese leave four-digit numbers unseparated.
NBSP, NNBSP = " ", " "
DOT_GROUP = {"de", "da", "es", "id", "it", "nl", "pt-BR", "ro", "tr", "el", "hr", "sl", "ca", "vi"}
SPACE_GROUP = {"fr": NNBSP, "fr-CA": NBSP, "cs": NBSP, "sk": NBSP, "ru": NBSP, "uk": NBSP, "pl": NBSP, "fi": NBSP,
               "nb": NBSP, "sv": NBSP, "hu": NBSP, "pt-PT": NBSP}
NO_GROUP_UNDER_10K = {"es", "hu", "pl", "pt-PT", "sl"}
SHOTS = ["route", "home", "guide", "nudge", "walk", "settings"]
GUIDES = ["g1", "g2", "g3"]
# Stride and pace the step table assumes: the app's defaults before it learns the walker's own (StrideCalibration).
STRIDE_M, PACE_M_PER_MIN = 0.75, 75  # 100 steps a minute
TABLE_STEPS = [1000, 2000, 3000, 4000, 5000, 8000, 10000]

# Generated paths, removed before each build so stale pages never linger.
GENERATED_DIRS = ["guides"] + [s for _, s, _ in LANGUAGES if s]
GENERATED_FILES = ["index.html", "support.html", "privacy-policy.html", "terms.html", "404.html", "sitemap.xml",
                   "robots.txt", "llms.txt", ".nojekyll", "CNAME"]


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return json.load(f)


STORE = load("data/store.json")
CAPTIONS = load("data/captions.json")
EN = load("i18n/en.json")


def e(text):
    return html.escape(str(text), quote=True)


def plain(text):
    """Text without tags or entities, for meta tags, JSON-LD and llms.txt."""
    return html.unescape(re.sub(r"<br\s*/?>", " ", re.sub(r"<(?!br)[^>]+>", "", text))).replace("  ", " ").strip()


def asset_url(path):
    """An asset's path with a hash of its content, so a deploy never pairs new pages with a cached old file."""
    with open(os.path.join(ROOT, path), "rb") as f:
        return "/%s?v=%s" % (path, hashlib.sha256(f.read()).hexdigest()[:10])


def app_store_url(campaign):
    query = "ct=%s&mt=8" % campaign
    if PROVIDER_TOKEN:
        query = "pt=%s&%s" % (PROVIDER_TOKEN, query)
    return "https://apps.apple.com/app/apple-store/id%s?%s" % (APP_ID, query)


class Lang:
    def __init__(self, code, segment, name):
        self.code, self.segment, self.name = code, segment, name
        path = os.path.join(ROOT, "i18n", code + ".json")
        self.strings = load("i18n/%s.json" % code) if os.path.exists(path) else {}
        self.dir = "rtl" if code in RTL else "ltr"
        self.store = STORE.get(code, STORE["en"])
        self.captions = CAPTIONS.get(code, CAPTIONS["en"])
        self.english = code.startswith("en")

    @property
    def prefix(self):
        return "/" + self.segment + "/" if self.segment else "/"

    def raw(self, key):
        value = self.strings.get(key)
        if value is None:
            value = EN[key]
        return value

    def t(self, key, **values):
        text = self.raw(key)
        base = dict(privacy=self.prefix + "privacy-policy.html", terms=self.prefix + "terms.html",
                    support=self.prefix + "support.html", eula=EULA_URL,
                    email='<a href="mailto:%s">%s</a>' % (EMAIL, EMAIL), english="")
        base.update(values)
        for k, v in base.items():
            text = text.replace("{%s}" % k, str(v))
        return text

    def num(self, n, decimals=0):
        # Halves round up (2.25 km → 2.3), as people expect, not to the even digit.
        n = decimal.Decimal(repr(n)).quantize(decimal.Decimal(1).scaleb(-decimals), decimal.ROUND_HALF_UP)
        s = "{:,.{d}f}".format(n, d=decimals)
        group, dec = ",", "."
        if self.code in DOT_GROUP:
            group, dec = ".", ","
        elif self.code in SPACE_GROUP:
            group, dec = SPACE_GROUP[self.code], ","
        if self.code in NO_GROUP_UNDER_10K and abs(n) < 10000:
            group = ""
        s = s.replace(",", "\x00").replace(".", dec).replace("\x00", group)
        return s.translate(NATIVE_DIGITS[self.code]) if self.code in NATIVE_DIGITS else s


ALL_LANGS = [Lang(*row) for row in LANGUAGES]
EN_LANG = ALL_LANGS[0]


def url_for(lang, path):
    return BASE_URL + lang.prefix + path


# ---------------------------------------------------------------- page chrome

ICONS = {
    # Simple 24 px stroke icons in the spirit of SF Symbols, drawn here so the site loads no icon font.
    "sit": '<circle cx="13" cy="4" r="2"/><path d="m9 21 2.5-6 2.5 2v4"/><path d="M11.5 15 12 9l-3 2-1.5 3"/><path d="m12 9 2 3 3 1"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "loop": '<path d="M20 12a8 8 0 1 1-2.34-5.66"/><path d="M20 4v4h-4"/>',
    "map": '<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/>',
    "star": '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/>',
    "phone": '<rect x="6" y="2" width="12" height="20" rx="3"/><path d="M10 5h4"/>',
    "person": '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
    "shield": '<path d="M12 3 4 6v6c0 4.5 3.4 8.3 8 9 4.6-.7 8-4.5 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
}


def icon(name):
    return ('<svg class="icon" viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" fill="none" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">%s</svg>' % ICONS[name])


BADGE_DIR = os.path.join(ROOT, "assets", "badges")


def badge_file(code):
    return code if os.path.exists(os.path.join(BADGE_DIR, code + ".svg")) else "en"


def badge_ratio(code):
    with open(os.path.join(BADGE_DIR, badge_file(code) + ".svg"), encoding="utf-8") as f:
        box = re.search(r'viewBox="([\d.\s-]+)"', f.read(3000)).group(1).split()
    return float(box[2]) / float(box[3])


def store_badge(lang, campaign, height=54, cls="badge"):
    """Apple's "Download on the App Store" badge, unaltered, in the page's language where Apple offers one.

    Apple's marketing guidelines: the official artwork, at least 40 px tall on screen, with clear space around it
    of at least a quarter of its height (the .badge margin), and the English badge where no localized one exists.
    """
    return '<a class="%s" href="%s"><img src="/assets/badges/%s.svg" width="%d" height="%d" alt="%s" lang="%s"></a>' % (
        cls, e(app_store_url(campaign)), badge_file(lang.code), round(badge_ratio(lang.code) * height), height,
        e(lang.t("badge.alt")), lang.code)


def lang_switch(lang, path):
    items = "".join(
        '<li><a href="%s" hreflang="%s" lang="%s"%s>%s</a></li>' % (
            other.prefix + path, other.code, other.code,
            ' aria-current="page"' if other is lang else "", e(other.name))
        for other in ALL_LANGS)
    return ('<details class="lang"><summary aria-label="%s">%s<span>%s</span></summary><ul>%s</ul></details>'
            % (e(lang.t("nav.language")), icon("globe"), e(lang.name), items))


def header(lang, path):
    home = lang.prefix
    return """<a class="skip" href="#main">{skip}</a>
<header class="site-header"><div class="wrap bar">
<a class="brand" href="{home}"><img src="/assets/icon-64.png" width="32" height="32" alt="">Kroky</a>
<nav class="nav" aria-label="Kroky"><a href="{home}#how">{how}</a><a href="{home}#faq">{faq}</a><a href="{home}guides/">{guides}</a></nav>
{switch}
</div></header>""".format(skip=lang.t("nav.skip"), home=home, how=lang.t("nav.how"), faq=lang.t("nav.faq"),
                          guides=lang.t("nav.guides"), switch=lang_switch(lang, path))


def footer(lang):
    home = lang.prefix
    studio = '<a href="%s">%s</a>' % (STUDIO_URL, lang.t("footer.studio"))
    apps = " · ".join('<a href="%s">%s</a>' % (url, lang.t(key)) for key, url in OTHER_APPS)
    return """<footer class="site-footer"><div class="wrap">
<p class="maker"><a class="maker-logo" href="{studio_url}" aria-hidden="true" tabindex="-1"><img src="/assets/nakolini-mark.png" alt="" width="20" height="20"></a><span>{made}</span></p>
<p>{also} {apps}</p>
<p><a href="{home}support.html">{support}</a> · <a href="{home}privacy-policy.html">{privacy}</a> · <a href="{home}terms.html">{terms}</a> · <a href="{home}guides/">{guides}</a></p>
<p class="fine">{copyright}</p>
</div></footer>""".format(
        studio_url=STUDIO_URL, made=lang.t("footer.made_by", studio=studio), also=lang.t("footer.also"), apps=apps,
        home=home, support=lang.t("footer.support"), privacy=lang.t("footer.privacy"), terms=lang.t("footer.terms"),
        guides=lang.t("nav.guides"), copyright=lang.t("footer.copyright"))


def jsonld_script(block):
    return '<script type="application/ld+json">%s</script>\n' % json.dumps(block, ensure_ascii=False).replace("</", "<\\/")


def render(lang, path, title, description, body, jsonld=(), og_image=None, noindex=False):
    canonical = url_for(lang, path)
    if noindex:
        links = '<meta name="robots" content="noindex">\n'
    else:
        links = '<link rel="canonical" href="%s">\n' % e(canonical)
        links += "".join('<link rel="alternate" hreflang="%s" href="%s">\n' % (o.code, e(url_for(o, path)))
                         for o in ALL_LANGS)
        links += '<link rel="alternate" hreflang="x-default" href="%s">\n' % e(url_for(EN_LANG, path))
    og_image = og_image or "%s/og/%s.png" % (BASE_URL, lang.code)
    return """<!doctype html>
<html lang="{code}" dir="{dir}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
{links}<meta property="og:type" content="website">
<meta property="og:site_name" content="Kroky">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{og_locale}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1D6B4B">
<meta name="color-scheme" content="light dark">
<meta name="apple-itunes-app" content="app-id={app_id}">
<link rel="icon" href="/favicon.ico" sizes="16x16 32x32 48x48">
<link rel="icon" type="image/png" sizes="192x192" href="/assets/icon-192.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="{css}">
{jsonld}</head>
<body>
{header}
<main id="main">
{body}
</main>
{footer}
</body>
</html>
""".format(code="en-US" if lang.code == "en" else lang.code, dir=lang.dir, title=e(plain(title)), description=e(plain(description)), links=links,
           canonical=e(canonical), og_image=e(og_image), og_locale=OG_LOCALE.get(lang.code, lang.code.replace("-", "_")), app_id=APP_ID,
           css=asset_url("assets/site.css"), jsonld="".join(jsonld_script(b) for b in jsonld),
           header=header(lang, path), body=body, footer=footer(lang))


# ---------------------------------------------------------------- structured data

APP_ENTITY_ID = BASE_URL + "/#app"
ORG = {"@type": "Organization", "@id": STUDIO_URL + "#org", "name": "nakolini", "url": STUDIO_URL, "logo": STUDIO_LOGO,
       "founder": [{"@type": "Person", "name": "Dmytro Hryb"}, {"@type": "Person", "name": "Vitalii Kikot"}]}


def app_jsonld(lang):
    names = sorted({s["name"] for s in STORE.values()} - {STORE["en"]["name"]})
    return {
        "@context": "https://schema.org",
        "@type": "MobileApplication",
        "@id": APP_ENTITY_ID,
        "name": "Kroky: Walk Breaks",
        "alternateName": ["Kroky"] + names,
        "description": plain(lang.t("home.description")),
        "inLanguage": lang.code,
        "operatingSystem": "iOS 17.0 or later",
        "applicationCategory": "HealthApplication",
        "applicationSubCategory": "Walking, step goal and sitting reminder",
        "url": url_for(lang, ""),
        "image": BASE_URL + "/assets/icon-512.png",
        "screenshot": ["%s/assets/shots/%s/%s.webp" % (BASE_URL, lang.code, s) for s in SHOTS],
        "downloadUrl": "https://apps.apple.com/app/id%s" % APP_ID,
        "installUrl": "https://apps.apple.com/app/id%s" % APP_ID,
        "availableLanguage": [l.code for l in ALL_LANGS],
        "offers": [
            {"@type": "Offer", "name": "Kroky", "price": "0", "priceCurrency": "USD"},
            {"@type": "Offer", "name": "Kroky Pro Yearly", "price": "19.99", "priceCurrency": "USD",
             "eligibleRegion": {"@type": "Country", "name": "US"}},
            {"@type": "Offer", "name": "Kroky Pro Lifetime", "price": "49.99", "priceCurrency": "USD",
             "eligibleRegion": {"@type": "Country", "name": "US"}},
        ],
        "featureList": [plain(lang.t("features.%d_t" % i)) for i in range(1, 9)],
        "dateModified": SITE_UPDATED,
        "author": ORG,
        "publisher": ORG,
    }


def faq_jsonld(items):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": plain(q),
                            "acceptedAnswer": {"@type": "Answer", "text": plain(a)}} for q, a in items]}


def breadcrumbs(lang, crumbs):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": plain(name),
                                 "item": url_for(lang, path)} for i, (name, path) in enumerate(crumbs)]}


def website_jsonld(lang):
    return {"@context": "https://schema.org", "@type": "WebSite", "@id": BASE_URL + "/#site", "name": "Kroky",
            "url": url_for(lang, ""), "inLanguage": lang.code, "publisher": ORG, "about": {"@id": APP_ENTITY_ID}}


# ---------------------------------------------------------------- pages

def caption_title(lang, shot):
    # The captions' line breaks are for the screenshots; Chinese and Japanese don't put a space where they were.
    return lang.captions[shot]["title"].replace("\n", "" if lang.code in CJK_STOP else " ").rstrip()


def phone(lang, shot, cls="phone", eager=False):
    cap = lang.captions[shot]
    title = caption_title(lang, shot)
    if title[-1] in ".!?。！？…؟।":
        alt = ("%s%s" if lang.code in CJK_STOP else "%s %s") % (title, cap["subtitle"])
    else:
        alt = ("%s。%s" if lang.code in CJK_STOP else "%s। %s" if lang.code in DANDA else "%s۔ %s" if lang.code == "ur" else "%s %s" if lang.code == "th" else "%s. %s") % (
            title, cap["subtitle"])
    return ('<div class="%s"><img src="/assets/shots/%s/%s.webp" width="600" height="1304" alt="%s"%s></div>'
            % (cls, lang.code, shot, e(alt), "" if eager else ' loading="lazy" decoding="async"'))


def faq_items(lang):
    return [(lang.t("faq.%d_q" % i), lang.t("faq.%d_a" % i)) for i in range(1, 16)]


def home_page(lang):
    shots = "".join(
        '<li><figure>%s<figcaption><strong>%s</strong><span>%s</span></figcaption></figure></li>' % (
            phone(lang, s), e(caption_title(lang, s)), e(lang.captions[s]["subtitle"]))
        for s in SHOTS)
    how = "".join('<li><span class="num">%s</span><div><h3>%s</h3><p>%s</p></div></li>' % (
        lang.num(i), lang.t("how.%d_t" % i), lang.t("how.%d" % i)) for i in range(1, 5))
    feature_icons = ["sit", "sun", "loop", "map", "star", "chart", "calendar", "globe"]
    features = "".join('<li class="card">%s<h3>%s</h3><p>%s</p></li>' % (
        icon(feature_icons[i - 1]), lang.t("features.%d_t" % i), lang.t("features.%d" % i)) for i in range(1, 9))
    privacy = "".join('<li class="card">%s<h3>%s</h3><p>%s</p></li>' % (
        icon(name), lang.t("privacy.%d_t" % i), lang.t("privacy.%d" % i))
        for i, name in ((1, "phone"), (2, "person"), (3, "shield")))
    y, n, one, unl = (lang.t("plans.yes"), lang.t("plans.no"), lang.t("plans.one_a_day"), lang.t("plans.unlimited"))
    rows = [("row_loops", one, unl), ("row_shuffle", one, unl), ("row_weather", y, y), ("row_steps", y, y),
            ("row_guide", y, y), ("row_maps", y, y), ("row_edit", y, y), ("row_week", y, y),
            ("row_nudges", n, y), ("row_reminders", n, y), ("row_meetings", n, y), ("row_favorites", n, y)]
    plans = "".join('<tr><th scope="row">%s</th><td>%s</td><td>%s</td></tr>' % (lang.t("plans." + k), a, b)
                    for k, a, b in rows)
    price_note = lang.t("plans.note") + (" " + lang.t("plans.price_us") if lang.english else "")
    faq = "".join('<details class="row"><summary><h3>%s</h3></summary><p>%s</p></details>' % (q, a)
                  for q, a in faq_items(lang))
    guides = guide_cards(lang)
    chips = "".join("<li>%s</li>" % lang.t("home.chip_%d" % i) for i in range(1, 4))
    body = """<section class="hero"><div class="wrap hero-grid">
<div class="hero-text">
<p class="eyebrow">{eyebrow}</p>
<h1>{h1}</h1>
<p class="lead">{lead}</p>
<p class="actions">{badge}</p>
<p class="facts">{facts}</p>
<ul class="chips">{chips}</ul>
</div>
<div class="hero-phone">{hero_phone}</div>
</div></section>

<section class="shots" aria-labelledby="shots-h"><div class="wrap">
<h2 id="shots-h">{shots_h2}</h2>
<ul class="strip">{shots}</ul>
</div></section>

<section id="how" class="wrap section"><h2>{how_h2}</h2><ol class="list how">{how}</ol></section>

<section class="wrap section"><h2>{features_h2}</h2><ul class="cards">{features}</ul></section>

<section class="wrap section"><h2>{privacy_h2}</h2><ul class="cards three">{privacy}</ul><p class="more">{privacy_more}</p></section>

<section class="wrap section"><h2>{plans_h2}</h2>
<div class="group table-wrap"><table class="plans"><thead><tr><td></td><th scope="col">{free}</th><th scope="col">{pro}</th></tr></thead><tbody>{plans}</tbody></table></div>
<p class="note">{price_note}</p></section>

<section id="faq" class="wrap section"><h2>{faq_h2}</h2><div class="group faq">{faq}</div></section>

<section class="wrap section"><h2>{guides_h2}</h2>{guides}</section>

<section class="wrap section"><div class="group maker-card">
<img src="/assets/nakolini-mark.png" width="48" height="48" alt="nakolini">
<div><h2>{maker_h2}</h2><p>{maker_text}</p><p><a class="button secondary" href="{studio}">{maker_link}</a></p></div>
</div></section>

<section class="cta"><div class="wrap">
<img src="/assets/icon-192.png" width="96" height="96" alt="">
<h2>{cta_h2}</h2>
<p>{cta_text}</p>
<p class="actions">{badge_end}</p>
</div></section>""".format(
        eyebrow=lang.t("home.eyebrow"), h1=lang.t("home.h1"), lead=lang.t("home.lead"),
        badge=store_badge(lang, "web_home_hero"), facts=lang.t("home.facts"), chips=chips,
        hero_phone=phone(lang, "home", eager=True), shots_h2=lang.t("home.shots_h2"), shots=shots,
        how_h2=lang.t("how.h2"), how=how, features_h2=lang.t("features.h2"), features=features,
        privacy_h2=lang.t("privacy.h2"), privacy=privacy, privacy_more=lang.t("privacy.more"),
        plans_h2=lang.t("plans.h2"), free=lang.t("plans.free"), pro=lang.t("plans.pro"), plans=plans,
        price_note=price_note, faq_h2=lang.t("faq.h2"), faq=faq, guides_h2=lang.t("guides.h2"), guides=guides,
        maker_h2=lang.t("maker.h2"), maker_text=lang.t("maker.text"), studio=STUDIO_URL,
        maker_link=lang.t("maker.link"), cta_h2=lang.t("cta.h2"), cta_text=lang.t("cta.text"),
        badge_end=store_badge(lang, "web_home_end"))
    title = "%s · %s" % (lang.store["name"], lang.store["subtitle"])
    return render(lang, "", title, lang.t("home.description"), body,
                  jsonld=[app_jsonld(lang), website_jsonld(lang), faq_jsonld(faq_items(lang))])


def guide_cards(lang):
    return '<ul class="cards three guides">%s</ul>' % "".join(
        '<li class="card"><a href="%sguides/%s/"><h3>%s</h3><p>%s</p><span class="go">%s</span></a></li>' % (
            lang.prefix, EN[g + ".slug"], lang.t(g + ".h1"), lang.t(g + ".answer"), lang.t("guides.read"))
        for g in GUIDES)


def app_box(lang, campaign):
    return """<aside class="group app-box"><img src="/assets/icon-192.png" width="64" height="64" alt="">
<div><h2>{name}</h2><p>{sub}</p></div>{badge}</aside>""".format(
        name=e(lang.store["name"]), sub=e(lang.store["subtitle"]), badge=store_badge(lang, campaign, height=48))


def step_table(lang):
    rows = []
    for steps in TABLE_STEPS:
        meters = steps * STRIDE_M
        minutes = round(meters / PACE_M_PER_MIN)
        m_unit, km_unit = UNITS.get(lang.code, ("\u00a0m", "\u00a0km"))
        dist = lang.num(round(meters)) + m_unit if meters < 1000 else lang.num(meters / 1000, 1) + km_unit
        if lang.code in ("en", "en-GB"):
            dist += " · %s mi" % lang.num(meters / 1609.344, 1)
        rows.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            lang.num(steps), lang.t("g2.minutes", n=lang.num(minutes)), dist))
    return """<div class="group table-wrap"><table class="plans steps"><thead><tr><th scope="col">{s}</th><th scope="col">{m}</th><th scope="col">{d}</th></tr></thead>
<tbody>{rows}</tbody></table></div><p class="note">{note}</p>""".format(
        s=lang.t("g2.table_steps"), m=lang.t("g2.table_minutes"), d=lang.t("g2.table_distance"), rows="".join(rows),
        note=lang.t("g2.table_note"))


def guide_page(lang, g):
    slug = EN[g + ".slug"]
    sections = {
        "g1": [("why_h2", "<p>%s</p>" % lang.t("g1.why")),
               ("setup_h2", '<ol class="plain">%s</ol>' % "".join("<li>%s</li>" % lang.t("g1.setup_%d" % i) for i in range(1, 5))),
               ("limits_h2", "<p>%s</p>" % lang.t("g1.limits"))],
        "g2": [("table_h2", step_table(lang)), ("own_h2", "<p>%s</p>" % lang.t("g2.own")),
               ("kroky_h2", "<p>%s</p>" % lang.t("g2.kroky"))],
        "g3": [("how_h2", "<p>%s</p>" % lang.t("g3.how")),
               ("change_h2", '<ul class="plain">%s</ul>' % "".join("<li>%s</li>" % lang.t("g3.change_%d" % i) for i in range(1, 5))),
               ("limits_h2", "<p>%s</p>" % lang.t("g3.limits"))],
    }[g]
    shot = {"g1": "nudge", "g2": "home", "g3": "route"}[g]
    body = """<article class="wrap prose guide">
<nav class="crumbs"><a href="{home}">Kroky</a> › <a href="{home}guides/">{guides}</a></nav>
<h1>{h1}</h1>
<div class="answer-grid"><p class="answer">{answer}</p>{phone}</div>
{sections}
{box}
<h2>{more}</h2>{others}
</article>""".format(
        home=lang.prefix, guides=lang.t("nav.guides"), h1=lang.t(g + ".h1"), answer=lang.t(g + ".answer"),
        phone=phone(lang, shot, cls="phone small", eager=True),
        sections="".join("<h2>%s</h2>%s" % (lang.t("%s.%s" % (g, k)), v) for k, v in sections),
        box=app_box(lang, "web_guide_" + g), more=lang.t("guides.h2"),
        others='<ul class="plain links">%s</ul>' % "".join(
            '<li><a href="%sguides/%s/">%s</a></li>' % (lang.prefix, EN[o + ".slug"], lang.t(o + ".h1"))
            for o in GUIDES if o != g))
    path = "guides/%s/" % slug
    article = {"@context": "https://schema.org", "@type": "Article", "headline": plain(lang.t(g + ".h1")),
               "description": plain(lang.t(g + ".description")), "inLanguage": lang.code,
               "url": url_for(lang, path), "dateModified": SITE_UPDATED, "author": ORG, "publisher": ORG,
               "about": {"@id": APP_ENTITY_ID}, "image": "%s/assets/shots/%s/%s.webp" % (BASE_URL, lang.code, shot)}
    crumbs = breadcrumbs(lang, [("Kroky", ""), (lang.t("nav.guides"), "guides/"), (lang.t(g + ".h1"), path)])
    return path, render(lang, path, lang.t(g + ".title"), lang.t(g + ".description"), body, jsonld=[article, crumbs])


def guides_index(lang):
    body = """<div class="wrap prose">
<nav class="crumbs"><a href="{home}">Kroky</a></nav>
<h1>{h1}</h1><p class="lead-dark">{intro}</p>
{cards}
{box}
</div>""".format(home=lang.prefix, h1=lang.t("nav.guides"), intro=lang.t("guides.intro"), cards=guide_cards(lang),
                 box=app_box(lang, "web_guides"))
    return render(lang, "guides/", lang.t("guides.title"), lang.t("guides.description"), body,
                  jsonld=[breadcrumbs(lang, [("Kroky", ""), (lang.t("nav.guides"), "guides/")])])


def legal_page(lang, path, prefix, sections, extra_top=""):
    note = ""
    if not lang.english:
        note = '<p class="note translation">%s</p>' % lang.t("legal.translation_note", english="/" + path)
    parts = []
    for heading, paras in sections:
        if heading:
            parts.append("<h2>%s</h2>" % lang.t(heading))
        parts.extend("<p>%s</p>" % lang.t(p) for p in paras)
    body = """<article class="wrap prose legal">
<nav class="crumbs"><a href="{home}">Kroky</a></nav>
<h1>{h1}</h1>
<p class="meta">{effective}</p>
{note}{top}{parts}
</article>""".format(home=lang.prefix, h1=lang.t(prefix + ".h1"),
                     effective=lang.t("legal.effective", date=lang.t("date.effective")), note=note, top=extra_top,
                     parts="".join(parts))
    return render(lang, path, lang.t(prefix + ".title"), lang.t(prefix + ".description"), body,
                  jsonld=[breadcrumbs(lang, [("Kroky", ""), (lang.t(prefix + ".h1"), path)])])


def privacy_page(lang):
    p = "privacy_page."
    leaves = '<ul class="plain">%s</ul>' % "".join(
        "<li>%s</li>" % lang.t(p + k) for k in ("leaves_weather", "leaves_maps", "leaves_osm", "leaves_handoff"))
    sections = [(None, [p + "intro"]), (p + "who_h2", [p + "who"]), (p + "collect_h2", [p + "collect"]),
                (p + "health_h2", [p + "health"]),
                (p + "location_h2", [p + "location_1", p + "location_2", p + "location_3", p + "location_4"])]
    rest = [(p + "calendar_h2", [p + "calendar"]), (p + "notifications_h2", [p + "notifications"]),
            (p + "purchases_h2", [p + "purchases"]), (p + "stays_h2", [p + "stays"]),
            (p + "choices_h2", [p + "choices"]), (p + "tracking_h2", [p + "tracking"]),
            (p + "website_h2", [p + "website"]), (p + "children_h2", [p + "children"]),
            (p + "changes_h2", [p + "changes"]), (p + "contact_h2", [p + "contact"])]
    # The list of recipients sits between the location and calendar sections.
    page = legal_page(lang, "privacy-policy.html", "privacy_page", sections + [(p + "leaves_h2", [])] + rest)
    marker = "<h2>%s</h2>" % lang.t(p + "leaves_h2")
    return page.replace(marker, marker + leaves, 1)


def terms_page(lang):
    p = "terms_page."
    sections = [(None, [p + "intro"]), (p + "license_h2", [p + "license"]),
                (p + "safety_h2", [p + "safety_1", p + "safety_2"]), (p + "health_h2", [p + "health"]),
                (p + "pro_h2", [p + "pro_1", p + "pro_2", p + "pro_3"]), (p + "data_h2", [p + "data"]),
                (p + "use_h2", [p + "use"]), (p + "ip_h2", [p + "ip"]), (p + "warranty_h2", [p + "warranty"]),
                (p + "liability_h2", [p + "liability"]), (p + "changes_h2", [p + "changes"]),
                (p + "contact_h2", [p + "contact"])]
    return legal_page(lang, "terms.html", "terms_page", sections)


def support_page(lang):
    s = "support."
    qs = ["steps", "nudges", "loop", "restore", "cancel", "avoid", "data"]
    faq = "".join('<details class="row" open><summary><h3>%s</h3></summary><p>%s</p></details>' % (
        lang.t(s + q + "_q"), lang.t(s + q + "_a")) for q in qs)
    body = """<article class="wrap prose">
<nav class="crumbs"><a href="{home}">Kroky</a></nav>
<h1>{h1}</h1>
<p class="meta">{meta}</p>
<h2>{faq_h2}</h2>
<div class="group faq">{faq}</div>
<h2>{contact_h2}</h2>
<p>{contact}</p>
<p>{tip}</p>
</article>""".format(home=lang.prefix, h1=lang.t(s + "h1"), meta=lang.t(s + "meta"), faq_h2=lang.t(s + "faq_h2"),
                     faq=faq, contact_h2=lang.t(s + "contact_h2"), contact=lang.t(s + "contact"),
                     tip=lang.t(s + "contact_tip"))
    items = [(lang.t(s + q + "_q"), lang.t(s + q + "_a")) for q in qs]
    return render(lang, "support.html", lang.t(s + "title"), lang.t(s + "description"), body,
                  jsonld=[faq_jsonld(items), breadcrumbs(lang, [("Kroky", ""), (lang.t(s + "h1"), "support.html")])])


def not_found_page():
    lang = EN_LANG
    body = """<div class="wrap prose"><h1>Page not found</h1>
<p>That page doesn't exist. Try <a href="/">Kroky's home page</a>, the <a href="/guides/">guides</a> or <a href="/support.html">support</a>.</p></div>"""
    return render(lang, "404.html", "Page not found · Kroky", "Page not found.", body, noindex=True)


# ---------------------------------------------------------------- site files

def page_paths():
    return ["", "guides/"] + ["guides/%s/" % EN[g + ".slug"] for g in GUIDES] + [
        "support.html", "privacy-policy.html", "terms.html"]


def sitemap():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for path in page_paths():
        for lang in ALL_LANGS:
            out.append("<url><loc>%s</loc><lastmod>%s</lastmod>" % (e(url_for(lang, path)), SITE_UPDATED))
            out.extend('<xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (o.code, e(url_for(o, path)))
                       for o in ALL_LANGS)
            out.append('<xhtml:link rel="alternate" hreflang="x-default" href="%s"/></url>' % e(url_for(EN_LANG, path)))
    out.append("</urlset>")
    return "\n".join(out) + "\n"


ROBOTS = """# Search engines and AI assistants are welcome to read and cite every page.
User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: Claude-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: Bingbot
Allow: /

Sitemap: %s/sitemap.xml
""" % BASE_URL


def llms_txt():
    en = EN_LANG
    lines = [
        "# Kroky: Walk Breaks",
        "",
        "> %s Free to start; Kroky Pro is a yearly subscription with a 7-day free trial ($19.99 a year in the US) or a "
        "one-time lifetime purchase ($49.99 in the US). iPhone only, iOS 17 or later. No account, no server, no "
        "analytics, no tracking. In 49 languages. Made by nakolini (%s), a two-person studio of Dmytro Hryb and "
        "Vitalii Kikot." % (plain(en.t("home.description")), STUDIO_URL),
        "",
        "## Pages",
        "",
        "- [Kroky for iPhone](%s/): what it does, how it works, free vs Kroky Pro, privacy, FAQ" % BASE_URL,
    ]
    for g in GUIDES:
        lines.append("- [%s](%s): %s" % (plain(en.t(g + ".h1")), url_for(en, "guides/%s/" % EN[g + ".slug"]),
                                         plain(en.t(g + ".answer"))))
    lines += [
        "- [Support](%s/support.html): Apple Health access, nudges, restoring and cancelling Kroky Pro, contact" % BASE_URL,
        "- [Privacy Policy](%s/privacy-policy.html): collects nothing; what goes to Apple and OpenStreetMap" % BASE_URL,
        "- [Terms of Use](%s/terms.html): Apple's standard EULA plus walking safety, Kroky Pro billing, map data" % BASE_URL,
        "- [App Store](https://apps.apple.com/app/id%s)" % APP_ID,
        "- [nakolini, the studio behind Kroky](%s)" % STUDIO_URL,
        "",
        "## Facts",
        "",
        "- App Store name: Kroky: Walk Breaks. Localized names: %s" % "; ".join(
            sorted({s["name"] for k, s in STORE.items() if s["name"] != STORE["en"]["name"]})),
        "- What it does: reads steps from Apple Health, notices a long sit (90 minutes by default), finds today's dry "
        "window in Apple Weather's hourly forecast, and plans a walking loop from where you are through parks and quiet "
        "streets, sized to close the gap to today's step goal (6,000, 8,000 or 10,000 steps) or 15, 30, 45 or 60 "
        "minutes. Guides the walk on a live map with optional spoken directions, also with the screen locked. Apple Maps "
        "or Google Maps hand-off is optional",
        "- Free: one new loop and one shuffle a day, today's dry window, steps and gap, live guidance, reverse, rate and "
        "avoid a street, weekly view, streak, walk results and history",
        "- Kroky Pro: sitting nudges (at most 2 a day, in your hours and days, with snooze and your own threshold), "
        "reminders when a dry window opens, Skip my meetings (calendar busy times), unlimited loops and shuffles, "
        "favorite loops mixed back in",
        "- Not: no Apple Watch app (watch steps count through Apple Health), no Android or iPad version, no workouts, "
        "no running or cycling routes, no social features",
        "- Privacy: location only while using the app, and continuously only during a walk the user starts; never "
        "\"Always\". Health data is read only, never written or sent. Weather and routing through Apple; parks and "
        "paths from OpenStreetMap Overpass with a location rounded to about 100 m",
        "- The name: \"kroky\" means \"steps\" (Ukrainian кроки in Latin letters; Czech and Slovak as is)",
        "- Support: %s" % EMAIL,
        "",
        "## Questions and answers",
        "",
    ]
    for q, a in faq_items(en):
        lines += ["### %s" % plain(q), "", plain(a), ""]
    lines += ["## Languages", "", "Every page is available in: %s." % ", ".join(
        "%s (%s)" % (l.name, url_for(l, "")) for l in ALL_LANGS), ""]
    return "\n".join(lines)


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def clean():
    for d in GENERATED_DIRS:
        p = os.path.join(ROOT, d)
        if os.path.isdir(p):
            shutil.rmtree(p)
    for f in GENERATED_FILES:
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            os.remove(p)


def main():
    clean()
    for lang in ALL_LANGS:
        base = lang.segment + "/" if lang.segment else ""
        write(base + "index.html", home_page(lang))
        write(base + "guides/index.html", guides_index(lang))
        for g in GUIDES:
            path, page = guide_page(lang, g)
            write(base + path + "index.html", page)
        write(base + "support.html", support_page(lang))
        write(base + "privacy-policy.html", privacy_page(lang))
        write(base + "terms.html", terms_page(lang))
    write("404.html", not_found_page())
    write("sitemap.xml", sitemap())
    write("robots.txt", ROBOTS)
    write("llms.txt", llms_txt())
    write(".nojekyll", "")
    write("CNAME", BASE_URL.split("//")[1] + "\n")
    print("built %d languages" % len(ALL_LANGS))


if __name__ == "__main__":
    main()
