import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
import { test } from 'node:test';

// Node's TS stripper does not resolve this repo's bundler-style extensionless TS import.
registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier === './ownedTab' && context.parentURL?.endsWith('/tabPicker.ts'))
      return nextResolve('./ownedTab.ts', context);
    return nextResolve(specifier, context);
  },
});
const { TabPicker } = await import('../../packages/extension/src/tabPicker.ts');

function fixture() {
  const tabs = new Map([
    [11, { id: 11, title: 'New Tab', url: 'chrome://newtab/' }],
    [12, { id: 12, title: 'Settings', url: 'chrome://settings/' }],
    [13, { id: 13, title: 'Web', url: 'https://example.org/' }],
    [14, { id: 14, title: 'Blank', url: 'about:blank' }],
  ]);
  const updated = [];
  const claimed = [];
  globalThis.chrome = {
    tabs: {
      query: async () => [...tabs.values()],
      get: async id => ({ ...tabs.get(id) }),
      update: async (id, options) => {
        updated.push({ id, url: options.url });
        const tab = tabs.get(id);
        if (!tab)
          throw new Error('Tab not found');
        tab.url = options.url;
        return { ...tab };
      },
    },
  };
  const registry = {
    isFree: () => true,
    claim: tab => claimed.push(tab.id),
  };
  const picker = new TabPicker(registry, { unclaimedGroups: async () => [] });
  return { picker, tabs, updated, claimed };
}

test('Chrome New Tab is offered but settings remains excluded', async () => {
  const { picker } = fixture();
  const candidates = await picker.candidates();
  assert.deepEqual(candidates.tabs.map(tab => tab.id), [11, 13, 14]);
  assert.deepEqual(candidates.groups, []);
});

test('converts only the explicitly selected Chrome New Tab, preserving the tab ID', async () => {
  const { picker, tabs, updated, claimed } = fixture();
  const selected = await picker.apply({ tabIds: [11] }, {}, 999);
  assert.deepEqual(selected.map(tab => [tab.id, tab.url]), [[11, 'about:blank']]);
  assert.deepEqual(updated, [{ id: 11, url: 'about:blank' }]);
  assert.deepEqual(claimed, [11]);
  assert.equal(tabs.get(12).url, 'chrome://settings/');
  assert.equal(tabs.get(13).url, 'https://example.org/');
});

test('ordinary website and genuine about:blank tabs do not require conversion', async () => {
  const { picker, updated, claimed } = fixture();
  await picker.apply({ tabIds: [13] }, {}, 999);
  await picker.apply({ tabIds: [14] }, {}, 999);
  assert.deepEqual(updated, []);
  assert.deepEqual(claimed, [13, 14]);
});

test('multiple selected tabs never trigger implicit blank-tab conversion', async () => {
  const { picker, updated } = fixture();
  await picker.apply({ tabIds: [11, 13] }, {}, 999);
  assert.deepEqual(updated, []);
});

test('failed tab-ID preservation rejects the claim', async () => {
  const { picker, claimed } = fixture();
  globalThis.chrome.tabs.update = async () => ({ id: 99, url: 'about:blank' });
  await assert.rejects(picker.apply({ tabIds: [11] }, {}, 999), /could not become/);
  assert.deepEqual(claimed, []);
});
