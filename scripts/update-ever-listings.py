#!/usr/bin/env python3
"""
update-ever-listings.py
Scrapes eversandiego.com/featured-properties.html, generates individual
property pages for agents.truelegacyhomes.com, and updates the index.html
Current Properties grid.
"""

import re
import os
import sys
import json
import time
import requests
from bs4 import BeautifulSoup

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

SKIP_ADDRESSES = ['1812 highland']  # Already handled as TLH renovation page

# ── NAV (shared across all pages) ──────────────────────────────────────────
NAV_HTML = '''\
  <!-- ─── NAV ─────────────────────────────────────────────────────────── -->
  <header class="sticky top-0 z-50 bg-white border-b border-gray-100 shadow-sm">
    <div class="max-w-6xl mx-auto px-4">
      <div class="flex items-center justify-between h-16">
        <a href="/" class="flex items-center gap-3">
          <img src="/images/leafrealtor.png" alt="True Legacy Homes" class="h-10 w-10 object-contain">
          <div class="leading-tight">
            <div class="text-sm font-bold text-tlh-dark" style="font-family:\'Source Serif Pro\',Georgia,serif;">True Legacy Homes</div>
            <div class="text-xs text-tlh-teal font-semibold tracking-widest uppercase">Realtor Partners</div>
          </div>
        </a>
        <nav class="hidden md:flex items-center gap-8">
          <a href="/properties/" class="nav-link text-sm font-semibold text-tlh-teal">Current Properties</a>
          <a href="/#buy-box" class="nav-link text-sm font-semibold text-gray-700">Buy Box</a>
          <a href="/#tracks" class="nav-link text-sm font-semibold text-gray-700">How It Works</a>
          <a href="/#contact" class="nav-link text-sm font-semibold text-gray-700">Contact</a>
        </nav>
        <div class="hidden md:flex items-center gap-3">
          <a href="tel:6194501702" class="text-sm font-semibold text-tlh-dark hover:text-tlh-teal transition">(619) 450-1702</a>
          <a href="/#contact" class="bg-tlh-teal text-white px-5 py-2 rounded-[5px] text-sm font-semibold hover:bg-tlh-teal-dark transition">Send Us a Property</a>
        </div>
        <button id="mobile-menu-btn" class="md:hidden p-2 text-gray-600" aria-label="Menu">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
        </button>
      </div>
      <div id="mobile-menu" class="pb-4 border-t border-gray-100">
        <nav class="flex flex-col gap-1 pt-3">
          <a href="/properties/" class="text-sm font-semibold text-tlh-teal py-2">Current Properties</a>
          <a href="/#buy-box" class="text-sm font-semibold text-gray-700 py-2 hover:text-tlh-teal">Buy Box</a>
          <a href="/#tracks" class="text-sm font-semibold text-gray-700 py-2 hover:text-tlh-teal">How It Works</a>
          <a href="/#contact" class="text-sm font-semibold text-gray-700 py-2 hover:text-tlh-teal">Contact</a>
          <a href="tel:6194501702" class="text-sm font-semibold text-tlh-teal py-2">(619) 450-1702</a>
        </nav>
      </div>
    </div>
  </header>'''

FOOTER_HTML = '''\
  <!-- ─── FOOTER ────────────────────────────────────────────────────────── -->
  <footer class="bg-white border-t border-gray-100 py-10">
    <div class="max-w-6xl mx-auto px-4">
      <div class="flex flex-col md:flex-row items-center justify-between gap-6">
        <div class="flex items-center gap-3">
          <img src="/images/leafrealtor.png" alt="True Legacy Homes" class="h-7 w-auto">
          <span class="text-sm font-semibold text-tlh-dark" style="font-family:\'Source Serif Pro\',Georgia,serif;">True Legacy Homes — Realtor Partners</span>
        </div>
        <nav class="flex gap-6 text-sm text-gray-500">
          <a href="/properties/" class="hover:text-tlh-teal transition">Properties</a>
          <a href="/#buy-box" class="hover:text-tlh-teal transition">Buy Box</a>
          <a href="/#contact" class="hover:text-tlh-teal transition">Contact</a>
          <a href="https://www.truelegacyhomes.com" class="hover:text-tlh-teal transition">Main Site ↗</a>
        </nav>
        <p class="text-sm text-gray-400">© 2026 True Legacy Homes. All rights reserved.</p>
      </div>
    </div>
  </footer>

  <script>
    document.getElementById('mobile-menu-btn').addEventListener('click', function() {
      document.getElementById('mobile-menu').classList.toggle('open');
    });
  </script>'''

MOBILE_JS = '''\
  <script>
    document.getElementById('mobile-menu-btn').addEventListener('click', function() {
      document.getElementById('mobile-menu').classList.toggle('open');
    });
  </script>'''

LIGHTBOX_CSS = '''\
    .gallery-item { cursor: pointer; }
    .gallery-item img { transition: transform 0.35s ease; }
    .gallery-item:hover img { transform: scale(1.04); }
    .lightbox { display: none; position: fixed; z-index: 9999; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.92); align-items: center; justify-content: center; }
    .lightbox.active { display: flex; }
    .lightbox-content { position: relative; max-width: 90%; max-height: 90vh; display: flex; align-items: center; justify-content: center; }
    .lightbox img { max-width: 100%; max-height: 90vh; object-fit: contain; border-radius: 4px; }
    .lightbox-close, .lightbox-prev, .lightbox-next { position: absolute; background: rgba(255,255,255,0.1); color: white; border: none; cursor: pointer; padding: 1rem 1.25rem; font-size: 1.75rem; transition: background 0.2s; z-index: 10000; line-height: 1; }
    .lightbox-close:hover, .lightbox-prev:hover, .lightbox-next:hover { background: rgba(255,255,255,0.22); }
    .lightbox-close { top: 20px; right: 20px; font-size: 2rem; }
    .lightbox-prev { left: 16px; top: 50%; transform: translateY(-50%); }
    .lightbox-next { right: 16px; top: 50%; transform: translateY(-50%); }
    .lightbox-caption { position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.6); color: white; padding: 0.4rem 1rem; border-radius: 9999px; font-size: 0.8rem; letter-spacing: 0.05em; white-space: nowrap; }'''

LIGHTBOX_JS = '''\
  <!-- ─── LIGHTBOX ──────────────────────────────────────────────────────── -->
  <div class="lightbox" id="lightbox" role="dialog" aria-modal="true">
    <div class="lightbox-content">
      <button class="lightbox-close" id="lb-close" aria-label="Close">×</button>
      <button class="lightbox-prev" id="lb-prev" aria-label="Previous">‹</button>
      <img id="lb-img" src="" alt="">
      <button class="lightbox-next" id="lb-next" aria-label="Next">›</button>
      <div class="lightbox-caption" id="lb-caption"></div>
    </div>
  </div>
  <script>
    (function(){
      var items = Array.from(document.querySelectorAll('.gallery-item'));
      var lb = document.getElementById('lightbox');
      var lbImg = document.getElementById('lb-img');
      var lbCap = document.getElementById('lb-caption');
      var cur = 0;
      function open(i){ cur=i; var it=items[i]; lbImg.src=it.dataset.src; lbImg.alt=it.dataset.alt||''; lbCap.textContent=(i+1)+' / '+items.length; lb.classList.add('active'); document.body.style.overflow='hidden'; }
      function close(){ lb.classList.remove('active'); document.body.style.overflow=''; }
      function prev(){ open((cur-1+items.length)%items.length); }
      function next(){ open((cur+1)%items.length); }
      items.forEach(function(el,i){ el.addEventListener('click',function(){ open(i); }); });
      document.getElementById('lb-close').addEventListener('click',close);
      document.getElementById('lb-prev').addEventListener('click',prev);
      document.getElementById('lb-next').addEventListener('click',next);
      lb.addEventListener('click',function(e){ if(e.target===lb) close(); });
      document.addEventListener('keydown',function(e){ if(!lb.classList.contains('active')) return; if(e.key==='Escape') close(); if(e.key==='ArrowLeft') prev(); if(e.key==='ArrowRight') next(); });
    })();
  </script>'''


def slugify(address, city):
    combined = (address + '-' + city).lower()
    combined = re.sub(r'[^a-z0-9\s-]', '', combined)
    combined = re.sub(r'\s+', '-', combined.strip())
    combined = re.sub(r'-+', '-', combined)
    return combined


def validate_image(url):
    try:
        r = SESSION.head(url, timeout=5, allow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False


def fetch_listing_page(url):
    """Fetch a detail page and extract images, description, and property details."""
    try:
        r = SESSION.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
    except Exception as e:
        print(f"  ⚠️  Could not fetch detail page: {e}")
        return {}, []

    details = {}

    # Full description
    desc_el = soup.select_one('.description p')
    if desc_el:
        details['description'] = desc_el.get_text(strip=True)

    # Property info fields
    for item in soup.select('.infos-item .item-copy, .infos-item .pg-copy'):
        text = item.get_text(' ', strip=True)
        def clean(s):
            """Strip Roya CMS 'span widget' artifacts and zero-width chars."""
            s = re.sub(r'span widget', '', s, flags=re.IGNORECASE)
            s = re.sub(r'[\u200b-\u200f\u00ad]', '', s)
            return s.strip()
        if 'Year Built:' in text:
            details['year_built'] = clean(re.sub(r'.*Year Built:\s*', '', text))
        elif 'Lot Sq Ft' in text:
            m = re.search(r'([\d,]+)\s*Lot Sq Ft', text)
            if m:
                details['lot_sqft'] = m.group(1)
        elif 'Type:' in text:
            details['type'] = clean(re.sub(r'.*Type:\s*', '', text))
        elif 'Stories:' in text:
            details['stories'] = clean(re.sub(r'.*Stories:\s*', '', text))
        elif 'MLS#:' in text:
            details['mls'] = clean(re.sub(r'.*MLS#:\s*', '', text))
        elif 'Community:' in text:
            raw = clean(re.sub(r'.*Community:\s*', '', text))
            # Strip leading zip code prefix like '92075 - '
            details['community'] = re.sub(r'^\d{5}\s*-\s*', '', raw)

    # Virtual tour
    vt = soup.find('a', href=re.compile(r'propertypanorama'))
    if vt:
        details['virtual_tour'] = vt['href']

    # Images from slider
    imgs = []
    for li in soup.select('.detail-slider li'):
        img = li.find('img')
        if img and img.get('src') and 'crmls.org' in img['src']:
            imgs.append(img['src'])
    # deduplicate
    seen = set()
    unique_imgs = []
    for img in imgs:
        if img not in seen:
            seen.add(img)
            unique_imgs.append(img)

    return details, unique_imgs


def fetch_all_listings():
    print("📡 Fetching eversandiego.com/featured-properties.html ...")
    r = SESSION.get('https://eversandiego.com/featured-properties.html', timeout=15)
    soup = BeautifulSoup(r.text, 'html.parser')

    properties = []
    for prop in soup.select('.property'):
        # Address
        h2 = prop.select_one('.title.street h2 a')
        if not h2:
            continue
        address = h2.get_text(strip=True)

        # Skip TLH-managed property
        if any(skip in address.lower() for skip in SKIP_ADDRESSES):
            print(f"  ⏭️  Skipping {address} (TLH property)")
            continue

        # Location
        loc_el = prop.select_one('.location')
        location = loc_el.get_text(strip=True) if loc_el else ''
        # Parse "Solana Beach, CA 92075"
        loc_parts = location.split(',')
        city = loc_parts[0].strip() if loc_parts else ''
        state_zip = loc_parts[1].strip() if len(loc_parts) > 1 else ''
        zip_match = re.search(r'\d{5}', state_zip)
        zipcode = zip_match.group(0) if zip_match else ''

        # Price
        price_el = prop.select_one('.price')
        price = price_el.get_text(strip=True) if price_el else ''

        # Stats
        beds_el = prop.select_one('.bedrooms .content')
        baths_el = prop.select_one('.bathrooms .content')
        sqft_el = prop.select_one('.area .content')
        beds = beds_el.get_text(strip=True) if beds_el else ''
        baths = baths_el.get_text(strip=True) if baths_el else ''
        sqft = sqft_el.get_text(strip=True) if sqft_el else ''

        # Short description
        desc_el = prop.select_one('.propertyCom')
        short_desc = desc_el.get_text(strip=True) if desc_el else ''

        # Hero image
        photo_el = prop.select_one('.property-photo')
        hero_img = ''
        if photo_el and photo_el.get('style'):
            m = re.search(r'url\(([^)]+)\)', photo_el['style'])
            if m:
                hero_img = m.group(1).strip('"\'')

        # Detail URL
        link_el = prop.select_one('a.property-link')
        detail_url = link_el['href'] if link_el else ''
        if detail_url and not detail_url.startswith('http'):
            detail_url = 'https://eversandiego.com/' + detail_url.lstrip('/')

        slug = slugify(address, city)

        properties.append({
            'address': address,
            'city': city,
            'zipcode': zipcode,
            'price': price,
            'beds': beds,
            'baths': baths,
            'sqft': sqft,
            'short_desc': short_desc,
            'hero_img': hero_img,
            'detail_url': detail_url,
            'slug': slug,
        })

    return properties


def enrich_property(prop):
    """Fetch detail page, validate images, return enriched prop."""
    print(f"  🔍 {prop['address']}, {prop['city']} ...")
    details, raw_imgs = fetch_listing_page(prop['detail_url'])
    time.sleep(0.5)

    # Validate images
    valid_imgs = []
    # Always check hero first
    if prop['hero_img'] and validate_image(prop['hero_img']):
        valid_imgs.append(prop['hero_img'])

    for img in raw_imgs:
        if img == prop['hero_img']:
            continue
        if len(valid_imgs) >= 8:
            break
        if validate_image(img):
            valid_imgs.append(img)
        time.sleep(0.1)

    # If hero was broken, use first valid from detail page
    if not valid_imgs and raw_imgs:
        for img in raw_imgs:
            if validate_image(img):
                valid_imgs.append(img)
                break

    prop.update(details)
    prop['images'] = valid_imgs
    prop['hero_img'] = valid_imgs[0] if valid_imgs else prop.get('hero_img', '')
    print(f"     ✅ {len(valid_imgs)} images, desc: {'yes' if prop.get('description') else 'no'}")
    if not valid_imgs:
        print(f"     ⛔ No valid images — skipping")
        return None
    return prop


def build_gallery_html(images, address):
    if not images:
        return ''
    cols = {1: 'grid-cols-1', 2: 'grid-cols-2', 3: 'grid-cols-3', 4: 'grid-cols-2 md:grid-cols-4'}
    n = len(images)
    grid_class = 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4'
    if n == 1:
        grid_class = 'grid-cols-1 max-w-2xl'
    elif n == 2:
        grid_class = 'grid-cols-2'

    items = []
    for i, img in enumerate(images):
        items.append(f'''          <div class="gallery-item relative overflow-hidden rounded-[5px] shadow-sm aspect-[4/3] cursor-pointer"
               data-src="{img}" data-alt="{address} photo {i+1}">
            <img src="{img}" alt="{address} photo {i+1}" class="w-full h-full object-cover hover:scale-105 transition duration-300" loading="{'eager' if i==0 else 'lazy'}">
          </div>''')

    return f'''    <!-- ─── GALLERY ──────────────────────────────────────────────────────── -->
    <section class="py-6 bg-white">
      <div class="max-w-6xl mx-auto px-4">
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
{chr(10).join(items)}
        </div>
      </div>
    </section>'''


def build_property_page(prop):
    address = prop['address']
    city = prop['city']
    zipcode = prop['zipcode']
    price = prop['price']
    beds = prop['beds']
    baths = prop['baths']
    sqft = prop['sqft']
    description = prop.get('description', prop.get('short_desc', ''))
    images = prop.get('images', [])
    hero = prop.get('hero_img', images[0] if images else '')
    year_built = prop.get('year_built', '')
    lot_sqft = prop.get('lot_sqft', '')
    prop_type = prop.get('type', '')
    stories = prop.get('stories', '')
    mls = prop.get('mls', '')
    community = prop.get('community', '')
    detail_url = prop.get('detail_url', '')

    # Details table rows
    detail_rows = []
    if price:
        detail_rows.append(('List Price', price))
    if beds:
        detail_rows.append(('Bedrooms', beds))
    if baths:
        detail_rows.append(('Bathrooms', baths))
    if sqft:
        detail_rows.append(('Living Area', f'{int(sqft):,} sq ft' if sqft.isdigit() else sqft + ' sq ft'))
    if lot_sqft:
        detail_rows.append(('Lot Size', f'{lot_sqft} sq ft'))
    if year_built:
        detail_rows.append(('Year Built', year_built))
    if prop_type:
        detail_rows.append(('Type', prop_type))
    if stories:
        detail_rows.append(('Stories', stories))
    if community:
        detail_rows.append(('Community', community))
    if mls:
        detail_rows.append(('MLS #', mls))

    rows_html = '\n'.join(
        f'              <tr class="border-b border-gray-100"><td class="py-2 pr-4 text-sm font-semibold text-gray-500 whitespace-nowrap">{k}</td><td class="py-2 text-sm text-gray-800">{v}</td></tr>'
        for k, v in detail_rows
    )

    gallery_html = build_gallery_html(images, address)

    ever_link = f'<a href="{detail_url}" target="_blank" rel="noopener" class="text-tlh-teal hover:underline">eversandiego.com</a>' if detail_url else 'eversandiego.com'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{address} — {city} | True Legacy Homes Realtor Partners</title>
  <meta name="description" content="View {address}, {city}, CA {zipcode} — {price}. {beds} bed, {baths} bath, {sqft} sqft. Partner listing via Ever San Diego.">
  <link rel="icon" type="image/png" href="https://www.truelegacyhomes.com/images/tlhICON.webp">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+Pro:wght@400;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/tailwind.min.css">
  {'<link rel="preload" as="image" href="' + hero + '">' if hero else ''}
  <style>
    html {{ scroll-behavior: smooth; }}
    [id] {{ scroll-margin-top: 80px; }}
    body {{ font-family: 'Inter', sans-serif; }}
    h1, h2, h3, h4 {{ font-family: 'Source Serif Pro', Georgia, serif; color: #132b42; }}
    .hero-text {{ color: #fff !important; }}
    .nav-link {{ transition: color 0.15s; }}
    .nav-link:hover {{ color: #158c8b; }}
    #mobile-menu {{ display: none; }}
    #mobile-menu.open {{ display: block; }}
{LIGHTBOX_CSS}
  </style>
</head>
<body class="bg-white text-gray-800 text-lg leading-loose antialiased">

{NAV_HTML}

  <main>

    <!-- ─── HERO ─────────────────────────────────────────────────────────── -->
    <section class="py-14 md:py-20 bg-tlh-dark text-white">
      <div class="max-w-6xl mx-auto px-4">
        <a href="/properties/" class="inline-flex items-center gap-1 text-sm text-white/50 hover:text-white transition mb-6">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
          Back to Current Properties
        </a>
        <div class="flex flex-wrap items-start gap-2 mb-3">
          <span class="bg-[#1d3557] text-white text-xs font-semibold tracking-widest uppercase px-3 py-1 rounded-sm">Ever San Diego</span>
          <span class="bg-green-600 text-white text-xs font-semibold tracking-widest uppercase px-3 py-1 rounded-sm">Active</span>
        </div>
        <h1 class="hero-text text-4xl md:text-5xl font-bold mb-2" style="font-family:'Source Serif Pro',Georgia,serif;">{address}</h1>
        <p class="text-white/70 text-xl mb-6">{city}, CA {zipcode}</p>
        <div class="flex flex-wrap gap-6 items-center">
          <span class="text-3xl font-bold text-tlh-teal">{price}</span>
          <div class="flex gap-4 text-white/80 text-base">
            {f'<span>{beds} Beds</span>' if beds else ''}
            {f'<span class="text-white/30">·</span><span>{baths} Baths</span>' if baths else ''}
            {f'<span class="text-white/30">·</span><span>{sqft} sqft</span>' if sqft else ''}
          </div>
        </div>
      </div>
    </section>

{gallery_html}

    <!-- ─── DETAILS ───────────────────────────────────────────────────────── -->
    <section class="py-14 md:py-20" style="background-color:#f9f4eb;">
      <div class="max-w-6xl mx-auto px-4">
        <div class="grid md:grid-cols-3 gap-10">

          <!-- Left: description + details table -->
          <div class="md:col-span-2">
            <h2 class="text-2xl font-bold mb-4">About This Property</h2>
            <p class="text-gray-700 text-base leading-relaxed mb-8">{description}</p>

            <h3 class="text-xl font-bold mb-3">Property Details</h3>
            <table class="w-full">
              <tbody>
{rows_html}
              </tbody>
            </table>

            <div class="mt-8 p-4 bg-white rounded-[5px] border border-gray-200 text-sm text-gray-500">
              Listing data courtesy of {ever_link} and Ever Eternity, Pacific Sotheby's International Realty (CA DRE# 01794748).
              Data © CRMLS. All information should be independently verified.
            </div>
          </div>

          <!-- Right: contact sidebar -->
          <div>
            <div class="bg-white rounded-[5px] border border-gray-200 p-6 sticky top-24">
              <h3 class="text-xl font-bold mb-1">Interested in this property?</h3>
              <p class="text-sm text-gray-500 mb-5">Your buyer gets exclusive access — before bidding wars start.</p>
              <form id="contact-form" action="https://formspree.io/f/info@truelegacyhomes.com" method="POST">
                <input type="hidden" name="property" value="{address}, {city}, CA {zipcode}">
                <input type="hidden" name="price" value="{price}">
                <div class="flex flex-col gap-3">
                  <input type="text" name="name" placeholder="Your Name" required
                    class="w-full border border-gray-200 rounded-[5px] px-4 py-2.5 text-sm focus:outline-none focus:border-tlh-teal">
                  <input type="tel" name="phone" placeholder="Phone Number" required
                    class="w-full border border-gray-200 rounded-[5px] px-4 py-2.5 text-sm focus:outline-none focus:border-tlh-teal">
                  <input type="email" name="email" placeholder="Email Address" required
                    class="w-full border border-gray-200 rounded-[5px] px-4 py-2.5 text-sm focus:outline-none focus:border-tlh-teal">
                  <input type="text" name="brokerage" placeholder="Brokerage"
                    class="w-full border border-gray-200 rounded-[5px] px-4 py-2.5 text-sm focus:outline-none focus:border-tlh-teal">
                  <textarea name="message" placeholder="Message (optional)" rows="3"
                    class="w-full border border-gray-200 rounded-[5px] px-4 py-2.5 text-sm focus:outline-none focus:border-tlh-teal resize-none"></textarea>
                  <button type="submit"
                    class="w-full bg-tlh-teal text-white py-3 rounded-[5px] text-sm font-semibold hover:bg-tlh-teal-dark transition">
                    Request Info
                  </button>
                </div>
              </form>
              <div class="mt-4 pt-4 border-t border-gray-100 text-center">
                <a href="tel:6194501702" class="text-sm font-semibold text-tlh-dark hover:text-tlh-teal transition">(619) 450-1702</a>
                <span class="text-gray-300 mx-2">·</span>
                <a href="mailto:info@truelegacyhomes.com" class="text-sm text-gray-500 hover:text-tlh-teal transition">Email Us</a>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>

    <!-- ─── CTA ───────────────────────────────────────────────────────────── -->
    <section class="py-24 bg-tlh-dark text-white text-center">
      <div class="max-w-2xl mx-auto px-6">
        <p class="text-sm font-semibold tracking-widest uppercase text-tlh-teal mb-4">Track 1 — Listing Agents</p>
        <h2 class="hero-text text-3xl md:text-4xl font-bold mb-4" style="font-family:'Source Serif Pro',Georgia,serif;">Have a seller who fits our buy box?</h2>
        <p class="text-white/70 text-lg mb-8 leading-relaxed">All-cash, no contingencies, 24–48hr offer decision. Estate contents handled. We close fast and make it easy.</p>
        <a href="/#contact" class="inline-block bg-tlh-teal text-white px-10 py-4 rounded-[5px] font-semibold text-base hover:bg-tlh-teal-dark transition">Send Us a Property</a>
      </div>
    </section>

  </main>

{FOOTER_HTML}

{LIGHTBOX_JS}

</body>
</html>'''


def build_properties_index(properties):
    """Build /properties/index.html listing all Ever SD properties."""
    cards = []
    for prop in properties:
        slug = prop['slug']
        address = prop['address']
        city = prop['city']
        zipcode = prop['zipcode']
        price = prop['price']
        beds = prop['beds']
        baths = prop['baths']
        sqft = prop['sqft']
        hero = prop.get('hero_img', '')
        short = prop.get('short_desc', '')
        if len(short) > 120:
            short = short[:120].rstrip() + '...'

        cards.append(f'''          <a href="/properties/{slug}/" class="group block rounded-[5px] overflow-hidden shadow-sm border border-gray-200 hover:shadow-lg hover:border-tlh-teal transition bg-white">
            <div class="relative aspect-[4/3] overflow-hidden">
              <img src="{hero}" alt="{address} {city}" class="w-full h-full object-cover group-hover:scale-105 transition duration-300" loading="lazy">
              <span class="absolute top-3 left-3 bg-[#1d3557] text-white text-xs font-semibold tracking-widest uppercase px-3 py-1 rounded-sm">Ever San Diego</span>
            </div>
            <div class="p-6">
              <h3 class="text-xl font-bold text-tlh-dark mb-1 group-hover:text-tlh-teal transition">{address}</h3>
              <p class="text-sm text-gray-500 mb-3">{city}, CA {zipcode}</p>
              <p class="text-gray-600 text-base mb-4">{short}</p>
              <div class="flex items-center justify-between">
                <span class="text-base font-bold text-tlh-teal">{price}</span>
                <span class="inline-flex items-center gap-1 text-tlh-teal font-semibold text-sm group-hover:gap-2 transition-all">
                  View
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                </span>
              </div>
            </div>
          </a>''')

    grid = '\n'.join(cards)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Current Properties | True Legacy Homes Realtor Partners</title>
  <meta name="description" content="Partner listings from Ever San Diego — featured pre-renovation and market-ready properties in Southern California.">
  <link rel="icon" type="image/png" href="https://www.truelegacyhomes.com/images/tlhICON.webp">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+Pro:wght@400;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/tailwind.min.css">
  <style>
    html {{ scroll-behavior: smooth; }}
    body {{ font-family: 'Inter', sans-serif; }}
    h1, h2, h3, h4 {{ font-family: 'Source Serif Pro', Georgia, serif; color: #132b42; }}
    .hero-text {{ color: #fff !important; }}
    .nav-link {{ transition: color 0.15s; }}
    .nav-link:hover {{ color: #158c8b; }}
    #mobile-menu {{ display: none; }}
    #mobile-menu.open {{ display: block; }}
  </style>
</head>
<body class="bg-white text-gray-800 text-lg leading-loose antialiased">

{NAV_HTML}

  <main>
    <section class="py-14 md:py-20 bg-tlh-dark text-white">
      <div class="max-w-6xl mx-auto px-4">
        <p class="text-sm font-semibold tracking-widest uppercase text-tlh-teal mb-4">Partner Listings</p>
        <h1 class="hero-text text-4xl md:text-5xl font-bold mb-4" style="font-family:'Source Serif Pro',Georgia,serif;">Current Properties</h1>
        <p class="text-white/70 text-xl max-w-2xl leading-relaxed">
          Featured listings from our partner <strong class="text-white">Ever San Diego</strong> — plus our own pre-renovation inventory. Give your buyers first access.
        </p>
      </div>
    </section>

    <section class="py-14 md:py-20" style="background-color:#f9f4eb;">
      <div class="max-w-6xl mx-auto px-4">
        <div class="mb-8">
          <p class="text-sm font-semibold tracking-widest uppercase text-tlh-teal mb-2">True Legacy Homes</p>
          <h2 class="text-2xl font-bold mb-6">Pre-Renovation Inventory</h2>
          <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
            <a href="/renovations/1812-highland/" class="group block rounded-[5px] overflow-hidden shadow-sm border border-gray-200 hover:shadow-lg hover:border-tlh-teal transition bg-white">
              <div class="relative aspect-[4/3] overflow-hidden">
                <img src="https://www.truelegacyhomes.com/renovations/1812-highland/images/highland-kitchen.webp"
                     alt="1812 Highland Newport Beach pre-renovation"
                     class="w-full h-full object-cover group-hover:scale-105 transition duration-300" loading="lazy">
                <span class="absolute top-3 left-3 bg-tlh-teal text-white text-xs font-semibold tracking-widest uppercase px-3 py-1 rounded-sm">Pre-Renovation</span>
              </div>
              <div class="p-6">
                <h3 class="text-xl font-bold text-tlh-dark mb-1 group-hover:text-tlh-teal transition">1812 Highland</h3>
                <p class="text-sm text-gray-500 mb-3">Newport Beach, CA 92660</p>
                <p class="text-gray-600 text-base mb-4">Full renovation — kitchen, primary suite, bathrooms, family room, entry. Design renders available.</p>
                <div class="flex items-center justify-between">
                  <span class="text-base font-bold text-tlh-teal">$4,495,000</span>
                  <span class="inline-flex items-center gap-1 text-tlh-teal font-semibold text-sm group-hover:gap-2 transition-all">View <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg></span>
                </div>
              </div>
            </a>
          </div>

          <p class="text-sm font-semibold tracking-widest uppercase text-tlh-teal mb-2">Partner Listings</p>
          <h2 class="text-2xl font-bold mb-6">Ever San Diego Featured Properties</h2>
          <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
{grid}
          </div>
        </div>
      </div>
    </section>
  </main>

{FOOTER_HTML}

</body>
</html>'''


def update_index_html(properties):
    """Replace the Current Properties grid in index.html."""
    index_path = os.path.join(BASE, 'index.html')
    with open(index_path, 'r') as f:
        html = f.read()

    # Build the 1812 Highland card (corrected Newport Beach)
    highland_card = '''          <!-- 1812 Highland -->
          <a href="/renovations/1812-highland/" class="group block rounded-[5px] overflow-hidden shadow-sm border border-gray-200 hover:shadow-lg hover:border-tlh-teal transition bg-white">
            <div class="relative aspect-[4/3] overflow-hidden">
              <img src="https://www.truelegacyhomes.com/renovations/1812-highland/images/highland-kitchen.webp"
                   alt="1812 Highland Newport Beach pre-renovation"
                   class="w-full h-full object-cover group-hover:scale-105 transition duration-300" loading="lazy">
              <span class="absolute top-3 left-3 bg-tlh-teal text-white text-xs font-semibold tracking-widest uppercase px-3 py-1 rounded-sm">Pre-Renovation</span>
            </div>
            <div class="p-6">
              <h3 class="text-xl font-bold text-tlh-dark mb-1 group-hover:text-tlh-teal transition">1812 Highland</h3>
              <p class="text-sm text-gray-500 mb-3">Newport Beach, CA</p>
              <p class="text-gray-600 text-base mb-4">Full renovation — kitchen, primary suite, bathrooms, family room, entry. Design renders available.</p>
              <div class="flex items-center justify-between">
                <span class="text-sm font-semibold text-tlh-teal">Design Preview Available</span>
                <span class="inline-flex items-center gap-1 text-tlh-teal font-semibold text-sm group-hover:gap-2 transition-all">
                  View
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                </span>
              </div>
            </div>
          </a>'''

    # Build Ever SD cards
    ever_cards = []
    for prop in properties:
        slug = prop['slug']
        address = prop['address']
        city = prop['city']
        zipcode = prop['zipcode']
        price = prop.get('price', '')
        hero = prop.get('hero_img', '')
        short = prop.get('short_desc', '')
        if len(short) > 120:
            short = short[:120].rstrip() + '...'

        ever_cards.append(f'''
          <!-- {address} -->
          <a href="/properties/{slug}/" class="group block rounded-[5px] overflow-hidden shadow-sm border border-gray-200 hover:shadow-lg hover:border-tlh-teal transition bg-white">
            <div class="relative aspect-[4/3] overflow-hidden">
              <img src="{hero}" alt="{address} {city}"
                   class="w-full h-full object-cover group-hover:scale-105 transition duration-300" loading="lazy">
              <span class="absolute top-3 left-3 bg-[#1d3557] text-white text-xs font-semibold tracking-widest uppercase px-3 py-1 rounded-sm">Ever San Diego</span>
            </div>
            <div class="p-6">
              <h3 class="text-xl font-bold text-tlh-dark mb-1 group-hover:text-tlh-teal transition">{address}</h3>
              <p class="text-sm text-gray-500 mb-3">{city}, CA {zipcode}</p>
              <p class="text-gray-600 text-base mb-4">{short}</p>
              <div class="flex items-center justify-between">
                <span class="text-base font-bold text-tlh-teal">{price}</span>
                <span class="inline-flex items-center gap-1 text-tlh-teal font-semibold text-sm group-hover:gap-2 transition-all">
                  View
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                </span>
              </div>
            </div>
          </a>''')

    new_grid = highland_card + '\n' + '\n'.join(ever_cards)

    # Replace between the grid div open and the "mt-8" mobile link div
    pattern = r'(        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">)\s*.*?(        </div>\s*\n\s*<div class="mt-8)'
    replacement = r'\1\n' + new_grid + r'\n\n\2'
    new_html = re.sub(pattern, replacement, html, flags=re.DOTALL)

    if new_html == html:
        print("  ⚠️  Could not find grid pattern in index.html — writing manually")
        # Fallback: find and replace the grid div content
        start = html.find('<div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">')
        end = html.find('</div>\n\n        <div class="mt-8', start)
        if start != -1 and end != -1:
            new_html = html[:start + len('<div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">')] + '\n' + new_grid + '\n\n        ' + html[end + 8:]

    with open(index_path, 'w') as f:
        f.write(new_html)
    print(f"  ✅ index.html updated")


def main():
    print("\n🏠 Ever San Diego Listings Updater\n" + "="*40)

    # Fetch listings
    properties = fetch_all_listings()
    print(f"\n📋 Found {len(properties)} properties to process\n")

    # Enrich each
    enriched = []
    for prop in properties:
        enriched_prop = enrich_property(prop)
        if enriched_prop is not None:
            enriched.append(enriched_prop)

    # Generate property pages
    print(f"\n📝 Generating property pages ...")
    for prop in enriched:
        slug = prop['slug']
        out_dir = os.path.join(BASE, 'properties', slug)
        os.makedirs(out_dir, exist_ok=True)
        page_html = build_property_page(prop)
        with open(os.path.join(out_dir, 'index.html'), 'w') as f:
            f.write(page_html)
        print(f"  ✅ /properties/{slug}/")

    # Generate properties index
    print(f"\n📄 Generating /properties/index.html ...")
    idx_html = build_properties_index(enriched)
    with open(os.path.join(BASE, 'properties', 'index.html'), 'w') as f:
        f.write(idx_html)
    print(f"  ✅ /properties/index.html")

    # Update main index
    print(f"\n🔄 Updating index.html Current Properties section ...")
    update_index_html(enriched)

    # Summary
    summary = {
        'processed': len(enriched),
        'properties': [
            {'address': p['address'], 'city': p['city'], 'slug': p['slug'],
             'images': len(p.get('images', [])), 'has_description': bool(p.get('description'))}
            for p in enriched
        ]
    }
    print(f"\n{'='*40}")
    print(f"✅ Done! {len(enriched)} properties processed.")
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
