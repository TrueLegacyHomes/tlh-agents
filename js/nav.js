/**
 * nav.js — Shared navigation for agents.truelegacyhomes.com
 * Edit this file to update the nav on ALL pages instantly.
 * Pages include this with: <div id="site-nav"></div><script src="/js/nav.js"></script>
 */
(function () {
  var html = `
  <header class="sticky top-0 z-50 bg-white border-b border-gray-100 shadow-sm">
    <div class="max-w-6xl mx-auto px-4">
      <div class="flex items-center justify-between h-16">

        <!-- Logo -->
        <a href="/" class="flex items-center gap-3">
          <img src="/images/leafrealtor.png" alt="True Legacy Homes" class="h-10 w-10 object-contain">
          <div class="leading-tight">
            <div class="text-sm font-bold text-tlh-dark" style="font-family:'Source Serif Pro',Georgia,serif;">True Legacy Homes</div>
            <div class="text-xs text-tlh-teal font-semibold tracking-widest uppercase">Realtor Partners</div>
          </div>
        </a>

        <!-- Desktop nav -->
        <nav class="hidden md:flex items-center gap-6">
          <a href="/properties/" class="nav-link text-sm font-semibold text-gray-700">Current Properties</a>
          <a href="/#buy-box" class="nav-link text-sm font-semibold text-gray-700">Buy Box</a>
          <a href="/#tracks" class="nav-link text-sm font-semibold text-gray-700">How It Works</a>
          <a href="/#contact" class="nav-link text-sm font-semibold text-gray-700">Contact</a>
        </nav>

        <!-- Desktop CTA -->
        <div class="hidden md:flex items-center gap-3">
          <a href="tel:6194501702" class="text-sm font-semibold text-tlh-dark hover:text-tlh-teal transition">(619) 450-1702</a>
          <a href="/#contact" style="background:#158c8b;color:#fff;padding:10px 20px !important;border-radius:5px;font-size:.875rem;font-weight:600;display:inline-block;line-height:1.4;text-decoration:none;">Send Us a Property</a>
        </div>

        <!-- Mobile hamburger -->
        <button id="mobile-menu-btn" class="md:hidden p-2 text-gray-600" aria-label="Menu">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
          </svg>
        </button>
      </div>

      <!-- Mobile menu -->
      <div id="mobile-menu" class="pb-4 border-t border-gray-100" style="display:none;">
        <nav class="flex flex-col gap-1 pt-3">
          <a href="/properties/" class="text-sm font-semibold text-gray-700 py-2 hover:text-tlh-teal">Current Properties</a>
          <a href="/#buy-box" class="text-sm font-semibold text-gray-700 py-2 hover:text-tlh-teal">Buy Box</a>
          <a href="/#tracks" class="text-sm font-semibold text-gray-700 py-2 hover:text-tlh-teal">How It Works</a>
          <a href="/#contact" class="text-sm font-semibold text-gray-700 py-2 hover:text-tlh-teal">Contact</a>
          <a href="tel:6194501702" class="text-sm font-semibold text-tlh-teal py-2">(619) 450-1702</a>
          <a href="/#contact" style="background:#158c8b;color:#fff;padding:10px 20px !important;border-radius:5px;font-size:.875rem;font-weight:600;display:block;line-height:1.4;text-align:center;text-decoration:none;margin-top:4px;">Send Us a Property</a>
        </nav>
      </div>
    </div>
  </header>`;

  var placeholder = document.getElementById('site-nav');
  if (placeholder) {
    placeholder.outerHTML = html;
  }

  // Wire mobile menu toggle after insertion
  document.addEventListener('DOMContentLoaded', function () {
    var btn = document.getElementById('mobile-menu-btn');
    var menu = document.getElementById('mobile-menu');
    if (btn && menu) {
      btn.addEventListener('click', function () {
        menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
      });
    }
  });
})();
