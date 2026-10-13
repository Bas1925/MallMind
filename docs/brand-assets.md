# Store logo sources

Imported 12 October 2026. The running app loads all ten files from `frontend/public/brands/`; it does not contact a logo service, CDN, or brand website. The exact store-slug mapping lives in `StoreBrand.tsx`.

## Vector assets

These eight vector marks come from [Simple Icons 14.0.0](https://github.com/simple-icons/simple-icons/tree/14.0.0), a versioned source with recorded brand references. Its [CC0 license](https://github.com/simple-icons/simple-icons/blob/14.0.0/LICENSE.md) is included as `public/brands/SIMPLE-ICONS-LICENSE.txt`. This does not waive brand trademark rights.

| Store | Local file | Vector source | Brand reference recorded by the source |
|---|---|---|---|
| Adidas | adidas.svg | [Asset](https://raw.githubusercontent.com/simple-icons/simple-icons/14.0.0/icons/adidas.svg) | [Adidas](https://www.adidas.com/) |
| Apple | apple.svg | [Asset](https://raw.githubusercontent.com/simple-icons/simple-icons/14.0.0/icons/apple.svg) | [Apple](https://www.apple.com/) |
| H&M | handm.svg | [Asset](https://raw.githubusercontent.com/simple-icons/simple-icons/14.0.0/icons/handm.svg) | [H&M](https://www2.hm.com/en_gb/index.html) |
| McDonald's | mcdonalds.svg | [Asset](https://raw.githubusercontent.com/simple-icons/simple-icons/14.0.0/icons/mcdonalds.svg) | [McDonald's newsroom](https://www.mcdonalds.com/gb/en-gb/newsroom.html) |
| Nike | nike.svg | [Asset](https://raw.githubusercontent.com/simple-icons/simple-icons/14.0.0/icons/nike.svg) | [Nike](https://www.nike.com/) |
| Samsung | samsung.svg | [Asset](https://raw.githubusercontent.com/simple-icons/simple-icons/14.0.0/icons/samsung.svg) | [Samsung brand identity](https://www.samsung.com/us/about-us/brand-identity/logo/) |
| Starbucks | starbucks.svg | [Asset](https://raw.githubusercontent.com/simple-icons/simple-icons/14.0.0/icons/starbucks.svg) | [Starbucks](https://www.starbucks.com/) |
| Zara | zara.svg | [Asset](https://raw.githubusercontent.com/simple-icons/simple-icons/14.0.0/icons/zara.svg) | [Zara](https://www.zara.com/) |

Path geometry is unchanged. Fill colors use the collection's brand metadata; viewBox whitespace is trimmed for consistent optical sizing. Only passive SVG path geometry is imported, without scripts, remote references, styles, or event handlers. These are identifiable vector renditions of the brands, not a claim that each file is its newest corporate master artwork.

## Official storefront images

- **MUJI:** `muji.png` — [official storefront](https://www.muji.us/), [original image](https://www.muji.us/cdn/shop/files/MUJI_Logo_NEW.png?v=1766089002&width=600). Unmodified PNG.
- **Super-Pharm:** `super-pharm.png` — [official storefront](https://shop.super-pharm.co.il/), the `#logo-top-img img` asset named `sp-online-130.png`. Unmodified 130 px storefront logo, kept at its native display width rather than enlarged. It includes the storefront's ONLINE lockup.

Official storefront images remain their owners' artwork; the app's MIT code license does not relicense them.

## Display and fallback

- Logos appear in store cards, detail dialogs, and map sidebar listings with their aspect ratios preserved. Cards and dialogs expose accessible image names; sidebar logos are decorative beside the visible store name.
- A failed image falls back to the store name.
- NOVA Cinema, Pages Bookstore, Pizza Napoli, Rooftop Cafe, and Sushi Kaito are fictional seeded concepts, so they keep text identities rather than borrowing an unrelated business's logo.
- NOVA Mall is a fictional portfolio demonstration, not an official mall or brand partner. No affiliation, opening-hours accuracy, or brand endorsement is claimed.
