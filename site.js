(function () {
  'use strict';

  function ready(fn) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn);
    else fn();
  }

  const MENUS = {
    'fmenu-desktop': {
      title: 'Formations',
      cols: [
        {
          label: 'Prévention & Sécurité',
          links: [
            ['UFA Campus Sécurité', '/cap-secure-academy/'],
            ['TFP APS — Agent de sécurité', '/formations/securite/tfp-aps-agent-prevention-securite/'],
            ['A3P — Protection des personnes', '/formations/securite/a3p-agent-protection-physique-personnes-initiale/'],
            ['SSIAP 1 · 2 · 3', '/formations/securite/ssiap-1-initial/'],
            ['SST & secourisme', '/formations/securite/sst-sauveteur-secouriste-travail/'],
            ['Habilitation électrique', '/formations/securite/habilitation-electrique-h0b0/'],
            ['AIPR', '/formations/securite/aipr/']
          ]
        },
        {
          label: 'Transport de personnes',
          links: [
            ['UFA Campus Transport', '/cap-transport-academy/'],
            ['Chauffeur VTC', '/formations/transport/vtc-chauffeur-prive/'],
            ['Conducteur de taxi', '/formations/transport/taxi-conducteur/'],
            ['Passerelle Taxi ↔ VTC', '/formations/transport/passerelle-taxi-vtc/'],
            ['Formation continue', '/formations/transport/vtc-formation-continue/'],
            ['TPMR', '/formations/transport/tpmr-transport-personnes-mobilite-reduite/']
          ]
        }
      ],
      width: 720
    },
    'nav-menu-financements': {
      links: [
        ['Financement CPF', '/financement-cpf/'],
        ['OPCO & employeurs', '/entreprises/'],
        ['France Travail', '/faq/#financement'],
        ['Questions fréquentes', '/faq/']
      ], width: 260
    },
    'nav-menu-ressources': {
      links: [
        ['Fiches métiers', '/metiers/'],
        ['Guides pratiques', '/guides/'],
        ['Blog & Actualités', '/blog/'],
        ['Album photos', '/album-photos/'],
        ['Vérifier un titre', '/verification/']
      ], width: 260
    },
    'nav-menu-propos': {
      links: [
        ['Qui sommes-nous', '/a-propos/'],
        ['Certification Qualiopi', '/certification-qualiopi/'],
        ['Indicateurs de résultats', '/indicateurs-resultats/'],
        ['Clients & partenaires', '/clients-partenaires/'],
        ['Accessibilité & Handicap', '/accessibilite/'],
        ['Notre histoire', '/a-propos/']
      ], width: 280
    }
  };

  const MOBILE_LINKS = [
    ['Formations', '/formations/'], ['Planning', '/planning/'], ['Entreprises', '/entreprises/'],
    ['Financement CPF', '/financement-cpf/'], ['Fiches métiers', '/metiers/'], ['Blog', '/blog/'],
    ['À propos', '/a-propos/'], ['Contact', '/contact/'], ['E-learning', 'https://oflms.vercel.app/login'],
    ['S’inscrire', '/inscription/']
  ];

  const icon = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg>';

  function styledPanel(id) {
    const p = document.createElement('div');
    p.id = id;
    p.className = 'nav-panel';
    p.style.cssText = 'position:absolute;top:calc(100% + 8px);left:0;z-index:80;background:#fff;border:1px solid #dde4f0;border-radius:14px;box-shadow:0 18px 45px rgba(13,27,62,.15);padding:16px;';
    return p;
  }

  /* Assistant conversationnel (sans serveur : réponses guidées + renvoi WhatsApp). */
  const CHAT_INTENTS = [
    {
      keys: ['bonjour', 'salut', 'hello', 'coucou'],
      answer: 'Bonjour 👋 Je peux vous aider sur les formations, le financement, la certification, le planning ou les contacts. Choisissez une question ci-dessous ou écrivez la vôtre.'
    },
    {
      keys: ['cpf', 'financement', 'opco', 'france travail', 'prix', 'cout', 'payer', 'financer'],
      answer: 'Nos formations peuvent être financées selon votre situation : CPF, OPCO ou France Travail. Le détail est sur la page <a href="/financement-cpf/">Financement CPF</a> et dans la <a href="/faq/#financement">FAQ</a>.'
    },
    {
      keys: ['qualiopi', 'certifie', 'certification', 'qualite', 'organisme'],
      answer: 'Oui, UFA Campus est certifié Qualiopi au titre des actions de formation. Plus d’informations sur la page <a href="/certification-qualiopi/">Certification Qualiopi</a>.'
    },
    {
      keys: ['distance', 'en ligne', 'elearning', 'visio', 'presentiel'],
      answer: 'Une partie de nos formations est accessible à distance, à votre rythme. Les formations de sécurité et de transport comportent souvent une partie en présentiel à Neuilly-Plaisance. Voir le <a href="/formations/">catalogue</a> et la <a href="/faq/">FAQ</a>.'
    },
    {
      keys: ['delai', 'demarr', 'debut', 'quand', 'inscription', 'session'],
      answer: 'Après votre demande, nous vous recontactons rapidement pour valider votre projet et votre financement. Un délai légal de 11 jours s’applique souvent pour le CPF. Consultez le <a href="/planning/">planning</a> et la <a href="/faq/">FAQ</a>.'
    },
    {
      keys: ['adresse', 'lieu', 'ou', 'neuilly', 'salle', 'local'],
      answer: 'Les formations en présentiel ont lieu au <strong>2 rue Vincent Van Gogh, 93360 Neuilly-Plaisance</strong>. Détails et accès sur la page <a href="/contact/">Contact et accès</a>.'
    },
    {
      keys: ['telephone', 'appeler', 'mail', 'email', 'contact', 'whatsapp', 'joindre', 'conseiller', 'humain'],
      answer: 'Vous pouvez nous joindre au <a href="tel:0981888222">0981888222</a>, par <a href="mailto:Ufacampus3@gmail.com">e-mail</a> ou sur <a href="https://wa.me/33981888222?text=Bonjour%2C%20je%20souhaite%20des%20informations%20sur%20vos%20formations." target="_blank" rel="noopener noreferrer">WhatsApp</a>. Voir la page <a href="/contact/">Contact</a>.'
    },
    {
      keys: ['planning', 'date', 'calendrier'],
      answer: 'Toutes les sessions et les dates sont sur la page <a href="/planning/">Planning des formations</a>.'
    },
    {
      keys: ['sst', 'ssiap', 'aps', 'vtc', 'taxi', 'aipr', 'habilitation', 'formation', 'catalogue'],
      answer: 'Nous proposons des formations en prévention & sécurité (SSIAP, SST, APS, AIPR, habilitation électrique) et en transport (VTC, taxi, TPMR). Découvrez le <a href="/formations/">catalogue complet</a>.'
    },
    {
      keys: ['handicap', 'accessibilite', 'pmr', 'amenagement'],
      answer: 'Nous étudions chaque situation avec notre référent handicap. Consultez la page <a href="/accessibilite/">Accessibilité & Handicap</a>.'
    },
    {
      keys: ['entreprise', 'employeur', 'equipe'],
      answer: 'Nous accompagnons aussi les entreprises : analyse de besoins, financement OPCO et formations sur mesure. Voir la page <a href="/entreprises/">Entreprises</a>.'
    }
  ];

  function normalizeChat(s) {
    return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
  }
  function matchChat(q, key) {
    if (key.length <= 4) return new RegExp('(^|[^a-z])' + key + '([^a-z]|$)').test(q);
    return q.indexOf(key) !== -1;
  }
  function chatReply(text) {
    const q = normalizeChat(text);
    for (const intent of CHAT_INTENTS) {
      if (intent.keys.some(k => matchChat(q, k))) return intent.answer;
    }
    return null;
  }

  function initChatbot(chatBtn, contactWrapper, hideContact) {
    if (!chatBtn || document.getElementById('ufa-chat')) return;

    const panel = document.createElement('section');
    panel.id = 'ufa-chat';
    panel.className = 'ufa-chat';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', 'Assistant UFA Campus');
    panel.hidden = true;
    panel.innerHTML =
      '<div class="ufa-chat-head">' +
        '<span class="ufa-chat-bot" aria-hidden="true">🤖</span>' +
        '<span class="ufa-chat-title"><strong>Assistant UFA Campus</strong><span>Réponse automatique · 7j/7</span></span>' +
        '<button type="button" class="ufa-chat-close" aria-label="Fermer le chat">×</button>' +
      '</div>' +
      '<div class="ufa-chat-body" aria-live="polite"></div>' +
      '<div class="ufa-chat-quick" aria-label="Questions fréquentes">' +
        '<button type="button" data-q="Financement CPF">Financement CPF</button>' +
        '<button type="button" data-q="Certifié Qualiopi ?">Certifié Qualiopi ?</button>' +
        '<button type="button" data-q="Formation à distance">À distance</button>' +
        '<button type="button" data-q="Délais de démarrage">Délais</button>' +
        '<button type="button" data-q="Adresse et accès">Adresse</button>' +
        '<button type="button" data-q="Parler à un conseiller">Parler à un conseiller</button>' +
      '</div>' +
      '<form class="ufa-chat-form">' +
        '<label class="sr-only" for="ufa-chat-input">Votre message</label>' +
        '<input id="ufa-chat-input" type="text" autocomplete="off" placeholder="Écrivez votre question…" />' +
        '<button type="submit" aria-label="Envoyer le message">➤</button>' +
      '</form>';
    document.body.appendChild(panel);

    const body = panel.querySelector('.ufa-chat-body');
    const form = panel.querySelector('.ufa-chat-form');
    const input = panel.querySelector('input');
    const quick = panel.querySelector('.ufa-chat-quick');

    function addMessage(content, who) {
      const div = document.createElement('div');
      div.className = 'ufa-chat-msg ' + who;
      if (who === 'user') div.textContent = content;
      else div.innerHTML = content; // réponses définies par le site uniquement
      body.appendChild(div);
      body.scrollTop = body.scrollHeight;
      return div;
    }
    function say(content) {
      const typing = addMessage('<span class="ufa-chat-dots">•••</span>', 'bot');
      setTimeout(() => { typing.innerHTML = content; body.scrollTop = body.scrollHeight; }, 420);
    }
    function ask(question) {
      const text = question.trim();
      if (!text) return;
      addMessage(text, 'user');
      input.value = '';
      const answer = chatReply(text);
      if (answer) {
        say(answer);
      } else {
        const wa = 'https://wa.me/33981888222?text=' + encodeURIComponent('Bonjour, ma question : ' + text);
        say('Je n’ai pas de réponse précise à cette question. Un conseiller peut vous répondre sur <a href="' + wa + '" target="_blank" rel="noopener noreferrer">WhatsApp</a>, au <a href="tel:0981888222">0981888222</a> ou par <a href="mailto:Ufacampus3@gmail.com">e-mail</a>.');
      }
    }
    function open() {
      hideContact();
      if (contactWrapper) contactWrapper.style.display = 'none';
      panel.hidden = false;
      chatBtn.setAttribute('aria-expanded', 'true');
      if (!body.children.length) {
        addMessage('Bonjour 👋 Je suis l’assistant UFA Campus. Je peux vous orienter sur les formations, le financement, la certification Qualiopi, le planning ou les contacts. Choisissez une question ou écrivez la vôtre.', 'bot');
      }
      input.focus();
    }
    function close() {
      panel.hidden = true;
      chatBtn.setAttribute('aria-expanded', 'false');
      if (contactWrapper) contactWrapper.style.removeProperty('display');
      chatBtn.focus();
    }

    chatBtn.setAttribute('aria-controls', 'ufa-chat');
    chatBtn.setAttribute('aria-expanded', 'false');
    chatBtn.addEventListener('click', e => {
      e.stopPropagation();
      if (panel.hidden) open(); else close();
    });
    panel.querySelector('.ufa-chat-close').addEventListener('click', close);
    form.addEventListener('submit', e => { e.preventDefault(); ask(input.value); });
    quick.addEventListener('click', e => {
      const button = e.target.closest('button[data-q]');
      if (button) ask(button.dataset.q);
    });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && !panel.hidden) close(); });
    document.addEventListener('click', e => {
      if (!panel.hidden && !panel.contains(e.target) && !chatBtn.contains(e.target)) close();
    });
  }

  function panelContent(cfg) {
    const inner = document.createElement('div');
    inner.style.cssText = 'display:flex;gap:24px;';
    if (cfg.cols) {
      cfg.cols.forEach(col => {
        const c = document.createElement('div');
        c.style.cssText = 'min-width:200px;';
        const t = document.createElement('div');
        t.className = 'nav-panel-title';
        t.textContent = col.label;
        c.appendChild(t);
        col.links.forEach(([label, href]) => {
          const a = document.createElement('a');
          a.href = href;
          a.textContent = label;
          a.style.cssText = 'display:block;padding:7px 10px;border-radius:6px;font-size:13px;color:#1a1a2e;';
          c.appendChild(a);
        });
        inner.appendChild(c);
      });
    } else {
      const c = document.createElement('div');
      c.style.cssText = 'min-width:220px;';
      (cfg.links || []).forEach(([label, href]) => {
        const a = document.createElement('a');
        a.href = href;
        a.textContent = label;
        a.style.cssText = 'display:block;padding:8px 10px;border-radius:6px;font-size:13px;color:#1a1a2e;';
        c.appendChild(a);
      });
      inner.appendChild(c);
    }
    return inner;
  }

  ready(function () {
    /* Contenu révélé (React retiré) */
    document.querySelectorAll('[data-reveal]').forEach(el => {
      el.style.opacity = '1';
      el.style.transform = 'none';
    });

    /* Fermeture du bandeau d'annonce */
    document.querySelectorAll('button[aria-label*="Fermer le bandeau"]').forEach(btn => {
      btn.classList.add('announce-close');
      btn.addEventListener('click', () => {
        const bar = btn.parentElement;
        if (bar) bar.style.display = 'none';
      });
    });

    /* Menus déroulants du header */
    let active = null;
    let closeTimer = null;

    function cancelClose() {
      if (closeTimer !== null) {
        clearTimeout(closeTimer);
        closeTimer = null;
      }
    }
    function closeMenu() {
      cancelClose();
      if (!active) return;
      active.panel.remove();
      active.btn.setAttribute('aria-expanded', 'false');
      active = null;
    }
    function scheduleClose() {
      cancelClose();
      // Laisse le temps à la souris de traverser l'espace entre le bouton et le panneau.
      closeTimer = setTimeout(closeMenu, 260);
    }
    function openMenu(btn, id) {
      cancelClose();
      if (active && active.btn === btn) return;
      closeMenu();
      const cfg = MENUS[id];
      const panel = styledPanel(id);
      panel.style.width = (cfg.width || 260) + 'px';
      panel.appendChild(panelContent(cfg));
      btn.parentElement.appendChild(panel);
      btn.setAttribute('aria-expanded', 'true');
      active = { btn, panel };
      panel.addEventListener('mouseenter', cancelClose);
      panel.addEventListener('mouseleave', scheduleClose);
      panel.addEventListener('focusin', cancelClose);
      panel.addEventListener('focusout', scheduleClose);
    }

    document.querySelectorAll('button[aria-controls]').forEach(btn => {
      const id = btn.getAttribute('aria-controls');
      if (id === 'mobile-menu') {
        const header = btn.closest('header');
        if (!header || document.getElementById(id)) return;
        const panel = document.createElement('div');
        panel.id = id;
        panel.style.cssText = 'display:none;position:absolute;top:100%;left:0;right:0;background:#fff;border-bottom:1px solid #dde4f0;box-shadow:0 16px 30px rgba(13,27,62,.12);padding:16px 24px 24px;z-index:80;';
        MOBILE_LINKS.forEach(([label, href]) => {
          const a = document.createElement('a');
          a.href = href;
          a.textContent = label;
          a.style.cssText = 'display:block;padding:12px 6px;border-bottom:1px solid #eef2f8;font-size:15px;font-weight:600;color:#0d1b3e;';
          a.addEventListener('click', () => { panel.style.display = 'none'; btn.setAttribute('aria-expanded', 'false'); });
          panel.appendChild(a);
        });
        header.style.position = 'sticky';
        header.appendChild(panel);
        btn.addEventListener('click', e => {
          e.stopPropagation();
          const show = panel.style.display === 'none';
          panel.style.display = show ? 'block' : 'none';
          btn.setAttribute('aria-expanded', String(show));
        });
        return;
      }
      if (!MENUS[id]) return;
      btn.addEventListener('click', e => {
        e.stopPropagation();
        if (active && active.btn === btn) closeMenu();
        else openMenu(btn, id);
      });
      const host = btn.parentElement;
      host.addEventListener('mouseenter', () => { cancelClose(); openMenu(btn, id); });
      host.addEventListener('mouseleave', scheduleClose);
      host.addEventListener('focusin', () => { cancelClose(); openMenu(btn, id); });
      host.addEventListener('focusout', scheduleClose);
    });

    document.addEventListener('click', e => {
      if (active && !active.panel.contains(e.target) && !active.btn.contains(e.target)) closeMenu();
    });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMenu(); });

    /* Accordéon FAQ */
    document.querySelectorAll('button[aria-expanded][aria-controls]').forEach(btn => {
      const id = btn.getAttribute('aria-controls');
      if (MENUS[id] || id === 'mobile-menu' || id === 'floating-contact-actions') return;
      const panel = document.getElementById(id);
      if (!panel) return;
      btn.addEventListener('click', () => {
        const isOpen = btn.getAttribute('aria-expanded') === 'true';
        btn.setAttribute('aria-expanded', String(!isOpen));
        panel.classList.toggle('hidden', isOpen);
        panel.hidden = isOpen;
        panel.style.display = isOpen ? 'none' : '';
        const chevron = btn.querySelector('svg');
        if (chevron) chevron.classList.toggle('rotate-180', !isOpen);
      });
    });

    /* Diaporama du hero */
    const pauseBtn = document.querySelector('button[aria-label="Mettre le diaporama en pause"]');
    if (pauseBtn) {
      const controls = pauseBtn.parentElement;
      const dots = Array.from(controls.querySelectorAll('button[aria-label^="Afficher le visuel"]'));
      const stage = controls.parentElement;
      const slides = Array.from(stage.querySelectorAll('img'));
      let index = Math.max(0, dots.findIndex(d => d.getAttribute('aria-current') === 'true'));
      let timer = null;

      function show(i) {
        index = (i + slides.length) % slides.length;
        slides.forEach((s, k) => { s.style.opacity = k === index ? '1' : '0'; });
        dots.forEach((d, k) => {
          d.setAttribute('aria-current', k === index ? 'true' : 'false');
          const span = d.querySelector('span');
          if (span) span.className = 'h-2 rounded-full transition-all ' +
            (k === index ? 'w-5 bg-white' : 'w-2 bg-white/45 group-hover:bg-white/75');
        });
      }
      function start() {
        stop();
        timer = setInterval(() => show(index + 1), 5000);
      }
      function stop() { if (timer) { clearInterval(timer); timer = null; } }

      dots.forEach((d, k) => d.addEventListener('click', () => { show(k); start(); }));
      pauseBtn.addEventListener('click', () => {
        if (timer) {
          stop();
          pauseBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="m5 3 14 9-14 9V3Z"/></svg>';
          pauseBtn.setAttribute('aria-label', 'Reprendre le diaporama');
        } else {
          start();
          pauseBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><rect x="14" y="4" width="4" height="16" rx="1"/><rect x="6" y="4" width="4" height="16" rx="1"/></svg>';
          pauseBtn.setAttribute('aria-label', 'Mettre le diaporama en pause');
        }
      });
      if (slides.length > 1) start();
    }

    /* Carrousels (planning, témoignages) */
    document.querySelectorAll('button[aria-label]').forEach(btn => {
      const label = (btn.getAttribute('aria-label') || '').toLowerCase();
      if (!/précédent|precedent|suivant|next|previous/.test(label)) return;
      const section = btn.closest('section');
      const scroller = section && (section.querySelector('.overflow-x-auto') || section.querySelector('[class*="overflow-x-auto"]'));
      if (!scroller) return;
      btn.addEventListener('click', () => {
        const card = scroller.querySelector(':scope > *');
        const step = card ? card.getBoundingClientRect().width + 20 : 360;
        scroller.scrollBy({ left: /suivant|next/.test(label) ? step : -step, behavior: 'smooth' });
      });
    });

    /* Widget de contact flottant */
    const actions = document.getElementById('floating-contact-actions');
    const contactBtn = document.querySelector('button[aria-controls="floating-contact-actions"]');
    const chatBtn = Array.from(document.querySelectorAll('button'))
      .find(b => b.textContent.trim() === 'Poser une question');

    let contactWrapper = null;
    let hideContact = () => {};

    if (actions && contactBtn) {
      const wrapper = contactBtn.parentElement;
      contactWrapper = wrapper;
      let widgetTimer = null;

      function cancelWidgetClose() {
        if (widgetTimer !== null) {
          clearTimeout(widgetTimer);
          widgetTimer = null;
        }
      }
      function showActions() {
        cancelWidgetClose();
        actions.classList.remove('hidden', 'invisible', 'opacity-0', 'translate-y-2');
        // Le conteneur parent est en pointer-events-none : on réactive le bloc ici.
        actions.style.pointerEvents = 'auto';
        contactBtn.setAttribute('aria-expanded', 'true');
        // Le bouton bleu est au-dessus dans le DOM : on l'efface pendant l'ouverture.
        if (chatBtn) chatBtn.style.display = 'none';
      }
      function hideActions() {
        cancelWidgetClose();
        actions.classList.add('invisible', 'opacity-0', 'translate-y-2');
        actions.style.pointerEvents = 'none';
        contactBtn.setAttribute('aria-expanded', 'false');
        if (chatBtn) chatBtn.style.removeProperty('display');
      }
      function scheduleWidgetClose() {
        cancelWidgetClose();
        widgetTimer = setTimeout(hideActions, 260);
      }

      wrapper.addEventListener('mouseenter', showActions);
      wrapper.addEventListener('mouseleave', scheduleWidgetClose);
      actions.addEventListener('mouseenter', cancelWidgetClose);
      actions.addEventListener('mouseleave', scheduleWidgetClose);
      actions.addEventListener('focusin', cancelWidgetClose);
      actions.addEventListener('focusout', scheduleWidgetClose);

      contactBtn.addEventListener('click', e => {
        e.stopPropagation();
        if (contactBtn.getAttribute('aria-expanded') === 'true') hideActions();
        else showActions();
      });

      document.addEventListener('click', e => {
        if (contactBtn.getAttribute('aria-expanded') === 'true' &&
            !wrapper.contains(e.target) && !(chatBtn && chatBtn.contains(e.target))) {
          hideActions();
        }
      });
      document.addEventListener('keydown', e => { if (e.key === 'Escape') hideActions(); });

      hideContact = hideActions;
    }

    // Le bouton « Poser une question » ouvre l’assistant conversationnel.
    initChatbot(chatBtn, contactWrapper, hideContact);

    /* Gestion des cookies */
    document.querySelectorAll('button').forEach(btn => {
      if (btn.textContent.trim() !== 'Gérer les cookies') return;
      btn.addEventListener('click', () => {
        let bar = document.getElementById('cookie-bar');
        if (bar) { bar.remove(); return; }
        bar = document.createElement('div');
        bar.id = 'cookie-bar';
        bar.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:120;background:#fff;border-top:1px solid #dde4f0;box-shadow:0 -8px 30px rgba(13,27,62,.12);padding:16px 24px;display:flex;flex-wrap:wrap;gap:16px;align-items:center;justify-content:space-between;';
        bar.innerHTML = '<p style="font-size:13px;color:#5a6785;margin:0;max-width:760px;">Nous utilisons des cookies pour améliorer votre expérience et mesurer l’audience de notre site. En continuant, vous acceptez notre politique de confidentialité.</p><div style="display:flex;gap:10px;"><button data-choice="accepted" style="background:#1a5fd4;color:#fff;border:0;border-radius:8px;padding:10px 18px;font-weight:600;">Accepter</button><button data-choice="declined" style="background:#fff;color:#0d1b3e;border:1px solid #dde4f0;border-radius:8px;padding:10px 18px;font-weight:600;">Refuser</button></div>';
        bar.querySelectorAll('button[data-choice]').forEach(b => b.addEventListener('click', () => {
          try { localStorage.setItem('cap-cookie-choice', b.dataset.choice); } catch (err) { /* ignore */ }
          bar.remove();
        }));
        document.body.appendChild(bar);
      });
    });
    /* Gestion des formulaires de contact & inscription (FormSubmit) */
    if (window.location.search.indexOf('success=true') !== -1) {
      const fb = document.getElementById('form-feedback') || document.getElementById('contact-feedback');
      if (fb) {
        fb.classList.remove('hidden');
        fb.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }

    document.querySelectorAll('form[action*="formsubmit.co"]').forEach(form => {
      form.addEventListener('submit', function () {
        const btn = form.querySelector('button[type="submit"]');
        if (btn) {
          btn.innerHTML = 'Envoi en cours…';
        }
      });
    });
  });
})();
