export const PAGE_SIZE = 10;
export const ENDPOINTS = ['MHCII', 'CD40', 'PDL1'];

export function filterRows(rows, {query = '', evidence = 'all', sort = 'rank'}) {
  const term = query.trim().toLocaleUpperCase();
  const selected = rows.filter(row => (!term || [row.symbol, row.id, row.mouseSymbol].some(value => value?.toLocaleUpperCase().includes(term))) &&
    (evidence === 'all' || (evidence === 'measured' ? row.rank !== null : row.rank === null)));
  return selected.sort((a, b) => {
    if (sort === 'symbol') return a.symbol.localeCompare(b.symbol);
    const key = sort === 'p' ? 'p' : 'rank';
    return (a[key] ?? Infinity) - (b[key] ?? Infinity) || a.symbol.localeCompare(b.symbol);
  });
}

export function pageRows(rows, page) {
  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const current = Math.min(pages, Math.max(1, Number.isFinite(page) ? Math.floor(page) : 1));
  return {rows: rows.slice((current - 1) * PAGE_SIZE, current * PAGE_SIZE), page: current, pages};
}

export function csvText(rows, endpoint) {
  const columns = ['endpoint', 'symbol', 'id', 'rank', 'score', 'effect', 'p', 'fdr', 'marker', 'source', 'doi', 'sourceLocation', 'frequency', 'rankLow', 'rankHigh'];
  const cell = value => {
    if (value == null) return '';
    let text = String(value);
    if (typeof value === 'string' && /^[=+@\-\t\r]/.test(text)) text = `'${text}`;
    return `"${text.replaceAll('"', '""')}"`;
  };
  return [columns.join(','), ...rows.map(row => columns.map(key => cell(key === 'endpoint' ? endpoint : row[key])).join(','))].join('\r\n');
}
