# Languages and accessibility

> Stable release: **2026.11.04.05** · Stable channel: **main** · Development channel: **dev**


## Offline runtime

Plus follows Unraid's session locale and reads bundled JSON. It does not contact a translation service during installed operation. Empty session locale selects English; unsupported values fall back to English instead of becoming file paths.

## Coverage and aliases

There are 42 canonical catalogs with 336 messages each. Labels, full dialogs, help, CLI descriptions, history presentation, and notification templates are covered. Native exports include three published pack aliases:

| Alias | Canonical catalog |
| --- | --- |
| `da_DA` | `da_DK` |
| `ja_JA` | `ja_JP` |
| `ko_KO` | `ko_KR` |

## Complete catalog list

| Code | Language/variant | Direction |
| --- | --- | --- |
| `af_ZA` | Afrikaans (Afrikaans) | LTR |
| `ar_AR` | العربية (Arabic) | RTL |
| `bn_BN` | বাংলা (Bengali) | LTR |
| `bs_BA` | Bosanski (Bosnian) | LTR |
| `ca_CA` | Català (Catalan) | LTR |
| `cs_CZ` | Čeština (Czech) | LTR |
| `da_DK` | Dansk (Danish) | LTR |
| `de_DE` | Deutsch (German) | LTR |
| `el_GR` | ελληνικά (Greek) | LTR |
| `en_US` | English (American) | LTR |
| `es_ES` | Español (Spanish) | LTR |
| `et_EE` | Eesti (Estonian) | LTR |
| `fa_FA` | فارسی (Persian) | RTL |
| `fi_FI` | Suomi (Finnish) | LTR |
| `fr_FR` | Français (French) | LTR |
| `ga_IE` | Gaeilge (Irish) | LTR |
| `he_IL` | עברית (Hebrew) | RTL |
| `hi_IN` | हिन्दी (Hindi) | LTR |
| `hr_HR` | Hrvatski (Croatian) | LTR |
| `hu_HU` | Magyar (Hungarian) | LTR |
| `id_ID` | Bahasa (Indonesian) | LTR |
| `it_IT` | Italiano (Italian) | LTR |
| `ja_JP` | 日本語 (Japanese) | LTR |
| `ko_KR` | 한국어 (Korean) | LTR |
| `lv_LV` | Latviešu (Latvian) | LTR |
| `nl_NL` | Nederlands (Dutch) | LTR |
| `no_NO` | Norsk (Norwegian) | LTR |
| `pl_PL` | Polski (Polish) | LTR |
| `pt_BR` | Português (Brazilian) | LTR |
| `pt_PT` | Português (Portuguese) | LTR |
| `ro_RO` | Română (Romanian) | LTR |
| `ru_RU` | Русский (Russian) | LTR |
| `sk_SK` | Slovenčina (Slovak) | LTR |
| `sl_SI` | Slovenščina (Slovenian) | LTR |
| `sr_RS` | Српски Језик (Serbian) | LTR |
| `sv_SE` | Svenska (Swedish) | LTR |
| `th_TH` | ไทย (Thai) | LTR |
| `tr_TR` | Türkçe (Turkish) | LTR |
| `uk_UA` | Українська (Ukrainian) | LTR |
| `vi_VN` | Tiếng Việt (Vietnamese) | LTR |
| `zh_CN` | 中文 (Chinese) | LTR |
| `zh_TW` | 繁體中文 (Traditional Chinese) | LTR |

## Embedded page behavior

Native processing can expand inline markers before plugin evaluation. Plus lookup happens during evaluation. Dialog values are JSON encoded, labels are escaped, and help is rendered after lookup. Tests reproduce native ordering through actual Unraid parsers.

## RTL and literal data

Arabic, Persian, and Hebrew use RTL form/popup presentation. Editable machine values remain LTR. Paths, IDs, host/kernel text, command names, keys, severity codes, and persistent history identity stay literal.

## Quality and reporting

Catalogs are machine authored and checked for source coverage, placeholders, links/markup, unsafe content, formatting execution, unchanged prose, and browser behavior. This is not native-speaker review. Report locale, route, exact phrase, and proposed wording.

The registry records the official Unraid language-key source blob and published language-pack source. Authoring is maintainer-only; normal checks and runtime remain offline.
