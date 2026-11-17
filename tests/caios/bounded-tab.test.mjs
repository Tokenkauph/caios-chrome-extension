// Node 24 can load this dependency-free TypeScript helper directly.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { settleWithin } from '../../packages/playwright-core/src/tools/backend/caiosBoundedTab.ts';

test('successful tab header is retained', async () => {
  assert.equal(await settleWithin(Promise.resolve('Wikipedia'), 50), 'Wikipedia');
});

test('a permanently pending title does not block tab enumeration', async () => {
  const start = Date.now();
  const result = await settleWithin(new Promise(() => {}), 25);
  assert.equal(result, undefined);
  assert.ok(Date.now() - start < 500, 'bounded operation must finish quickly');
});

test('a rejected title also degrades gracefully', async () => {
  assert.equal(await settleWithin(Promise.reject(new Error('detached')), 100), undefined);
});
