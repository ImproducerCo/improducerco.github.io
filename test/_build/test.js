// Прототип /test/: состояния экрана по адресу (#s=empty) и отметки описи.
// Ничего никуда не отправляется: форм нет, отметки живут в localStorage этого браузера.
(function () {
  var LABEL = {full: 'Заполнено', empty: 'Пусто', loading: 'Загрузка', error: 'Ошибка',
    denied: 'Нет доступа', long: 'Длинный текст', booked: 'Записан на разговор', saved: 'Сохранено',
    confirm: 'Подтверждение', near: 'Близко к сроку'};

  function current() {
    var m = location.hash.match(/s=([a-z]+)/);
    return m ? m[1] : 'full';
  }

  function show(s) {
    var blocks = document.querySelectorAll('[data-st]');
    if (!blocks.length) return;
    var known = Array.prototype.some.call(blocks, function (el) {
      return el.getAttribute('data-st').split(' ').indexOf(s) >= 0;
    });
    if (!known) s = 'full';
    blocks.forEach(function (el) {
      el.hidden = el.getAttribute('data-st').split(' ').indexOf(s) < 0;
    });
    document.querySelectorAll('.proto a[data-s]').forEach(function (a) {
      if (a.dataset.s === s) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
    var b = document.querySelector('.proto summary b');
    if (b) b.textContent = LABEL[s] || s;
    var p = document.querySelector('details.proto');
    if (p) p.open = false;
  }

  window.addEventListener('hashchange', function () { show(current()); });
  show(current());

  // Кнопки «ввод → дальше» в полях: Enter в поле ведёт туда же, куда главная кнопка рядом.
  document.querySelectorAll('[data-next]').forEach(function (el) {
    el.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); location.href = el.dataset.next; }
    });
  });

  // Закрыть открытые меню кликом мимо.
  document.addEventListener('click', function (e) {
    document.querySelectorAll('details[open].acct, details[open].site-menu, details[open].side-menu, details[open].proto')
      .forEach(function (d) { if (!d.contains(e.target)) d.open = false; });
  });

  // Отметки описи: ✓ · ✕ · ⊘ и комментарий на строку.
  var KEY = 'improducer-test-opis-v1';
  var rows = document.querySelectorAll('.opis .row[data-id]');
  if (!rows.length) return;
  function load() { try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { return {}; } }
  function save(s) { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) { /* приватное окно: отметки только на экране */ } }
  var state = load();
  var SIGN = {ok: '✓', no: '✕', wrong: '⊘'};

  function paint(row) {
    var st = state[row.dataset.id] || {};
    row.classList.remove('m-ok', 'm-no', 'm-wrong');
    if (st.mark) row.classList.add('m-' + st.mark);
    row.querySelectorAll('.mbtn').forEach(function (b) {
      var on = st.mark === b.dataset.mark;
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }

  rows.forEach(function (row) {
    var id = row.dataset.id;
    paint(row);
    row.querySelectorAll('.mbtn').forEach(function (b) {
      b.addEventListener('click', function () {
        var cur = (state[id] || {}).mark;
        state[id] = Object.assign({}, state[id], {mark: cur === b.dataset.mark ? null : b.dataset.mark});
        save(state); paint(row);
      });
    });
    var ta = row.querySelector('.cmt');
    if (ta) {
      ta.value = (state[id] || {}).note || '';
      ta.addEventListener('input', function () {
        state[id] = Object.assign({}, state[id], {note: ta.value}); save(state);
      });
    }
  });

  var copy = document.querySelector('[data-act="copy-marks"]');
  var out = document.querySelector('[data-copy-out]');
  if (copy) copy.addEventListener('click', function () {
    var lines = [];
    rows.forEach(function (row) {
      var st = state[row.dataset.id] || {};
      if (!st.mark && !st.note) return;
      lines.push(row.dataset.id + ' ' + (SIGN[st.mark] || '·') + (st.note ? ' — ' + st.note : ''));
    });
    var text = lines.length ? lines.join('\n') : 'Отметок пока нет.';
    if (out) { out.hidden = false; out.textContent = text; }
    if (navigator.clipboard) navigator.clipboard.writeText(text).then(function () {
      copy.textContent = 'Скопировано — вставьте в чат';
    }, function () { copy.textContent = 'Не скопировалось — выделите текст ниже'; });
  });
})();
