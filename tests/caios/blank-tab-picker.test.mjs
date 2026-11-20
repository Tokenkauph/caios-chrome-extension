import assert from 'node:assert/strict';
import { test } from 'node:test';
import { isChromeNewTabUrl, isDebuggableUrl } from '../../packages/extension/src/ownedTab.ts';

test('only built-in Chrome New Tab variants receive the consented blank conversion', () => {
  for (const url of ['chrome://newtab', 'chrome://newtab/', 'chrome://new-tab-page', 'chrome://new-tab-page/'])
    assert.equal(isChromeNewTabUrl(url), true, url);
  for (const url of ['chrome://settings/', 'chrome://extensions/', 'chrome://version/', 'devtools://devtools/', 'https://example.org/', 'about:blank', undefined])
    assert.equal(isChromeNewTabUrl(url), false, String(url));
});

test('existing Chrome-internal debugger protections remain in place', () => {
  for (const url of ['chrome://newtab/', 'chrome://settings/', 'chrome://extensions/', 'edge://settings/', 'devtools://devtools/'])
    assert.equal(isDebuggableUrl(url), false, url);
  for (const url of ['about:blank', 'https://example.org/'])
    assert.equal(isDebuggableUrl(url), true, url);
});
