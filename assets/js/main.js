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
});
