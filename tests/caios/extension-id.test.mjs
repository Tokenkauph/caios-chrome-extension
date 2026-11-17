import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';

const manifest = JSON.parse(readFileSync(new URL('../../packages/extension/manifest.json', import.meta.url), 'utf8'));
const der = Buffer.from(manifest.key, 'base64');
const digest = createHash('sha256').update(der).digest().subarray(0, 16);
const caiosId = Array.from(digest, byte => String.fromCharCode(97 + (byte >> 4)) + String.fromCharCode(97 + (byte & 15))).join('');
const official = 'mmlmfjhmonkocbjadbfplnigmagldckm';

function configuredId(id) {
  const env = { ...process.env };
  if (id === undefined)
    delete env.CAIOS_PLAYWRIGHT_EXTENSION_ID;
  else
    env.CAIOS_PLAYWRIGHT_EXTENSION_ID = id;
  return spawnSync(process.execPath, ['--input-type=module', '--eval',
    "import { playwrightExtensionId } from './packages/playwright-core/src/tools/utils/extension.ts'; process.stdout.write(playwrightExtensionId);"],
    { encoding: 'utf8', env });
}

test('CAIOS manifest has distinct stable ID', () => {
  assert.match(caiosId, /^[a-p]{32}$/);
  assert.notEqual(caiosId, official);
});

test('official MCP ID remains default', () => {
  const result = configuredId(undefined);
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout, official);
});

test('explicit CAIOS ID directs the forked MCP', () => {
  const result = configuredId(caiosId);
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout, caiosId);
});

test('invalid ID fails before connection', () => {
  const result = configuredId('invalid-id');
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /CAIOS_PLAYWRIGHT_EXTENSION_ID must/);
});
