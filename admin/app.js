(function () {
  'use strict';

  const state = { pages: [], selected: null, filter: 'all', query: '' };
  const $ = id => document.getElementById(id);

  async function api(url, options) {
    const response = await fetch(url, Object.assign({ headers: { 'Content-Type': 'application/json' } }, options));
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.ok === false) throw new Error(data.error || 'Erreur de communication');
    return data;
  }

  function toast(message, isError) {
    const el = $('toast');
    el.textContent = message;
    el.classList.toggle('error', Boolean(isError));
    el.hidden = false;
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => { el.hidden = true; }, 6000);
  }

  function visiblePages() {
    const q = state.query.toLocaleLowerCase('fr');
    return state.pages.filter(page => {
      if (state.filter === 'modified' && !page.modified) return false;
      if (state.filter !== 'all' && state.filter !== 'modified' && page.category !== state.filter) return false;
      if (q && !(page.name + ' ' + page.path).toLocaleLowerCase('fr').includes(q)) return false;
      return true;
    });
  }

  function renderList() {
    const list = $('list');
    const pages = visiblePages();
    list.innerHTML = '';
    if (!pages.length) {
      const p = document.createElement('p');
      p.className = 'empty';
      p.style.margin = '30px auto';
      p.textContent = 'Aucune formation ne correspond à cette recherche.';
      list.appendChild(p);
      return;
    }
    pages.forEach(page => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'item' + (state.selected === page.path ? ' active' : '');
      const title = document.createElement('strong');
      title.textContent = (page.modified ? '● ' : '') + page.name;
      const meta = document.createElement('small');
      meta.textContent = page.category + ' · ' + page.path;
      btn.appendChild(title);
      btn.appendChild(meta);
      btn.addEventListener('click', () => selectPage(page.path));
      list.appendChild(btn);
    });
  }

  function fieldRows(key) {
    if (key === 'sessions') return 5;
    if (key.indexOf('description') === 0) return 4;
    return 2;
  }

  function renderFields(page) {
    const container = $('fields');
    container.innerHTML = '';
    Object.keys(page.fields).forEach(key => {
      const field = page.fields[key];
      const wrap = document.createElement('div');
      wrap.className = 'field';

      const label = document.createElement('label');
      label.textContent = field.label;
      label.htmlFor = 'field-' + key;
      wrap.appendChild(label);

      const area = document.createElement('textarea');
      area.id = 'field-' + key;
      area.dataset.key = key;
      area.rows = fieldRows(key);
      area.value = field.display || '';
      if (!field.present) {
        area.disabled = true;
        area.placeholder = 'Ce champ n’existe pas sur cette fiche.';
      }
      wrap.appendChild(area);

      if (field.count > 1) {
        const hint = document.createElement('small');
        hint.textContent = 'Appliqué à ' + field.count + ' emplacements de la page.';
        wrap.appendChild(hint);
      }
      if (key === 'sessions' && field.present) {
        const hint = document.createElement('small');
        hint.textContent = field.count + ' session(s) actuellement affichée(s). Une session par ligne.';
        wrap.appendChild(hint);
      }
      container.appendChild(wrap);
    });
  }

  function selectPage(path) {
    const page = state.pages.find(p => p.path === path);
    if (!page) return;
    state.selected = path;
    $('empty').hidden = true;
    $('formWrap').hidden = false;
    $('formCategory').textContent = page.category;
    $('formTitle').textContent = page.name;
    $('formPath').textContent = '/' + path;
    $('formBadge').hidden = !page.modified;
    renderFields(page);
    renderList();
  }

  async function reload() {
    const data = await api('api/overview');
    state.pages = data.pages;
    $('counter').textContent = data.pages.length + ' fiches · ' + data.modified + ' modifiée(s)';
    renderList();
    if (state.selected) selectPage(state.selected);
  }

  async function init() {
    $('search').addEventListener('input', e => { state.query = e.target.value; renderList(); });
    document.querySelectorAll('.chip').forEach(chip => {
      chip.addEventListener('click', () => {
        document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        state.filter = chip.dataset.filter;
        renderList();
      });
    });

    $('form').addEventListener('submit', async e => {
      e.preventDefault();
      if (!state.selected) return;
      const fields = {};
      document.querySelectorAll('#fields textarea[data-key]:not(:disabled)').forEach(area => {
        fields[area.dataset.key] = area.value;
      });
      try {
        await api('api/save', {
          method: 'POST',
          body: JSON.stringify({ path: state.selected, fields: fields })
        });
        await reload();
        toast('Modifications enregistrées. Cliquez sur « Appliquer au site » pour les publier.');
      } catch (err) {
        toast(err.message, true);
      }
    });

    $('reset').addEventListener('click', async () => {
      if (!state.selected) return;
      if (!window.confirm('Rétablir les valeurs d’origine de cette fiche ?')) return;
      try {
        await api('api/reset', { method: 'POST', body: JSON.stringify({ path: state.selected }) });
        await reload();
        toast('Fiche rétablie.');
      } catch (err) {
        toast(err.message, true);
      }
    });

    $('apply').addEventListener('click', async () => {
      const button = $('apply');
      button.disabled = true;
      button.textContent = 'Application…';
      try {
        const data = await api('api/apply', { method: 'POST', body: '{}' });
        const n = data.changed.length;
        toast(n ? (n + ' fiche(s) mise(s) à jour sur le site.') : 'Site déjà à jour — aucune modification à appliquer.');
        await reload();
      } catch (err) {
        toast(err.message, true);
      } finally {
        button.disabled = false;
        button.textContent = 'Appliquer au site';
      }
    });

    try {
      await reload();
    } catch (err) {
      toast('Impossible de charger les formations : ' + err.message, true);
    }
  }

  init();
})();
