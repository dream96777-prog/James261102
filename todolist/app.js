'use strict';

const STORAGE_KEY = 'todolist.v1';
const BACKUP_KEY = 'todolist.v1.backup';
const PROBE_KEY = 'todolist.probe';
const MAX_TEXT_LENGTH = 200;
const TOAST_DURATION_MS = 5000;

const STORAGE_MESSAGES = {
  unavailable: '이 브라우저에서는 저장되지 않습니다. 페이지를 닫으면 할일이 사라집니다.',
  quota: '저장 공간이 부족해 저장하지 못했습니다. 완료 항목을 지워주세요.',
  corrupted: '저장된 데이터를 읽지 못해 빈 목록으로 시작합니다. 원본은 백업해 두었습니다.',
};

const DATE_FORMAT = new Intl.DateTimeFormat('ko-KR', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  weekday: 'long',
});

const el = {
  banner: document.getElementById('banner'),
  date: document.getElementById('today-date'),
  progress: document.getElementById('progress'),
  progressBar: document.getElementById('progress-bar'),
  progressFill: document.getElementById('progress-fill'),
  progressText: document.getElementById('progress-text'),
  form: document.getElementById('todo-form'),
  input: document.getElementById('todo-input'),
  overdue: document.getElementById('overdue'),
  overdueTitle: document.getElementById('overdue-title'),
  overdueList: document.getElementById('overdue-list'),
  list: document.getElementById('todo-list'),
  empty: document.getElementById('empty'),
  clearCompleted: document.getElementById('clear-completed'),
  toast: document.getElementById('toast'),
  toastMessage: document.getElementById('toast-message'),
  viewTemplate: document.getElementById('todo-view-template'),
  editTemplate: document.getElementById('todo-edit-template'),
  overdueTemplate: document.getElementById('overdue-item-template'),
};

let storageIssue = null;
let todos = load();
let editingId = null;
let renderedDate = null;
let undoItems = [];
let toastTimer = null;

/* 날짜 */

// toISOString()은 UTC 기준이라 한국 시간 오전 9시 이전에 전날이 되므로 로컬 값으로 만든다.
function todayKey() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${now.getFullYear()}-${month}-${day}`;
}

function shortDate(key) {
  const [, month, day] = key.split('-');
  return `${Number(month)}월 ${Number(day)}일`;
}

/* 저장소 */

function isValidTodo(todo) {
  return Boolean(todo)
    && typeof todo.id === 'string'
    && typeof todo.text === 'string'
    && typeof todo.date === 'string'
    && typeof todo.completed === 'boolean';
}

function load() {
  storageIssue = null;
  let raw;
  try {
    localStorage.setItem(PROBE_KEY, '1');
    localStorage.removeItem(PROBE_KEY);
    raw = localStorage.getItem(STORAGE_KEY);
  } catch {
    storageIssue = 'unavailable';
    return [];
  }
  if (raw === null) return [];

  try {
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed.todos) && parsed.todos.every(isValidTodo)) return parsed.todos;
  } catch {
    // 아래에서 손상된 데이터로 처리한다.
  }
  storageIssue = 'corrupted';
  try {
    localStorage.setItem(BACKUP_KEY, raw);
  } catch {
    // 백업에 실패해도 앱은 계속 동작해야 한다.
  }
  return [];
}

function save() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: 1, todos }));
    storageIssue = null;
  } catch (error) {
    storageIssue = error.name === 'QuotaExceededError' && storageIssue !== 'unavailable' ? 'quota' : 'unavailable';
  }
}

function commit() {
  save();
  render();
}

/* 상태 변경 */

function createId() {
  if (crypto.randomUUID) return crypto.randomUUID();
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function normalizeText(text) {
  return text.trim().slice(0, MAX_TEXT_LENGTH);
}

function addTodo(text) {
  todos.push({
    id: createId(),
    text,
    date: todayKey(),
    completed: false,
    createdAt: new Date().toISOString(),
    completedAt: null,
  });
  commit();
}

function toggleTodo(id, completed) {
  const todo = todos.find((item) => item.id === id);
  if (!todo) return;
  todo.completed = completed;
  todo.completedAt = completed ? new Date().toISOString() : null;
  commit();
}

function removeTodos(predicate) {
  const removed = todos.filter(predicate);
  if (removed.length === 0) return;
  todos = todos.filter((item) => !predicate(item));
  commit();
  showUndoToast(removed);
}

function undoRemove() {
  const existingIds = new Set(todos.map((item) => item.id));
  todos.push(...undoItems.filter((item) => !existingIds.has(item.id)));
  hideToast();
  commit();
}

function carryOver(predicate) {
  const today = todayKey();
  todos.filter(predicate).forEach((item) => {
    item.date = today;
  });
  commit();
}

function isOverdue(todo, today = todayKey()) {
  return todo.date < today && !todo.completed;
}

/* 수정 */

function startEdit(id) {
  editingId = id;
  render();
}

function finishEdit(text, { refocus }) {
  const id = editingId;
  if (id === null) return;
  editingId = null;

  const todo = todos.find((item) => item.id === id);
  const next = text === null ? '' : normalizeText(text);
  if (todo && next && next !== todo.text) {
    todo.text = next;
    save();
  }
  render();

  if (refocus) {
    const item = [...el.list.children].find((child) => child.dataset.id === id);
    item?.querySelector('.edit-btn')?.focus();
  }
}

// 한글 입력 중 Enter를 누르면 조합이 끝나기 전에 제출될 수 있어, 조합이 끝난 뒤에 처리한다.
function onSubmitAfterComposition(form, input, handler) {
  let composing = false;
  let pending = false;

  input.addEventListener('compositionstart', () => {
    composing = true;
  });
  input.addEventListener('compositionend', () => {
    composing = false;
    if (pending) {
      pending = false;
      handler();
    }
  });
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    if (composing) {
      pending = true;
    } else {
      handler();
    }
  });
}

/* 렌더링 */

// 항목을 다시 만들지 않고 재사용해야 포커스가 유지되고, 수정 입력창의 blur로 다시 그려져도 클릭이 사라지지 않는다.
function syncList(parent, items, createItem, updateItem) {
  const existing = new Map([...parent.children].map((child) => [child.dataset.id, child]));
  const active = document.activeElement;

  items.forEach((item, index) => {
    const node = existing.get(item.id) ?? createItem(item);
    existing.delete(item.id);
    updateItem(node, item);
    if (parent.children[index] !== node) {
      parent.insertBefore(node, parent.children[index] ?? null);
    }
  });
  existing.forEach((node) => node.remove());

  if (active !== document.activeElement && active?.isConnected && editingId === null) {
    active.focus();
  }
}

function createListItem(item) {
  const node = document.createElement('li');
  node.dataset.id = item.id;
  return node;
}

function enterEditMode(node, todo) {
  node.replaceChildren(el.editTemplate.content.cloneNode(true));
  const form = node.querySelector('.edit-form');
  const input = node.querySelector('.edit-input');
  input.value = todo.text;
  input.setAttribute('aria-label', `'${todo.text}' 수정`);

  onSubmitAfterComposition(form, input, () => finishEdit(input.value, { refocus: true }));
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !event.isComposing) finishEdit(null, { refocus: true });
  });
  input.addEventListener('blur', () => finishEdit(input.value, { refocus: false }));

  input.focus();
  input.select();
}

function updateTodoItem(node, todo) {
  const mode = todo.id === editingId ? 'edit' : 'view';
  node.className = 'todo';
  node.classList.toggle('done', todo.completed);

  if (node.dataset.mode !== mode) {
    node.dataset.mode = mode;
    if (mode === 'edit') {
      enterEditMode(node, todo);
    } else {
      node.replaceChildren(el.viewTemplate.content.cloneNode(true));
    }
  }
  if (mode === 'edit') return;

  const check = node.querySelector('.todo-check');
  check.checked = todo.completed;
  check.setAttribute('aria-label', `${todo.text} 완료`);
  node.querySelector('.todo-text').textContent = todo.text;
  node.querySelector('.edit-btn').setAttribute('aria-label', `${todo.text} 수정`);
  node.querySelector('.delete-btn').setAttribute('aria-label', `${todo.text} 삭제`);
}

function updateOverdueItem(node, todo) {
  node.className = 'overdue-item';
  if (!node.hasChildNodes()) {
    node.append(el.overdueTemplate.content.cloneNode(true));
  }
  node.querySelector('.overdue-date').textContent = shortDate(todo.date);
  node.querySelector('.todo-text').textContent = todo.text;
  node.querySelector('.carry-btn').setAttribute('aria-label', `${todo.text} 오늘로 가져오기`);
  node.querySelector('.delete-btn').setAttribute('aria-label', `${todo.text} 삭제`);
}

function byCreatedAt(a, b) {
  return (a.createdAt ?? '').localeCompare(b.createdAt ?? '');
}

function render() {
  const today = todayKey();
  renderedDate = today;

  const todayTodos = todos.filter((todo) => todo.date === today).sort(byCreatedAt);
  const active = todayTodos.filter((todo) => !todo.completed);
  const completed = todayTodos.filter((todo) => todo.completed);
  const overdue = todos
    .filter((todo) => isOverdue(todo, today))
    .sort((a, b) => a.date.localeCompare(b.date) || byCreatedAt(a, b));

  // 수정 중인 항목이 다른 탭이나 날짜 변경으로 사라지면, 제거될 때의 blur가 다시 저장하지 않도록 먼저 해제한다.
  if (!todayTodos.some((todo) => todo.id === editingId)) editingId = null;

  el.banner.hidden = storageIssue === null;
  el.banner.textContent = storageIssue ? STORAGE_MESSAGES[storageIssue] : '';

  el.date.textContent = DATE_FORMAT.format(new Date());
  el.date.dateTime = today;

  const percent = todayTodos.length ? Math.round((completed.length / todayTodos.length) * 100) : 0;
  el.progress.hidden = todayTodos.length === 0;
  el.progressBar.setAttribute('aria-valuenow', String(percent));
  el.progressFill.style.width = `${percent}%`;
  el.progressText.textContent = `${completed.length} / ${todayTodos.length} 완료`;

  el.overdue.hidden = overdue.length === 0;
  el.overdueTitle.textContent = `지난 할일 ${overdue.length}개`;
  syncList(el.overdueList, overdue, createListItem, updateOverdueItem);

  syncList(el.list, [...active, ...completed], createListItem, updateTodoItem);

  el.empty.hidden = todayTodos.length > 0;
  el.clearCompleted.hidden = completed.length === 0;
}

/* 토스트 */

function startToastTimer() {
  clearTimeout(toastTimer);
  toastTimer = setTimeout(hideToast, TOAST_DURATION_MS);
}

function showUndoToast(items) {
  undoItems = items;
  el.toastMessage.textContent = items.length === 1 ? '삭제했습니다.' : `${items.length}개를 삭제했습니다.`;
  el.toast.hidden = false;
  startToastTimer();
}

function hideToast() {
  clearTimeout(toastTimer);
  const hadFocus = el.toast.contains(document.activeElement);
  el.toast.hidden = true;
  undoItems = [];
  if (hadFocus) el.input.focus();
}

/* 이벤트 */

const actions = {
  edit: (id) => startEdit(id),
  delete: (id) => removeTodos((todo) => todo.id === id),
  carry: (id) => carryOver((todo) => todo.id === id),
  'carry-all': () => carryOver((todo) => isOverdue(todo)),
  'delete-overdue': () => removeTodos((todo) => isOverdue(todo)),
  'clear-completed': () => {
    const today = todayKey();
    removeTodos((todo) => todo.date === today && todo.completed);
  },
  undo: () => undoRemove(),
};

document.addEventListener('click', (event) => {
  const button = event.target.closest('[data-action]');
  if (!button) return;
  const id = button.closest('[data-id]')?.dataset.id;
  actions[button.dataset.action](id);

  // 키보드로 누른 버튼이 사라지거나 숨겨지면 포커스를 잃지 않게 입력창으로 옮긴다. (detail 0 = 키보드 동작)
  if (event.detail === 0 && button.offsetParent === null && editingId === null) el.input.focus();
});

el.list.addEventListener('change', (event) => {
  if (!event.target.matches('.todo-check')) return;
  toggleTodo(event.target.closest('[data-id]').dataset.id, event.target.checked);
});

el.list.addEventListener('dblclick', (event) => {
  if (!event.target.matches('.todo-text')) return;
  startEdit(event.target.closest('[data-id]').dataset.id);
});

onSubmitAfterComposition(el.form, el.input, () => {
  const text = normalizeText(el.input.value);
  if (text) addTodo(text);
  el.input.value = '';
  el.input.focus();
});

el.toast.addEventListener('mouseenter', () => clearTimeout(toastTimer));
el.toast.addEventListener('mouseleave', () => {
  if (!el.toast.contains(document.activeElement)) startToastTimer();
});
el.toast.addEventListener('focusin', () => clearTimeout(toastTimer));
el.toast.addEventListener('focusout', () => {
  if (!el.toast.hidden) startToastTimer();
});

window.addEventListener('storage', (event) => {
  if (event.key !== STORAGE_KEY && event.key !== null) return;
  todos = load();
  render();
});

function refreshIfDateChanged() {
  if (todayKey() !== renderedDate) render();
}

window.addEventListener('focus', refreshIfDateChanged);
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) refreshIfDateChanged();
});

render();
