import {ENDPOINTS, filterRows, pageRows, csvText} from './model.mjs';

const $ = id => document.getElementById(id);
const params = new URLSearchParams(location.search);
const state = {
  endpoint: ENDPOINTS.includes(params.get('endpoint')) ? params.get('endpoint') : 'MHCII',
  query: params.get('q') || '',
  evidence: ['measured', 'missing'].includes(params.get('evidence')) ? params.get('evidence') : 'all',
  sort: ['symbol', 'p'].includes(params.get('sort')) ? params.get('sort') : 'rank',
  page: Math.max(1, Number(params.get('page')) || 1), selected: params.get('gene'),
};
let allRows = [], filtered = [], summary, controller;
const cache = new Map();
const integer = value => Number(value).toLocaleString('en-US', {maximumFractionDigits: 0});
const decimal = (value, digits = 3) => value == null ? 'Not available' : Number(value).toFixed(digits);
const probability = value => value == null ? 'Not available' : value < .001 ? value.toExponential(2) : value.toFixed(3);

function el(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function syncUrl() {
  const query = new URLSearchParams({endpoint: state.endpoint});
  if (state.query) query.set('q', state.query);
  if (state.evidence !== 'all') query.set('evidence', state.evidence);
  if (state.sort !== 'rank') query.set('sort', state.sort);
  if (state.page > 1) query.set('page', String(state.page));
  if (state.selected) query.set('gene', state.selected);
  history.replaceState(null, '', `${location.pathname}?${query}${location.hash}`);
}

function pairs(section, values) {
  const dl = el('dl');
  for (const [label, value] of values) dl.append(el('dt', label), el('dd', value));
  section.append(dl);
}

function detailSection(title) {
  const section = el('section', undefined, 'detail-section');
  section.append(el('h4', title));
  return section;
}

function renderDetail(row) {
  $('detail-title').textContent = row?.symbol || 'Gene evidence';
  $('gene-id').textContent = row ? (row.id || 'Stable ID unresolved') : 'Select a candidate';
  const content = $('detail-content');
  content.replaceChildren();
  if (!row) {
    content.append(el('p', 'Choose a matching candidate to inspect its evidence.', 'muted'));
    return;
  }
  const human = detailSection('Human transcriptomic association');
  pairs(human, [['Standardized effect', decimal(row.effect)], ['Primary FDR', probability(row.fdr)], ['p-value', probability(row.p)]]);
  human.append(el('p', `${summary.patients} patients. This is an observational association, not a functional effect.`));
  const marker = detailSection(`${state.endpoint === 'PDL1' ? 'PD-L1' : state.endpoint} marker evidence`);
  if (row.rank === null) {
    marker.append(el('p', 'No eligible marker evidence. The transcriptomic result remains available; missing evidence is not a negative result.'));
    content.append(human, marker);
    return;
  }
  pairs(marker, [['Integrated rank', integer(row.rank)], ['Heuristic score', decimal(row.score)], ['Marker contrast', decimal(row.marker)]]);
  marker.append(el('p', 'Mouse macrophages. The contrast is high-minus-low selection enrichment, not an expression fold change.'));
  const stability = detailSection('Patient-resampling stability');
  pairs(stability, [['Top-20 frequency', row.frequency == null ? 'Not available' : `${Math.round(row.frequency * 100)}%`],
    ['Central 95% rank range', row.rankLow == null ? 'Not available' : `${integer(row.rankLow)}–${integer(row.rankHigh)}`]]);
  stability.append(el('p', `${summary.bootstrapDraws} paired patient draws, with marker evidence fixed. These ranges are not functional-performance confidence intervals.`));
  const source = detailSection('Source and mapping');
  source.append(el('p', `${row.mouseSymbol} → ${row.symbol} · ${row.mouseId || 'Mouse ID unresolved'}`));
  source.append(el('p', row.source, 'source-location'));
  source.append(el('p', `eLife Figure 1 source workbook · ${row.sourceLocation}`, 'source-location'));
  const link = el('a', 'Open source paper ↗');
  link.href = `https://doi.org/${encodeURI(row.doi)}`;
  link.target = '_blank'; link.rel = 'noopener noreferrer';
  source.append(link);
  content.append(human, marker, stability, source);
}

function render() {
  filtered = filterRows(allRows, state);
  const view = pageRows(filtered, state.page);
  state.page = view.page;
  let selected = view.rows.find(row => row.symbol === state.selected) || view.rows[0];
  state.selected = selected?.symbol || null;
  const fragment = document.createDocumentFragment();
  for (const row of view.rows) {
    const tr = document.createElement('tr');
    tr.setAttribute('aria-selected', String(row.symbol === state.selected));
    tr.append(el('td', row.rank === null ? '—' : integer(row.rank)));
    const cell = el('td');
    const button = el('button', row.symbol, 'gene-button');
    button.type = 'button';
    button.setAttribute('aria-label', `Inspect ${row.symbol}`);
    button.setAttribute('aria-pressed', String(row.symbol === state.selected));
    button.addEventListener('click', () => {
      state.selected = row.symbol;
      renderDetail(row);
      document.querySelectorAll('#rows tr').forEach(item => {
        const active = item.querySelector('button').textContent === row.symbol;
        item.setAttribute('aria-selected', String(active));
        item.querySelector('button').setAttribute('aria-pressed', String(active));
      });
      syncUrl();
      if (matchMedia('(max-width:760px)').matches) {
        $('detail').scrollIntoView({block: 'start'});
        $('detail-title').setAttribute('tabindex', '-1');
        $('detail-title').focus({preventScroll: true});
      }
    });
    cell.append(button); tr.append(cell);
    tr.append(el('td', row.score === null ? '—' : decimal(row.score), 'number'));
    tr.append(el('td', probability(row.fdr), 'number'));
    fragment.append(tr);
  }
  $('rows').replaceChildren(fragment);
  $('empty').hidden = filtered.length !== 0;
  $('result-count').textContent = `${integer(filtered.length)} candidates · ${integer(filtered.filter(row => row.rank !== null).length)} ranked`;
  $('page-label').textContent = `Page ${view.page} of ${integer(view.pages)}`;
  $('previous').disabled = view.page <= 1;
  $('next').disabled = view.page >= view.pages;
  $('export').disabled = filtered.length === 0;
  renderDetail(selected);
  syncUrl();
}

function renderSummary() {
  $('release').textContent = `Release ${summary.release}`;
  $('cohort').textContent = `${summary.patients} patients · ${integer(summary.genes)} candidate genes · GSE131907`;
  $('baseline-note').textContent = `${summary.patients} patients; ${summary.primaryDiscoveries} primary discoveries at 5% FDR.`;
  $('evidence-note').textContent = `${integer(summary.markerRecords)} mouse marker records, with qualitative T-cell findings kept separate.`;
  $('robustness-note').textContent = `${summary.bootstrapDraws} patient-bootstrap draws. Independent validation remains ${summary.validation}.`;
  const coverage = summary.coverage[state.endpoint];
  $('coverage-note').textContent = `${integer(coverage.ranked)} of ${integer(coverage.total)} genes have eligible mapped marker evidence. The other ${integer(coverage.total - coverage.ranked)} are left unranked for integration.`;
  $('report-links').replaceChildren(...summary.documents.map(doc => {
    const link = el('a');
    if (!/^downloads\/[a-z-]+\.md$/.test(doc.url)) throw new Error('Invalid report URL');
    link.href = doc.url; link.download = '';
    link.append(el('span', doc.title), el('small', 'MD ↓'));
    return link;
  }));
}

async function getJson(path, signal) {
  const response = await fetch(path, {signal});
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

async function load() {
  controller?.abort();
  controller = new AbortController();
  const signal = controller.signal;
  $('workspace').setAttribute('aria-busy', 'true');
  allRows = []; filtered = [];
  $('load-error').hidden = true;
  $('export').disabled = $('previous').disabled = $('next').disabled = true;
  $('result-count').textContent = 'Loading candidates…';
  $('rows').replaceChildren();
  $('empty').hidden = true;
  $('detail-title').textContent = 'Gene evidence';
  $('gene-id').textContent = 'Loading…';
  $('detail-content').replaceChildren(el('p', 'Loading source evidence…', 'muted'));
  try {
    summary ||= await getJson('data/summary.json', signal);
    const endpoint = state.endpoint;
    const rows = cache.get(endpoint) || await getJson(`data/${endpoint}.json`, signal);
    if (signal.aborted) return;
    if (!Array.isArray(rows) || rows.length !== summary.genes) throw new Error('Incomplete candidate snapshot');
    cache.set(endpoint, rows);
    allRows = rows;
    // A shared gene URL opens the corresponding page when no filter is active.
    if (state.selected && !state.query) {
      const index = filterRows(allRows, state).findIndex(row => row.symbol === state.selected);
      if (index >= 0) state.page = Math.floor(index / 10) + 1;
    }
    renderSummary(); render();
  } catch (error) {
    if (signal.aborted) return;
    allRows = []; filtered = [];
    $('load-error').hidden = false;
    $('result-count').textContent = 'Results unavailable';
    $('gene-id').textContent = 'Results unavailable';
    $('detail-content').replaceChildren(el('p', 'Retry loading to inspect the evidence.', 'muted'));
  } finally {
    if (!signal.aborted) $('workspace').setAttribute('aria-busy', 'false');
  }
}

for (const name of ['endpoint', 'evidence', 'sort']) $(name).value = state[name];
$('search').value = state.query;
$('search').addEventListener('input', event => {state.query = event.target.value; state.page = 1; state.selected = null; if (allRows.length) render();});
for (const name of ['evidence', 'sort']) $(name).addEventListener('change', event => {state[name] = event.target.value; state.page = 1; state.selected = null; if (allRows.length) render();});
$('endpoint').addEventListener('change', event => {state.endpoint = event.target.value; state.page = 1; state.selected = null; load();});
$('reset').addEventListener('click', () => {
  state.query = ''; state.evidence = 'all'; state.sort = 'rank'; state.page = 1; state.selected = null;
  $('search').value = ''; $('evidence').value = 'all'; $('sort').value = 'rank';
  if (allRows.length) render();
});
$('previous').addEventListener('click', () => {state.page--; state.selected = null; render();});
$('next').addEventListener('click', () => {state.page++; state.selected = null; render();});
$('retry').addEventListener('click', load);
$('export').addEventListener('click', () => {
  if (!filtered.length) return;
  const blob = new Blob([csvText(filtered, state.endpoint)], {type: 'text/csv;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const link = el('a'); link.href = url; link.download = `oncomyeloid-${state.endpoint}-filtered.csv`;
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
load();
