document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.querySelector('.sidebar');
  const toggle = document.querySelector('.mobile-nav-toggle');

  if (sidebar && toggle) {
    toggle.addEventListener('click', () => {
      const isOpen = sidebar.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    sidebar.querySelectorAll('.nav-item').forEach((link) => {
      link.addEventListener('click', () => {
        if (window.innerWidth <= 992 && sidebar.classList.contains('is-open')) {
          sidebar.classList.remove('is-open');
          toggle.setAttribute('aria-expanded', 'false');
        }
      });
    });
  }
  // adjust article images margin when page loads
  const cleanedPath = window.location.pathname.replace(/\/+$/, '') || '/';
  const isAbout = cleanedPath === '/about';
  document.querySelectorAll('.article-body img').forEach((img) => {
    img.style.margin = isAbout ? '1rem' : '1rem 0';
  });

  // open brand grid links in new tab
  document.querySelectorAll('.brand-grid a').forEach((anchor) => {
    anchor.setAttribute('target', '_blank');
    anchor.setAttribute('rel', 'noreferrer noopener');
  });

  if (document.body.classList.contains('layout-project')) {
    const projectImages = document.querySelectorAll('.project-content img');
    if (projectImages.length) {
      const lightbox = document.createElement('div');
      lightbox.className = 'project-lightbox';
      lightbox.innerHTML = '<button class=\"close\" aria-label=\"Close\">&times;</button><img alt=\"Project media\">';
      document.body.appendChild(lightbox);
      const lightboxImg = lightbox.querySelector('img');
      const closeBtn = lightbox.querySelector('.close');
      const closeLightbox = () => lightbox.classList.remove('visible');
      closeBtn.addEventListener('click', closeLightbox);
      lightbox.addEventListener('click', (event) => {
        if (event.target === lightbox) closeLightbox();
      });
      document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') closeLightbox();
      });
      projectImages.forEach((img) => {
        img.style.cursor = 'zoom-in';
        img.addEventListener('click', () => {
          lightboxImg.src = img.src;
          lightboxImg.alt = img.alt || '';
          lightbox.classList.add('visible');
        });
      });
    }
  }
  const tocCards = document.querySelectorAll('.toc-card');
  const slugCache = new Map();

  const slugify = (text) => {
    const basic = text
      .toLowerCase()
      .trim()
      .replace(/[\s]+/g, '-')
      .replace(/[^\w-]/g, '');
    if (!slugCache.has(basic)) {
      slugCache.set(basic, 0);
      return basic;
    }
    const count = slugCache.get(basic) + 1;
    slugCache.set(basic, count);
    return `${basic}-${count}`;
  };

  tocCards.forEach((card) => {
    const list = card.querySelector('.toc-list');
    const sourceSelector = card.getAttribute('data-toc-source');
    const source = document.querySelector(sourceSelector);

    if (!list || !source) {
      card.hidden = true;
      return;
    }

    const headings = source.querySelectorAll('h2, h3, h4');
    if (!headings.length) {
      card.hidden = true;
      return;
    }

    const tocEntries = [];

    headings.forEach((heading) => {
      const level = parseInt(heading.tagName.slice(1), 10);
      if (!heading.id) {
        heading.id = slugify(heading.textContent);
      }
      const li = document.createElement('li');
      li.className = `toc-item level-${level}`;
      const anchor = document.createElement('a');
      anchor.href = `#${heading.id}`;
      anchor.textContent = heading.textContent.trim();
      li.appendChild(anchor);
      li.dataset.headingId = heading.id;
      list.appendChild(li);
      tocEntries.push({ heading, li });
    });

    const setActive = (id) => {
      tocEntries.forEach(({ li }) => {
        li.classList.toggle('active', li.dataset.headingId === id);
      });
    };

    const updateActiveHeading = () => {
      if (!tocEntries.length) return;
      const offset = 140;
      let currentId = tocEntries[0].heading.id;
      for (const { heading } of tocEntries) {
        const top = heading.getBoundingClientRect().top;
        if (top - offset <= 0) {
          currentId = heading.id;
        } else {
          break;
        }
      }
      setActive(currentId);
    };

    let ticking = false;
    const onScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          updateActiveHeading();
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    updateActiveHeading();
  });

  const consentKey = 'td_cookie_consent_v1';
  const consentDefaults = { necessary: true, functional: false, analytics: false };
  const banner = document.querySelector('[data-cookie-banner]');
  const preferenceTriggers = document.querySelectorAll('[data-open-consent]');
  const consentToggles = document.querySelectorAll('[data-consent-toggle]');
  let consentState = loadConsentState();

  function loadConsentState() {
    try {
      const stored = localStorage.getItem(consentKey);
      if (!stored) return null;
      const parsed = JSON.parse(stored);
      return {
        ...consentDefaults,
        functional: Boolean(parsed.functional),
        analytics: Boolean(parsed.analytics),
      };
    } catch (error) {
      console.warn('Unable to read consent state', error);
      return null;
    }
  }

  function persistConsentState(nextState, { silent } = {}) {
    consentState = { ...consentDefaults, ...nextState };
    try {
      localStorage.setItem(
        consentKey,
        JSON.stringify({ ...consentState, updatedAt: new Date().toISOString() }),
      );
    } catch (error) {
      console.warn('Unable to persist consent state', error);
    }
    updateToggleUI();
    applyConsentToPage();
    if (!silent) hideConsentBanner();
  }

  function updateToggleUI() {
    consentToggles.forEach((toggle) => {
      const key = toggle.dataset.consentToggle;
      if (!key) return;
      toggle.checked = Boolean(consentState?.[key]);
    });
  }

  function showConsentBanner() {
    if (!banner) return;
    updateToggleUI();
    banner.hidden = false;
    banner.classList.add('is-visible');
  }

  function hideConsentBanner() {
    if (!banner) return;
    banner.classList.remove('is-visible');
    banner.hidden = true;
  }

  function readToggleState() {
    const next = { ...consentDefaults, ...(consentState || {}) };
    consentToggles.forEach((toggle) => {
      const key = toggle.dataset.consentToggle;
      if (key) next[key] = Boolean(toggle.checked);
    });
    return next;
  }

  function loadGiscusWidget(container) {
    if (!container || container.dataset.consentLoaded === 'true') return;
    const slot = container.querySelector('.consent-block__slot');
    if (!slot) return;
    const script = document.createElement('script');
    script.src = 'https://giscus.app/client.js';
    script.async = true;
    script.crossOrigin = 'anonymous';
    script.setAttribute('data-repo', container.dataset.giscusRepo || '');
    script.setAttribute('data-repo-id', container.dataset.giscusRepoId || '');
    script.setAttribute('data-category', container.dataset.giscusCategory || '');
    script.setAttribute('data-category-id', container.dataset.giscusCategoryId || '');
    script.setAttribute('data-mapping', container.dataset.giscusMapping || 'pathname');
    script.setAttribute('data-strict', container.dataset.giscusStrict || '0');
    script.setAttribute('data-reactions-enabled', container.dataset.giscusReactions || '1');
    script.setAttribute('data-emit-metadata', container.dataset.giscusEmitMetadata || '0');
    script.setAttribute('data-input-position', container.dataset.giscusInputPosition || 'bottom');
    script.setAttribute('data-theme', container.dataset.giscusTheme || 'noborder_gray');
    script.setAttribute('data-lang', container.dataset.giscusLang || 'en');
    slot.innerHTML = '';
    slot.appendChild(script);
    const noscript = document.createElement('noscript');
    noscript.textContent = 'Please enable JavaScript to view the comments.';
    slot.appendChild(noscript);
    container.dataset.consentLoaded = 'true';
  }

  function disableConsentElement(container) {
    if (!container) return;
    const slot = container.querySelector('.consent-block__slot');
    if (slot) slot.innerHTML = '';
    container.dataset.consentLoaded = 'false';
    const placeholder = container.querySelector('[data-consent-placeholder]');
    if (placeholder) placeholder.hidden = false;
  }

  function applyConsentToPage() {
    document.querySelectorAll('[data-consent-category]').forEach((element) => {
      const category = element.dataset.consentCategory;
      if (!category) return;
      const isAllowed = Boolean(consentState?.[category]);
      const placeholder = element.querySelector('[data-consent-placeholder]');
      if (placeholder) placeholder.hidden = isAllowed;

      if (!isAllowed) {
        disableConsentElement(element);
        return;
      }

      if (element.dataset.consentType === 'giscus') {
        loadGiscusWidget(element);
      }
    });
  }

  document.addEventListener('click', (event) => {
    const action = event.target.closest('[data-consent-action]');
    if (!action) return;
    const actionType = action.dataset.consentAction;
    if (actionType === 'accept-all') {
      persistConsentState({ functional: true, analytics: true });
    } else if (actionType === 'reject') {
      persistConsentState({ functional: false, analytics: false });
    } else if (actionType === 'save') {
      persistConsentState(readToggleState());
    } else if (actionType === 'accept-functional') {
      persistConsentState({ ...(consentState || consentDefaults), functional: true }, { silent: true });
    }
  });

  preferenceTriggers.forEach((trigger) => {
    trigger.addEventListener('click', showConsentBanner);
  });

  if (consentState) {
    updateToggleUI();
    applyConsentToPage();
  } else {
    consentState = { ...consentDefaults };
    showConsentBanner();
  }

  const optimizeImages = () => {
    const images = document.querySelectorAll('img');
    images.forEach((img) => {
      if (!img.getAttribute('loading')) {
        img.setAttribute('loading', 'lazy');
      }
      if (!img.getAttribute('decoding')) {
        img.setAttribute('decoding', 'async');
      }
    });
  };

  optimizeImages();
});
