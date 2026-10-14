const all = __DATA__;
const hours = __HOURS__;
let shown = all.slice();
let idx = 0;

const $ = id => document.getElementById(id);

function renderList() {
  const list = $('list');
  list.innerHTML = '';
  shown.forEach((e, i) => {
    const li = document.createElement('li');
    li.textContent = e.label;
    li.className = i === idx ? 'active' : '';
    li.onclick = () => go(i);
    list.appendChild(li);
  });
}

function go(i) {
  if (!shown.length) return;
  idx = Math.max(0, Math.min(i, shown.length - 1));
  const e = shown[idx];
  $('title').textContent = e.label + '  (' + (idx + 1) + '/' + shown.length + ')';
  $('skew').src = e.skew;
  $('diffs').src = e.diffs;
  renderList();
  $('list').children[idx].scrollIntoView({ block: 'nearest' });
}

function setFilter(h, btn) {
  shown = h === null ? all.slice() : all.filter(e => e.hour === h);
  document.querySelectorAll('#filters button').forEach(b => b.classList.remove('on'));
  btn.classList.add('on');
  go(0);
}

const f = $('filters');
const mk = (text, h) => {
  const b = document.createElement('button');
  b.textContent = text;
  b.onclick = () => setFilter(h, b);
  f.appendChild(b);
  return b;
};
const allBtn = mk('All', null);
hours.forEach(h => mk(String(h).padStart(2, '0') + 'Z', h));
allBtn.classList.add('on');

$('prev').onclick = () => go(idx - 1);
$('next').onclick = () => go(idx + 1);
document.addEventListener('keydown', ev => {
  if (ev.key === 'ArrowLeft' || ev.key === 'ArrowUp') { go(idx - 1); ev.preventDefault(); }
  if (ev.key === 'ArrowRight' || ev.key === 'ArrowDown') { go(idx + 1); ev.preventDefault(); }
  if (ev.key === 'Home') { go(0); ev.preventDefault(); }
  if (ev.key === 'End') { go(shown.length - 1); ev.preventDefault(); }
});

go(0);