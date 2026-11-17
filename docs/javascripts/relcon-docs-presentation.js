(() => {
  let key = null;
  // Keep the saved preference separate from the viewport's effective mode.
  let enabled = false;
  const desktop = window.matchMedia('(min-width: 76.25em)');
  const presenting = () => enabled && desktop.matches;
  let targets = [];
  let active = 0;
  let pending = false;


  const content = () => document.querySelector('.presentation-content');
  const offset = () => {
    const header = document.querySelector('.md-header');
    return Math.max(0, header?.getBoundingClientRect().bottom || 0) + 32;
  };

  function updateNavigation() {
    const page = content();
    if (!page) return;
    const nav = page.querySelector('.presentation-nav');
    nav.hidden = !presenting() || targets.length < 2;
    if (nav.hidden) return;
    let index = 0;
    targets.forEach((target, i) => {
      if (target.getBoundingClientRect().top <= offset() + 48) index = i;
    });
    // A short final section may not be able to reach the top of the viewport.
    if (window.scrollY > 0 && window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) {
      index = targets.length - 1;
    }
    active = index;
    const heading = targets[index].matches('h1,h2,h3')
      ? targets[index] : null;
    const label = heading?.textContent.replace(/¶\s*$/, '').trim() || `Section ${index + 1}`;
    nav.querySelector('[data-section-title]').textContent = label;
    nav.querySelector('[data-section-count]').textContent = `${index + 1} / ${targets.length}`;
    nav.querySelector('[data-section-step="-1"]').disabled = index === 0;
    nav.querySelector('[data-section-step="1"]').disabled = index === targets.length - 1;
  }

  function render() {
    const page = content();
    if (!page) { targets = []; return; }
    if (key === null) {
      const siteRoot = new URL(page.dataset.presentationRoot, location.href).pathname;
      key = `relcon-docs:presentation:${siteRoot}`;
      try { enabled = localStorage.getItem(key) === 'true'; } catch (_) {}
    }
    const button = page.querySelector('.presentation-toggle');
    const controls = page.querySelector('.presentation-controls');
    const copyButton = page.querySelector('[data-md-copy-url]');
    if (copyButton && copyButton.parentElement !== controls) controls.prepend(copyButton);
    page.classList.toggle('presentation-mode', presenting());
    button.setAttribute('aria-pressed', String(presenting()));
    button.hidden = !desktop.matches;

    // Only top-level Markdown rules are boundaries, not rules inside examples.
    const first = page.querySelector(':scope > h1');
    const boundaries = [...page.querySelectorAll(':scope > hr')]
      .map(rule => rule.nextElementSibling)
      .filter(target => target && !target.matches('hr, .presentation-nav'));
    targets = first ? [first, ...boundaries] : boundaries;
    updateNavigation();
  }

  function move(step) {
    const index = Math.max(0, Math.min(targets.length - 1, active + step));
    if (!presenting() || !targets[index] || index === active) return;
    const target = targets[index];
    const permalink = target.matches('h1,h2,h3,h4,h5,h6')
      ? target.querySelector('a.headerlink') : null;
    if (permalink) {
      // Use the theme's anchor navigation so its table of contents stays in sync.
      permalink.click();
    } else {
      target.scrollIntoView({behavior: 'instant', block: 'start'});
    }
    updateNavigation();
  }

  document.addEventListener('click', event => {
    if (!(event.target instanceof Element)) return;
    if (desktop.matches && event.target.closest('.presentation-toggle')) {
      enabled = !enabled;
      try { localStorage.setItem(key, String(enabled)); } catch (_) {}
      render();
    }
    const step = event.target.closest('[data-section-step]');
    if (step && !step.disabled) move(Number(step.dataset.sectionStep));
  });

  document.addEventListener('keydown', event => {
    if (!presenting() || !content() || event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    if (event.target instanceof Element && event.target.closest('input, textarea, select, [contenteditable], [role="dialog"], [role="slider"], .glightbox-container')) return;
    if (document.querySelector('.glightbox-open, dialog[open]')) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      enabled = false;
      try { localStorage.setItem(key, 'false'); } catch (_) {}
      render();
      return;
    }
    if (targets.length < 2 || window.getSelection()?.toString()) return;
    if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
      event.preventDefault();
      move(event.key === 'ArrowRight' ? 1 : -1);
    }
  });

  function onScroll() {
    if (!presenting() || pending) return;
    pending = true;
    requestAnimationFrame(() => { pending = false; updateNavigation(); });
  }
  window.addEventListener('scroll', onScroll, {passive: true});
  window.addEventListener('resize', onScroll);
  desktop.addEventListener('change', render);

  if (typeof document$ !== 'undefined') document$.subscribe(render);
  else if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', render);
  else render();
})();
