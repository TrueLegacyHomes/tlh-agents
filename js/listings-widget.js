/**
 * listings-widget.js
 * Fetches /data/listings.json and renders Ever San Diego listing cards
 * into any element with id="ever-listings-grid".
 *
 * Single source of truth: data/listings.json (written by update-ever-listings.py)
 * Used by: index.html (homepage Current Properties section)
 *          properties/index.html (full listings page)
 */

(function () {
  var CONTAINER_ID = 'ever-listings-grid';

  function cardHTML(p) {
    var desc = p.short_desc || '';
    if (desc.length > 130) desc = desc.slice(0, 130).trimEnd() + '...';
    return [
      '<a href="/properties/' + p.slug + '/" class="group block rounded-[5px] overflow-hidden shadow-sm border border-gray-200 hover:shadow-lg hover:border-tlh-teal transition bg-white">',
      '  <div class="relative aspect-[4/3] overflow-hidden">',
      '    <img src="' + p.hero_img + '" alt="' + p.address + ' ' + p.city + '"',
      '         class="w-full h-full object-cover group-hover:scale-105 transition duration-300" loading="lazy">',
      '  </div>',
      '  <div class="p-6">',
      '    <h3 class="text-xl font-bold text-tlh-dark mb-1 group-hover:text-tlh-teal transition">' + p.address + '</h3>',
      '    <p class="text-sm text-gray-500 mb-3">' + p.city + ', CA ' + p.zipcode + '</p>',
      '    <p class="text-gray-600 text-base mb-4">' + desc + '</p>',
      '    <div class="flex items-center justify-between">',
      '      <span class="text-base font-bold text-tlh-teal">' + p.price + '</span>',
      '      <span class="inline-flex items-center gap-1 text-tlh-teal font-semibold text-sm group-hover:gap-2 transition-all">',
      '        View',
      '        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>',
      '      </span>',
      '    </div>',
      '  </div>',
      '</a>',
    ].join('\n');
  }

  function render(listings) {
    var el = document.getElementById(CONTAINER_ID);
    if (!el) return;
    if (!listings || !listings.length) {
      el.innerHTML = '<p class="text-gray-500 col-span-3 text-center py-8">No listings available right now — check back soon.</p>';
      return;
    }
    el.innerHTML = listings.map(cardHTML).join('\n');
  }

  function init() {
    var el = document.getElementById(CONTAINER_ID);
    if (!el) return;

    // Show skeleton while loading
    el.innerHTML = [1, 2, 3].map(function () {
      return '<div class="rounded-[5px] overflow-hidden shadow-sm border border-gray-200 bg-white animate-pulse">' +
        '<div class="aspect-[4/3] bg-gray-200"></div>' +
        '<div class="p-6"><div class="h-5 bg-gray-200 rounded mb-2 w-3/4"></div>' +
        '<div class="h-4 bg-gray-100 rounded mb-4 w-1/2"></div>' +
        '<div class="h-4 bg-gray-100 rounded w-full"></div></div></div>';
    }).join('');

    fetch('/data/listings.json?v=' + Date.now())
      .then(function (r) { return r.json(); })
      .then(function (data) { render(data.listings || []); })
      .catch(function () {
        // Silently fall back — static cards from last script run remain visible
        el.innerHTML = '';
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
