import test from 'node:test';
import assert from 'node:assert/strict';
import {filterRows, pageRows, csvText} from './model.mjs';

const rows = [
  {symbol: 'B', id: 'HGNC:2', rank: null, p: null},
  {symbol: 'A', id: 'HGNC:1', mouseSymbol: 'Abc', rank: 1, p: 0, score: 0},
];
test('search matches human identifiers and mapped mouse symbols', () => {
  assert.equal(filterRows(rows, {query: 'hgnc:1'})[0].symbol, 'A');
  assert.equal(filterRows(rows, {query: ' abc '})[0].symbol, 'A');
  assert.equal(filterRows(rows, {query: 'unknown'}).length, 0);
});
test('missing evidence remains distinct from measured zero', () => {
  assert.deepEqual(filterRows(rows, {evidence: 'missing'}).map(r => r.symbol), ['B']);
  assert.deepEqual(filterRows(rows, {evidence: 'measured'}).map(r => r.symbol), ['A']);
  assert.equal(filterRows(rows, {sort: 'p'})[0].p, 0);
  assert.equal(rows[0].symbol, 'B');
});
test('pagination clamps invalid pages and handles empty results', () => {
  assert.equal(pageRows([], 99).page, 1);
  assert.equal(pageRows(rows, NaN).page, 1);
  assert.equal(pageRows(Array.from({length: 21}, (_, i) => i), 99).rows[0], 20);
});
test('CSV preserves missing values and escapes quotes and spreadsheet formulas', () => {
  const csv = csvText([{symbol: '=formula', id: 'a,"b', rank: null, effect: -2}], 'CD40');
  assert.ok(csv.includes('"\'=formula"'));
  assert.ok(csv.includes('"a,""b"'));
  assert.ok(csv.includes(',,"-2"'));
});
