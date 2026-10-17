// Прототип /test/: состояния экрана по адресу (#s=empty) и отметки описи.
// Ничего никуда не отправляется: форм нет, отметки живут в localStorage этого браузера.
(function () {
  var LABEL = {full: 'Заполнено', empty: 'Пусто', loading: 'Загрузка', error: 'Ошибка', denied: 'Нет доступа', long: 'Длинный текст', saved: 'Сохранено', confirm: 'Подтверждение', sent: 'Письмо отправлено', code: 'Ввод кода', badcode: 'Неверный код', limit: 'Лимит исчерпан', streaming: 'Ответ идёт', paid: 'Оплачено', tool: 'С инструментом', month: 'Помесячно', canceled: 'Отменён', close: 'Близко к лимиту', notfound: 'Ничего не найдено', select: 'Выбор нескольких', kbfull: 'Знания почти заполнены', add: 'Добавить свой', exported: 'Экспорт запрошен', signout: 'Выйти везде', decided: 'Решение принято'};

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

  // Имя из входа Google: сервер входа приводит сюда с #n=<имя> (connect app_signin.ts). Имя держится в этой
  // вкладке (sessionStorage), из адреса стирается. Без входа — выдуманный «Тест».
  var n = location.hash.match(/^#n=([^&]*)/);
  function dec(v) { try { return decodeURIComponent(v).slice(0, 60); } catch (e) { return ''; } }
  if (n) {
    try { if (dec(n[1])) sessionStorage.setItem('improducer-test-name', dec(n[1])); } catch (e) { /* без хранилища — имя только на этой странице */ }
    history.replaceState(null, '', location.pathname + location.search);
  }
  var name = '';
  try { name = sessionStorage.getItem('improducer-test-name') || ''; } catch (e) { name = n ? dec(n[1]) : ''; }
  if (name) {
    document.querySelectorAll('[data-user="name"]').forEach(function (el) { el.textContent = name; });
    document.querySelectorAll('[data-user="initial"]').forEach(function (el) { el.textContent = name.charAt(0).toUpperCase(); });
  }

  window.addEventListener('hashchange', function () { show(current()); });
  show(current());

  // Кнопки «ввод → дальше» в полях: Enter в поле ведёт туда же, куда главная кнопка рядом.
  document.querySelectorAll('[data-next]').forEach(function (el) {
    el.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); location.href = el.dataset.next; }
    });
  });

  // «Скопировать» у адреса коннектора.
  document.querySelectorAll('[data-copy]').forEach(function (b) {
    b.addEventListener('click', function () {
      if (!navigator.clipboard) { b.textContent = 'Выделите адрес'; return; }
      navigator.clipboard.writeText(b.dataset.copy).then(function () { b.textContent = 'Скопировано'; },
        function () { b.textContent = 'Выделите адрес'; });
    });
  });

  // Закрыть открытые меню кликом мимо.
  document.addEventListener('click', function (e) {
    document.querySelectorAll('details[open].acct, details[open].site-menu, details[open].side-menu, details[open].proto, details[open].cmenu')
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
