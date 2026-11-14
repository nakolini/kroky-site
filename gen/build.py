#!/usr/bin/env python3
"""Builds kroky.nakolini.com: every page in all 49 of the app's languages, plus sitemap, robots.txt and llms.txt.

Python 3.9+ standard library only. Run from anywhere: python3 gen/build.py
Copy is in i18n/<lang>.json (en.json is the source), the App Store names and the screenshot captions are in data/,
and the output is written to the repo root, which GitHub Pages serves as is.
"""
import datetime, decimal, hashlib, html, json, os, re, shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASE_URL = "https://kroky.nakolini.com"
APP_ID = "6824215298"
# App Store Connect provider token (the pt= of a campaign link). Without it the App Store ignores ct= in Analytics.
PROVIDER_TOKEN = "128480147"
STUDIO_URL = "https://nakolini.com/"
STUDIO_LOGO = "https://nakolini.com/assets/logo/nakolini-mark-tile.png"
EMAIL = "support@kroky.nakolini.com"
EULA_URL = "https://www.apple.com/legal/internet-services/itunes/dev/stdeula/"
OTHER_APPS = [("footer.anonimo", "https://anonimo.nakolini.com/"),
              ("footer.expenny", "https://expenny.nakolini.com/"),
              ("footer.prospekt", "https://prospekt.nakolini.com/")]
# Bump when the pages change meaningfully: sitemap lastmod and JSON-LD dateModified.
SITE_UPDATED = "2026-11-09"
# Pages carry this token where their own last-modified date goes; write() swaps in the date from data/lastmod.json,
# which only moves when the page's content changes, so sitemap lastmod and dateModified stay honest.
MODIFIED = "@@MODIFIED@@"
LASTMOD_FILE = "data/lastmod.json"
# IndexNow (Bing, Yandex, Seznam, Naver; Bing feeds Copilot and ChatGPT search): the key file at the site root
# proves we own the host. scripts/indexnow.py submits the pages whose lastmod is today.
INDEXNOW_KEY = "6b0f3c1e9a8d4f27b5c2e1d0a9f8c7b6"
# The App Store release of version 1.0.
RELEASED = "2026-11-03"
STORE_URL = "https://apps.apple.com/us/app/kroky-walk-breaks/id%s" % APP_ID
# The App Store lists the app under its co-founder's developer account.
DEVELOPER = {"@type": "Person", "name": "Vitalii Kikot", "url": "https://apps.apple.com/us/developer/vitalii-kikot/id1871566359"}

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
GUIDES = ["g1", "g2", "g3", "g4", "g5"]
# Stride and pace the step table assumes: the app's defaults before it learns the walker's own (StrideCalibration).
STRIDE_M, PACE_M_PER_MIN = 0.75, 75  # 100 steps a minute
TABLE_STEPS = [1000, 2000, 3000, 4000, 5000, 8000, 10000]

# Generated paths, removed before each build so stale pages never linger.
GENERATED_DIRS = ["guides", "get", "press"] + [s for _, s, _ in LANGUAGES if s]
GENERATED_FILES = ["llms-full.txt", "index.html", "support.html", "privacy-policy.html", "terms.html", "404.html", "sitemap.xml",
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
    "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
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
<nav class="nav" aria-label="Kroky"><a href="{home}#how">{how}</a><a href="{home}#plans">{plans}</a><a href="{home}#faq">{faq}</a><a href="{home}guides/">{guides}</a></nav>
<a class="get" href="{get_url}" aria-label="{get_label}">{get}</a>
{switch}
</div></header>""".format(skip=lang.t("nav.skip"), home=home, how=lang.t("nav.how"), plans=lang.t("nav.plans"),
                          faq=lang.t("nav.faq"), guides=lang.t("nav.guides"), get_url=e(app_store_url("web_header")),
                          get_label=e(plain(lang.t("nav.get_app"))), get=lang.t("nav.get"),
                          switch=lang_switch(lang, path))


def footer(lang):
    home = lang.prefix
    studio = '<a href="%s">%s</a>' % (STUDIO_URL, lang.t("footer.studio"))
    apps = " · ".join('<a href="%s">%s</a>' % (url, lang.t(key)) for key, url in OTHER_APPS)
    return """<footer class="site-footer"><div class="wrap">
<p class="maker"><a class="maker-logo" href="{studio_url}" aria-hidden="true" tabindex="-1"><picture><source srcset="/assets/nakolini-mark-white.png" media="(prefers-color-scheme: dark)"><img src="/assets/nakolini-mark.png" alt="" width="20" height="20"></picture></a><span>{made}</span></p>
<p>{also} {apps}</p>
<p><a href="{home}support.html">{support}</a> · <a href="{home}privacy-policy.html">{privacy}</a> · <a href="{home}terms.html">{terms}</a> · <a href="{home}guides/">{guides}</a> · <a href="/press/">{press}</a></p>
<p class="fine">{copyright}</p>
</div></footer>""".format(
        studio_url=STUDIO_URL, made=lang.t("footer.made_by", studio=studio), also=lang.t("footer.also"), apps=apps,
        home=home, support=lang.t("footer.support"), privacy=lang.t("footer.privacy"), terms=lang.t("footer.terms"),
        guides=lang.t("nav.guides"), press=lang.t("footer.press"), copyright=lang.t("footer.copyright"))


def jsonld_script(block):
    return '<script type="application/ld+json">%s</script>\n' % json.dumps(block, ensure_ascii=False).replace("</", "<\\/")


def render(lang, path, title, description, body, jsonld=(), og_image=None, noindex=False, og_type="website",
           modified=None, alternates=True):
    canonical = url_for(lang, path)
    if noindex:
        links = '<meta name="robots" content="noindex">\n'
    else:
        links = '<link rel="canonical" href="%s">\n' % e(canonical)
    if not noindex and alternates:
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
{links}<meta property="og:type" content="{og_type}">{article_time}
<meta property="og:site_name" content="Kroky">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{title}">
<meta property="og:locale" content="{og_locale}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image:alt" content="{title}">
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
           header=header(lang, "" if noindex else path), body=body, footer=footer(lang), og_type=og_type,
           article_time='\n<meta property="article:modified_time" content="%s">' % modified if modified else "")


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
        "genre": "Health & Fitness",
        "sameAs": [STORE_URL],
        "datePublished": RELEASED,
        "softwareVersion": "1.0",
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
        "dateModified": MODIFIED,
        "author": [ORG, DEVELOPER],
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
            "url": BASE_URL + "/", "inLanguage": [l.code for l in ALL_LANGS], "publisher": ORG, "about": {"@id": APP_ENTITY_ID}}


# ---------------------------------------------------------------- pages

def caption_title(lang, shot):
    # The captions' line breaks are for the screenshots; Chinese and Japanese don't put a space where they were.
    return lang.captions[shot]["title"].replace("\n", "" if lang.code in CJK_STOP else " ").rstrip()


def phone(lang, shot, cls="phone", eager=False, decorative=False):
    cap = lang.captions[shot]
    title = caption_title(lang, shot)
    if title[-1] in ".!?。！？…؟।":
        alt = ("%s%s" if lang.code in CJK_STOP else "%s %s") % (title, cap["subtitle"])
    else:
        alt = ("%s。%s" if lang.code in CJK_STOP else "%s। %s" if lang.code in DANDA else "%s۔ %s" if lang.code == "ur" else "%s %s" if lang.code == "th" else "%s. %s") % (
            title, cap["subtitle"])
    # In the strip the figcaption already says it, so screen readers shouldn't hear it twice.
    return ('<div class="%s"><img src="/assets/shots/%s/%s.webp" width="600" height="1304" alt="%s"%s></div>'
            % (cls, lang.code, shot, "" if decorative else e(alt),
               ' fetchpriority="high"' if eager else ' loading="lazy" decoding="async"'))


# "Is Kroky free?" and the Apple Watch question are what people ask first.
FAQ_ORDER = [1, 6, 16, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15]


def faq_items(lang):
    return [(lang.t("faq.%d_q" % i), lang.t("faq.%d_a" % i)) for i in FAQ_ORDER]


# Feature cards that are Kroky Pro only: sitting nudges and Skip my meetings.
PRO_FEATURES = {1, 7}


def check_cell(lang, value):
    if value == lang.t("plans.yes"):
        return '%s<span class="skip">%s</span>' % (icon("check"), value)
    return value


def home_page(lang):
    shots = "".join(
        '<li><figure>%s<figcaption><strong>%s</strong><span>%s</span></figcaption></figure></li>' % (
            phone(lang, s, decorative=True), e(caption_title(lang, s)), e(lang.captions[s]["subtitle"]))
        for s in SHOTS if s != "home")  # Home is the hero
    how = "".join('<li><span class="num">%s</span><div><h3>%s</h3><p>%s</p></div></li>' % (
        lang.num(i), lang.t("how.%d_t" % i), lang.t("how.%d" % i)) for i in range(1, 5))
    feature_icons = ["sit", "sun", "loop", "map", "star", "chart", "calendar", "globe"]
    pro_tag = '<span class="pro-tag">%s</span>' % lang.t("plans.pro")
    features = "".join('<li class="card">%s<h3>%s%s</h3><p>%s</p></li>' % (
        icon(feature_icons[i - 1]), lang.t("features.%d_t" % i), pro_tag if i in PRO_FEATURES else "",
        lang.t("features.%d" % i)) for i in range(1, 9))
    privacy = "".join('<li class="card">%s<h3>%s</h3><p>%s</p></li>' % (
        icon(name), lang.t("privacy.%d_t" % i), lang.t("privacy.%d" % i))
        for i, name in ((1, "phone"), (2, "person"), (3, "shield")))
    y, n, one, unl = (lang.t("plans.yes"), lang.t("plans.no"), lang.t("plans.one_a_day"), lang.t("plans.unlimited"))
    rows = [("row_loops", one, unl), ("row_shuffle", one, unl), ("row_weather", y, y), ("row_steps", y, y),
            ("row_guide", y, y), ("row_maps", y, y), ("row_edit", y, y), ("row_week", y, y),
            ("row_nudges", n, y), ("row_reminders", n, y), ("row_meetings", n, y), ("row_favorites", n, y)]
    plans = "".join('<tr><th scope="row">%s</th><td>%s</td><td>%s</td></tr>' % (
        lang.t("plans." + k), check_cell(lang, a), check_cell(lang, b)) for k, a, b in rows)
    price_note = lang.t("plans.note") + (" " + lang.t("plans.price_us") if lang.english else "")
    faq = "".join('<details class="row"><summary><span class="q">%s</span></summary><p>%s</p></details>' % (q, a)
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
<p class="qr"><img src="/assets/qr-app-store.svg" width="96" height="96" alt=""><span>{qr}</span></p>
</div>
<div class="hero-phone">{hero_phone}</div>
</div></section>

<section class="shots" aria-labelledby="shots-h"><div class="wrap">
<h2 id="shots-h">{shots_h2}</h2>
<ul class="strip" tabindex="0" role="region" aria-label="{shots_label}">{shots}</ul>
</div></section>

<section id="how" class="wrap section"><h2>{how_h2}</h2><ol class="list how">{how}</ol></section>

<section class="wrap section"><h2>{features_h2}</h2><ul class="cards">{features}</ul></section>

<section class="wrap section"><h2>{privacy_h2}</h2><ul class="cards three">{privacy}</ul><p class="more">{privacy_more}</p></section>

<section id="plans" class="wrap section"><h2>{plans_h2}</h2>
<p class="promise">{promise}</p>
<div class="group table-wrap"><table class="plans"><thead><tr><td></td><th scope="col">{free}</th><th scope="col">{pro}</th></tr></thead><tbody>{plans}</tbody></table></div>
<p class="note">{price_note}</p>
<p class="actions">{badge_plans}</p></section>

<section id="faq" class="wrap section"><h2>{faq_h2}</h2><div class="group faq">{faq}</div></section>

<section class="wrap section"><h2>{guides_h2}</h2>{guides}</section>

<section class="cta"><div class="wrap">
<img src="/assets/icon-192.png" width="96" height="96" alt="">
<h2>{cta_h2}</h2>
<p>{cta_text}</p>
<p class="actions">{badge_end}</p>
</div></section>""".format(
        eyebrow=lang.t("home.eyebrow"), h1=lang.t("home.h1"), lead=lang.t("home.lead"),
        badge=store_badge(lang, "web_home_hero"), facts=lang.t("home.facts"), chips=chips, qr=lang.t("home.qr"),
        shots_label=e(plain(lang.t("home.shots_h2"))), promise=lang.t("plans.promise"),
        badge_plans=store_badge(lang, "web_home_plans", height=48),
        hero_phone=phone(lang, "home", eager=True), shots_h2=lang.t("home.shots_h2"), shots=shots,
        how_h2=lang.t("how.h2"), how=how, features_h2=lang.t("features.h2"), features=features,
        privacy_h2=lang.t("privacy.h2"), privacy=privacy, privacy_more=lang.t("privacy.more"),
        plans_h2=lang.t("plans.h2"), free=lang.t("plans.free"), pro=lang.t("plans.pro"), plans=plans,
        price_note=price_note, faq_h2=lang.t("faq.h2"), faq=faq, guides_h2=lang.t("guides.h2"), guides=guides,
        cta_h2=lang.t("cta.h2"), cta_text=lang.t("cta.text"),
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
<div><p class="app-name">{name}</p><p>{sub}</p></div>{badge}</aside>""".format(
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


# A second real screen beside the guide section it illustrates.
SECTION_SHOTS = {("g1", "setup_h2"): "settings", ("g2", "kroky_h2"): "walk", ("g3", "how_h2"): "guide",
                 ("g4", "compare_h2"): "nudge", ("g5", "kroky_h2"): "route"}


def section_html(lang, g, key, content):
    heading = "<h2>%s</h2>" % lang.t("%s.%s" % (g, key))
    shot = SECTION_SHOTS.get((g, key))
    if not shot:
        return heading + content
    return '%s<div class="answer-grid shot-grid"><div>%s</div>%s</div>' % (
        heading, content, phone(lang, shot, cls="phone small"))


GUIDE_PUBLISHED = {"g1": "2026-10-25", "g2": "2026-10-25", "g3": "2026-10-25", "g4": SITE_UPDATED, "g5": SITE_UPDATED}


def guide_page(lang, g):
    slug = EN[g + ".slug"]
    sections = {
        "g1": [("why_h2", "<p>%s</p>" % lang.t("g1.why")),
               ("setup_h2", '<ol class="plain">%s</ol>' % "".join("<li>%s</li>" % lang.t("g1.setup_%d" % i) for i in range(1, 5))),
               ("limits_h2", "<p>%s</p>" % lang.t("g1.limits"))],
        "g2": [("table_h2", step_table(lang)), ("own_h2", "<p>%s</p>" % lang.t("g2.own")),
               ("kroky_h2", "<p>%s</p>" % lang.t("g2.kroky"))],
        "g4": [("compare_h2", "<p>%s</p>" % lang.t("g4.compare")),
               ("needs_h2", '<ul class="plain">%s</ul>' % "".join("<li>%s</li>" % lang.t("g4.needs_%d" % i) for i in range(1, 4))),
               ("limits_h2", "<p>%s</p>" % lang.t("g4.limits"))],
        "g5": [("math_h2", "<p>%s</p>" % lang.t("g5.math")),
               ("when_h2", '<ul class="plain">%s</ul>' % "".join("<li>%s</li>" % lang.t("g5.when_%d" % i) for i in range(1, 5))),
               ("kroky_h2", "<p>%s</p>" % lang.t("g5.kroky"))],
        "g3": [("how_h2", "<p>%s</p>" % lang.t("g3.how")),
               ("change_h2", '<ul class="plain">%s</ul>' % "".join("<li>%s</li>" % lang.t("g3.change_%d" % i) for i in range(1, 5))),
               ("limits_h2", "<p>%s</p>" % lang.t("g3.limits"))],
    }[g]
    shot = {"g1": "nudge", "g2": "home", "g3": "route", "g4": "home", "g5": "walk"}[g]
    body = """<article class="wrap prose guide">
<nav class="crumbs" aria-label="Breadcrumb"><a href="{home}">Kroky</a> › <a href="{home}guides/">{guides}</a></nav>
<h1>{h1}</h1>
<div class="answer-grid"><div><p class="answer">{answer}</p><p class="actions">{badge_top}</p></div>{phone}</div>
{sections}
{box}
<h2>{more}</h2>{others}
</article>""".format(
        home=lang.prefix, guides=lang.t("nav.guides"), h1=lang.t(g + ".h1"), answer=lang.t(g + ".answer"),
        phone=phone(lang, shot, cls="phone small", eager=True),
        badge_top=store_badge(lang, "web_guide_%s_top" % g, height=44),
        sections="".join(section_html(lang, g, k, v) for k, v in sections),
        box=app_box(lang, "web_guide_" + g), more=lang.t("guides.h2"),
        others='<ul class="plain links">%s</ul>' % "".join(
            '<li><a href="%sguides/%s/">%s</a></li>' % (lang.prefix, EN[o + ".slug"], lang.t(o + ".h1"))
            for o in GUIDES if o != g))
    path = "guides/%s/" % slug
    article = {"@context": "https://schema.org", "@type": "Article", "headline": plain(lang.t(g + ".h1")),
               "description": plain(lang.t(g + ".description")), "inLanguage": lang.code,
               "url": url_for(lang, path), "mainEntityOfPage": url_for(lang, path), "datePublished": GUIDE_PUBLISHED[g],
               "dateModified": MODIFIED, "author": ORG, "publisher": ORG, "about": {"@id": APP_ENTITY_ID},
               "image": ["%s/og/%s.png" % (BASE_URL, lang.code),
                         "%s/assets/shots/%s/%s.webp" % (BASE_URL, lang.code, shot)]}
    crumbs = breadcrumbs(lang, [("Kroky", ""), (lang.t("nav.guides"), "guides/"), (lang.t(g + ".h1"), path)])
    return path, render(lang, path, lang.t(g + ".title"), lang.t(g + ".description"), body, jsonld=[article, crumbs],
                        og_type="article", modified=MODIFIED)


def guides_index(lang):
    body = """<div class="wrap prose">
<nav class="crumbs" aria-label="Breadcrumb"><a href="{home}">Kroky</a></nav>
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
<nav class="crumbs" aria-label="Breadcrumb"><a href="{home}">Kroky</a></nav>
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


def press_page():
    """English only: journalists and creators read English, and the facts don't change by language."""
    lang = EN_LANG
    shots = "".join('<li><a href="/assets/shots/en/%s.webp">%s</a></li>' % (s, e(caption_title(lang, s))) for s in SHOTS)
    body = """<article class="wrap prose">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Kroky</a></nav>
<h1>Kroky press kit</h1>
<p class="answer">{description}</p>
<h2>Fact sheet</h2>
<ul class="plain">
<li><strong>Name:</strong> Kroky: Walk Breaks ("kroky" means "steps" in Ukrainian, Czech and Slovak)</li>
<li><strong>Platform:</strong> iPhone, iOS 17 or later. On the App Store since November 3, 2026.</li>
<li><strong>Price:</strong> free. Kroky Pro adds sitting nudges, dry-window reminders, Skip my meetings and unlimited loops: $19.99 a year with a 7-day free trial, or $49.99 once (US prices).</li>
<li><strong>Privacy:</strong> no account, no server, no analytics, no tracking. Steps, settings and walk history stay on the iPhone.</li>
<li><strong>Languages:</strong> {n} languages.</li>
<li><strong>Made by:</strong> <a href="{studio}">nakolini</a>, a two-person studio of Dmytro Hryb and Vitalii Kikot.</li>
</ul>
<h2>Downloads</h2>
<ul class="plain">
<li><a href="/assets/icon-512.png">App icon (512 × 512 PNG)</a></li>
<li><a href="/og/en.png">Social image (1200 × 630 PNG)</a></li>
<li>Screenshots (English): <ul class="plain">{shots}</ul></li>
</ul>
<p>Screenshots in each of Kroky's languages are at <code>/assets/shots/&lt;language&gt;/</code>, and the App Store page has the full captioned set.</p>
<h2>Contact</h2>
<p>Writing about Kroky or making a video? Email {email}, and we'll send you a Kroky Pro promo code and answer your questions.</p>
{box}
</article>""".format(description=e(plain(lang.t("home.description"))), n=len(ALL_LANGS), studio=STUDIO_URL, shots=shots,
                     email='<a href="mailto:%s">%s</a>' % (EMAIL, EMAIL), box=app_box(lang, "web_press"))
    return render(lang, "press/", "Kroky press kit · Kroky: Walk Breaks",
                  "Fact sheet, app icon and screenshots for Kroky: Walk Breaks, the iPhone app that plans walk breaks "
                  "sized to your step goal.", body, alternates=False,
                  jsonld=[breadcrumbs(lang, [("Kroky", ""), ("Press kit", "press/")])])


def get_page():
    """A short link to say out loud or print: kroky.nakolini.com/get goes straight to the App Store."""
    url = e(app_store_url("web_get"))
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex">
<title>Kroky on the App Store</title>
<meta http-equiv="refresh" content="0;url={url}">
</head><body><p><a href="{url}">Kroky: Walk Breaks on the App Store</a></p></body></html>
""".format(url=url)


# ---------------------------------------------------------------- site files

def page_paths():
    return ["", "guides/"] + ["guides/%s/" % EN[g + ".slug"] for g in GUIDES] + [
        "support.html", "privacy-policy.html", "terms.html"]


def sitemap():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for path in page_paths():
        for lang in ALL_LANGS:
            out.append("<url><loc>%s</loc><lastmod>%s</lastmod>" % (e(url_for(lang, path)), LASTMOD[url_for(lang, path)]["date"]))
            out.extend('<xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (o.code, e(url_for(o, path)))
                       for o in ALL_LANGS)
            out.append('<xhtml:link rel="alternate" hreflang="x-default" href="%s"/></url>' % e(url_for(EN_LANG, path)))
    press = url_for(EN_LANG, "press/")
    out.append("<url><loc>%s</loc><lastmod>%s</lastmod></url>" % (e(press), LASTMOD[press]["date"]))
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

User-agent: Applebot
Allow: /

User-agent: Perplexity-User
Allow: /

User-agent: CCBot
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
        "- [App Store](%s)" % STORE_URL,
        "- [Press kit](%s/press/): fact sheet, icon and screenshots" % BASE_URL,
        "- [nakolini, the studio behind Kroky](%s)" % STUDIO_URL,
        "",
        "## Facts",
        "",
        "- On the App Store since %s (version 1.0): %s. The App Store lists the developer as Vitalii Kikot, "
        "co-founder of nakolini" % (RELEASED, STORE_URL),
        "- Category: Health & Fitness. Price: free, with in-app purchases (Kroky Pro)",
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
    lines += ["## Optional", "", "- Every page is available in: %s." % ", ".join(
        "%s (%s)" % (l.name, url_for(l, "")) for l in ALL_LANGS), ""]
    return "\n".join(lines)


def load_lastmod():
    path = os.path.join(ROOT, LASTMOD_FILE)
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}


LASTMOD_SEEN = load_lastmod()
LASTMOD = {}
TODAY = os.environ.get("KROKY_TODAY") or datetime.date.today().isoformat()


def stamp(rel, text):
    """Swaps the page's own last-modified date in for MODIFIED, moving it only when the content changed."""
    if not rel.endswith(".html") or rel == "404.html":
        return text
    url = BASE_URL + "/" + (rel[:-len("index.html")] if rel.endswith("index.html") else rel)
    # Asset cache-busting hashes change with every CSS edit; they aren't content.
    digest = hashlib.sha256(re.sub(r"\?v=[0-9a-f]+", "", text).encode("utf-8")).hexdigest()[:16]
    old = LASTMOD_SEEN.get(url)
    date = old["date"] if old and old["hash"] == digest else TODAY
    LASTMOD[url] = {"hash": digest, "date": date}
    return text.replace(MODIFIED, date)


def llms_full_txt():
    """Every English page's text as Markdown, so an assistant can quote Kroky without fetching and parsing HTML."""
    en = EN_LANG
    t = lambda k: plain(en.t(k))
    out = [llms_txt().rstrip(), "", "# Full text", "", "## Kroky for iPhone (%s/)" % BASE_URL, "",
           t("home.h1"), "", t("home.lead"), "", "### %s" % t("how.h2"), ""]
    out += ["%d. %s: %s" % (i, t("how.%d_t" % i), t("how.%d" % i)) for i in range(1, 5)]
    out += ["", "### %s" % t("features.h2"), ""]
    out += ["- %s%s: %s" % (t("features.%d_t" % i), " (Kroky Pro)" if i in PRO_FEATURES else "", t("features.%d" % i))
            for i in range(1, 9)]
    out += ["", "### %s" % t("privacy.h2"), ""] + ["- %s: %s" % (t("privacy.%d_t" % i), t("privacy.%d" % i)) for i in (1, 2, 3)]
    out += ["", "### %s" % t("plans.h2"), "", t("plans.promise") + " " + t("plans.note") + " " + t("plans.price_us"), ""]
    for g in GUIDES:
        out += ["## %s (%s)" % (t(g + ".h1"), url_for(en, "guides/%s/" % EN[g + ".slug"])), "", t(g + ".answer"), ""]
        for k in [k for k in EN if k.startswith(g + ".") and k.endswith("_h2")]:
            base = k[len(g) + 1:-3]
            out += ["### %s" % t(k), ""]
            if g == "g2" and base == "table":
                out += ["| Steps left | Walk | Distance |", "| --- | --- | --- |"]
                for steps in TABLE_STEPS:
                    m = steps * STRIDE_M
                    out.append("| %s | about %s min | %s km (%s mi) |" % (
                        en.num(steps), en.num(round(m / PACE_M_PER_MIN)), en.num(m / 1000, 1), en.num(m / 1609.344, 1)))
                out += ["", t("g2.table_note"), ""]
                continue
            items = sorted(k2 for k2 in EN if re.fullmatch(r"%s\.%s_\d+" % (g, base), k2))
            if items:
                out += ["- " + t(i) for i in items] + [""]
            elif g + "." + base in EN:
                out += [t(g + "." + base), ""]
    s = "support."
    out += ["## Support (%s/support.html)" % BASE_URL, ""]
    for q in ["steps", "nudges", "loop", "restore", "cancel", "avoid", "data"]:
        out += ["### " + t(s + q + "_q"), "", t(s + q + "_a"), ""]
    return "\n".join(out)


def write(rel, text):
    text = stamp(rel, text)
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def clean():
    for d in GENERATED_DIRS:
        p = os.path.join(ROOT, d)
        if os.path.isdir(p):
            shutil.rmtree(p)
    for f in GENERATED_FILES + [n for n in os.listdir(ROOT) if re.fullmatch(r"[0-9a-f]{32}\.txt", n)]:
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
    write("press/index.html", press_page())
    write("get/index.html", get_page())
    write("sitemap.xml", sitemap())
    with open(os.path.join(ROOT, LASTMOD_FILE), "w", encoding="utf-8") as f:
        json.dump(dict(sorted(LASTMOD.items())), f, indent=0)
        f.write("\n")
    write(INDEXNOW_KEY + ".txt", INDEXNOW_KEY)
    write("llms-full.txt", llms_full_txt())
    write("robots.txt", ROBOTS)
    write("llms.txt", llms_txt())
    write(".nojekyll", "")
    write("CNAME", BASE_URL.split("//")[1] + "\n")
    print("built %d languages" % len(ALL_LANGS))


if __name__ == "__main__":
    main()
