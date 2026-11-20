/* Assistant d’inscription UFA Campus : étapes, sessions, pièces jointes et vérification. */
(function () {
  'use strict';

  var form = document.getElementById('inscription-form');
  if (!form) return;

  var steps = Array.prototype.slice.call(form.querySelectorAll('.ufa-step'));
  var indicators = Array.prototype.slice.call(form.querySelectorAll('[data-step-indicator]'));
  var banner = document.getElementById('ufa-step-error');
  var formationSelect = document.getElementById('insc-formation');
  var sessionContainer = document.getElementById('insc-sessions');
  var sessionHint = document.getElementById('insc-session-hint');
  var sessionDetails = document.getElementById('insc-session-details');
  var modaliteSelect = document.getElementById('insc-modalite');
  var fileInputs = Array.prototype.slice.call(form.querySelectorAll('input[type="file"]'));
  var totalInfo = document.getElementById('ufa-files-total');
  var recap = document.getElementById('insc-recap');
  var amenagement = document.getElementById('insc-amenagement');
  var amenagementDetails = document.getElementById('insc-amenagement-details');
  var submitButton = document.getElementById('btn-submit-inscription');
  var MAX_FILES = 10 * 1024 * 1024;
  var current = 1;

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' o';
    if (bytes < 1024 * 1024) return Math.round(bytes / 1024) + ' Ko';
    return (Math.round(bytes / (1024 * 1024) * 10) / 10) + ' Mo';
  }

  function showBanner(message) {
    if (!banner) return;
    if (!message) {
      banner.textContent = '';
      banner.classList.add('hidden');
      return;
    }
    banner.textContent = message;
    banner.classList.remove('hidden');
  }

  function errorFor(field) {
    return document.getElementById('err-' + field.name);
  }

  function setError(field, message) {
    var target = errorFor(field);
    if (target) {
      target.textContent = message;
      target.classList.remove('hidden');
    }
    field.setAttribute('aria-invalid', 'true');
  }

  function clearError(field) {
    var target = errorFor(field);
    if (target) {
      target.textContent = '';
      target.classList.add('hidden');
    }
    field.removeAttribute('aria-invalid');
  }

  function validateField(field) {
    clearError(field);
    var value = (field.value || '').trim();

    if (field.type === 'checkbox') {
      if (field.checked) return true;
      setError(field, 'Veuillez cocher cette case pour continuer.');
      return false;
    }
    if (!value) {
      setError(field, 'Ce champ est obligatoire.');
      return false;
    }
    if (field.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
      setError(field, 'Saisissez une adresse e-mail valide.');
      return false;
    }
    if (field.type === 'tel' && value.replace(/\D/g, '').length < 10) {
      setError(field, 'Saisissez un numéro de téléphone valide.');
      return false;
    }
    return true;
  }

  function validateStep(number, focus) {
    var section = form.querySelector('.ufa-step[data-step="' + number + '"]');
    if (!section) return true;
    var fields = Array.prototype.slice.call(section.querySelectorAll('[required]'));
    var invalid = null;

    fields.forEach(function (field) {
      if (!validateField(field) && !invalid) invalid = field;
    });

    if (number === 4 && !validateDocuments()) invalid = invalid || fileInputs[0];

    if (invalid && focus) {
      showBanner('Veuillez corriger les champs signalés avant de continuer.');
      invalid.focus();
    }
    return !invalid;
  }

  function showStep(number) {
    current = number;
    steps.forEach(function (section) {
      section.hidden = Number(section.dataset.step) !== number;
    });
    indicators.forEach(function (item) {
      var index = Number(item.dataset.stepIndicator);
      item.toggleAttribute('aria-current', index === number);
      if (index === number) item.setAttribute('aria-current', 'step');
      item.classList.toggle('is-current', index === number);
      item.classList.toggle('is-done', index < number);
    });
    showBanner('');
    if (number === 5) buildRecap();
    var heading = form.querySelector('.ufa-step[data-step="' + number + '"] h3');
    if (heading) heading.focus();
    if (form.scrollIntoView) form.scrollIntoView({ block: 'start' });
  }

  function renderSessions() {
    if (!sessionContainer) return;
    sessionContainer.textContent = '';
    var formation = formationSelect ? formationSelect.value : '';
    if (sessionDetails) sessionDetails.value = '';

    if (!formation) {
      sessionHint.textContent = 'Sélectionnez une formation pour afficher ses sessions.';
      return;
    }

    var list = (window.UFA_SESSIONS || []).filter(function (item) {
      return item.formation === formation;
    });

    if (list.length) {
      sessionHint.textContent = list.length + ' session(s) planifiée(s). Cliquez sur celle qui vous convient.';
    } else {
      sessionHint.textContent = 'Aucune session planifiée pour le moment : notre équipe vous recontactera pour convenir des dates.';
    }

    list.forEach(function (item, index) {
      var value = 's' + index;
      var details = [item.date, item.mois, item.nom, item.lieu, item.modalite, item.places, item.horaires]
        .filter(Boolean).join(' · ');
      var label = document.createElement('label');
      label.className = 'ufa-session-option';
      var radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = 'session';
      radio.value = value;
      radio.setAttribute('data-details', details);
      radio.setAttribute('data-modalite', item.modalite || '');
      var body = document.createElement('span');
      body.className = 'ufa-session-body';
      var date = document.createElement('span');
      date.className = 'ufa-session-date';
      date.textContent = item.date + (item.mois ? ' · ' + item.mois : '');
      var title = document.createElement('span');
      title.className = 'ufa-session-name';
      title.textContent = item.nom + (item.modalite ? ' · ' + item.modalite : '');
      var meta = document.createElement('span');
      meta.className = 'ufa-session-meta';
      meta.textContent = [item.lieu, item.places].filter(Boolean).join(' · ');
      body.appendChild(date);
      body.appendChild(title);
      if (meta.textContent) body.appendChild(meta);
      if (item.horaires) {
        var schedule = document.createElement('span');
        schedule.className = 'ufa-session-meta';
        schedule.textContent = item.horaires;
        body.appendChild(schedule);
      }
      if (item.fiche) {
        var link = document.createElement('a');
        link.className = 'ufa-session-link';
        link.href = item.fiche;
        link.textContent = 'Voir la fiche de formation';
        body.appendChild(link);
      }
      label.appendChild(radio);
      label.appendChild(body);
      sessionContainer.appendChild(label);
    });

    var fallback = document.createElement('label');
    fallback.className = 'ufa-session-option ufa-session-fallback';
    var radioFallback = document.createElement('input');
    radioFallback.type = 'radio';
    radioFallback.name = 'session';
    radioFallback.value = 'a-convenir';
    radioFallback.setAttribute('data-details', 'Dates à convenir avec UFA Campus');
    var text = document.createElement('span');
    text.className = 'ufa-session-body';
    text.textContent = 'Dates à convenir / être rappelé(e)';
    fallback.appendChild(radioFallback);
    fallback.appendChild(text);
    sessionContainer.appendChild(fallback);
  }

  function validateDocuments() {
    if (!fileInputs.length) return true;
    var total = 0;
    var error = document.getElementById('err-documents');
    var allowed = /\.(pdf|jpe?g|png|docx?)$/i;
    var tooLarge = false;
    var badType = false;

    fileInputs.forEach(function (input) {
      Array.prototype.forEach.call(input.files || [], function (file) {
        total += file.size;
        if (!allowed.test(file.name)) badType = true;
      });
    });

    if (badType || total > MAX_FILES) {
      if (error) {
        error.textContent = badType
          ? 'Formats acceptés : PDF, JPG, PNG, DOC ou DOCX.'
          : 'La taille totale des fichiers ne doit pas dépasser 10 Mo.';
        error.classList.remove('hidden');
      }
      fileInputs.forEach(function (input) { input.value = ''; });
      updateFiles();
      return false;
    }

    if (error) {
      error.textContent = '';
      error.classList.add('hidden');
    }
    return true;
  }

  function updateFiles() {
    if (!totalInfo) return;
    var total = 0;
    var count = 0;

    fileInputs.forEach(function (input) {
      var files = Array.prototype.slice.call(input.files || []);
      var meta = document.getElementById(input.id + '-meta');
      var row = input.closest('.ufa-file-row');
      var clear = row ? row.querySelector('.ufa-file-clear') : null;
      count += files.length;
      files.forEach(function (file) { total += file.size; });

      if (meta) {
        if (!files.length) {
          meta.textContent = input.getAttribute('data-default') || input.dataset.default || '';
        } else if (files.length === 1) {
          meta.textContent = files[0].name + ' · ' + formatSize(files[0].size);
        } else {
          meta.textContent = files.length + ' fichiers sélectionnés · ' + formatSize(
            files.reduce(function (sum, file) { return sum + file.size; }, 0)
          );
        }
      }
      if (clear) clear.hidden = files.length === 0;
    });

    totalInfo.textContent = count
      ? count + ' fichier(s) sélectionné(s) · total ' + formatSize(total) + ' / 10 Mo'
      : 'Aucun fichier sélectionné.';
  }

  function buildRecap() {
    if (!recap) return;
    recap.textContent = '';

    function add(label, value) {
      if (!value) return;
      var row = document.createElement('div');
      row.className = 'ufa-recap-row';
      var dt = document.createElement('dt');
      dt.textContent = label;
      var dd = document.createElement('dd');
      dd.textContent = value;
      row.appendChild(dt);
      row.appendChild(dd);
      recap.appendChild(row);
    }

    add('Formation', formationSelect ? formationSelect.value : '');
    var chosen = form.querySelector('input[name="session"]:checked');
    if (chosen) add('Session', chosen.getAttribute('data-details') || 'Dates à convenir');
    if (modaliteSelect && chosen && chosen.value === 'a-convenir') {
      if (modaliteSelect.value) add('Format souhaité', modaliteSelect.value);
    } else if (modaliteSelect && modaliteSelect.value && chosen && chosen.dataset.modalite) {
      add('Format', chosen.dataset.modalite);
    }
    add('Civilité', val('insc-genre'));
    var name = [val('insc-prenom'), val('insc-nom')].filter(Boolean).join(' ');
    add('Nom', name);
    add('E-mail', val('insc-email'));
    add('Téléphone', val('insc-tel'));
    add('Ville', val('insc-ville'));
    add('Financement', val('insc-financement'));
    add('Situation', val('insc-situation'));
    add('Employeur / OPCO', val('insc-employeur'));
    add('Message', val('insc-message'));
    add('Aménagements', val('insc-amenagement-texte'));
    if (amenagement && amenagement.checked && !val('insc-amenagement-texte')) {
      add('Aménagements', 'Échange souhaité avec le référent handicap');
    }
    var count = fileInputs.reduce(function (sum, input) {
      return sum + (input.files ? input.files.length : 0);
    }, 0);
    add('Documents joints', count ? count + ' fichier(s)' : 'Aucun document');
  }

  function val(id) {
    var el = document.getElementById(id);
    return el ? (el.value || '').trim() : '';
  }

  steps.forEach(function (section) { section.hidden = Number(section.dataset.step) !== 1; });
  indicators.forEach(function (item) {
    var isFirst = item.dataset.stepIndicator === '1';
    item.classList.toggle('is-current', isFirst);
    if (isFirst) item.setAttribute('aria-current', 'step');
  });

  fileInputs.forEach(function (input) {
    var meta = document.getElementById(input.id + '-meta');
    if (meta) input.setAttribute('data-default', meta.textContent);
  });
  renderSessions();
  updateFiles();

  if (formationSelect) formationSelect.addEventListener('change', renderSessions);

  form.addEventListener('change', function (event) {
    var target = event.target;
    if (target.name === 'session') {
      if (sessionDetails) {
        sessionDetails.value = target.getAttribute('data-details') || target.value;
      }
      if (modaliteSelect && target.dataset.modalite) {
        var wanted = target.dataset.modalite;
        Array.prototype.forEach.call(modaliteSelect.options, function (option) {
          if (option.value === wanted) modaliteSelect.value = wanted;
        });
      }
      clearError(target);
    }
    if (target.required) clearError(target);
    if (target.type === 'file') {
      if (event.target.files && event.target.files.length) {
        var total = 0;
        fileInputs.forEach(function (input) {
          Array.prototype.forEach.call(input.files || [], function (file) { total += file.size; });
        });
        if (total > MAX_FILES) {
          target.value = '';
          var error = document.getElementById('err-documents');
          if (error) {
            error.textContent = 'La taille totale des fichiers ne doit pas dépasser 10 Mo.';
            error.classList.remove('hidden');
          }
        } else {
          var err = document.getElementById('err-documents');
          if (err) err.classList.add('hidden');
        }
      }
      updateFiles();
    }
  });

  form.addEventListener('click', function (event) {
    var next = event.target.closest('.ufa-next');
    var back = event.target.closest('.ufa-back');
    var clear = event.target.closest('.ufa-file-clear');

    if (clear) {
      var input = document.getElementById(clear.dataset.clear);
      if (input) {
        input.value = '';
        updateFiles();
      }
      return;
    }
    if (back) {
      showStep(Number(back.dataset.back));
      return;
    }
    if (next) {
      var targetStep = Number(next.dataset.next);
      if (validateStep(current, true)) {
        showStep(targetStep);
      }
    }
  });

  if (amenagement && amenagementDetails) {
    amenagement.addEventListener('change', function () {
      amenagementDetails.hidden = !amenagement.checked;
    });
  }

  fileInputs.forEach(function (input) {
    var row = input.closest('.ufa-file-row');
    if (row) {
      var clear = document.createElement('button');
      clear.type = 'button';
      clear.className = 'ufa-file-clear';
      clear.dataset.clear = input.id;
      clear.textContent = 'Retirer';
      clear.hidden = true;
      row.appendChild(clear);
    }
  });
  updateFiles();

  form.addEventListener('submit', function (event) {
    var firstInvalid = 0;
    for (var number = 1; number <= steps.length; number += 1) {
      if (!validateStep(number, false)) {
        firstInvalid = number;
        break;
      }
    }
    if (firstInvalid) {
      event.preventDefault();
      showStep(firstInvalid);
      showBanner('Veuillez corriger les champs signalés avant d’envoyer votre demande.');
      var invalid = form.querySelector('[aria-invalid="true"]');
      if (invalid) invalid.focus();
      return;
    }
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = 'Envoi en cours…';
    }
  });
})();
