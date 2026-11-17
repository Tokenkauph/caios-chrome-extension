/* Focused CAIOS relay retry acceptance without a real browser or user profile. */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const ts = require('typescript');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const source = fs.readFileSync(path.join(root, 'packages/extension/src/connectionBroker.ts'), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;

function setup(failures) {
  let attempts = 0;
  let reserved = 0;
  let released = 0;
  let created = 0;
  const channel = { closed: false };
  const Channel = {
    open: async () => {
      ++attempts;
      if (attempts <= failures)
        throw new Error('WebSocket error');
      return channel;
    },
  };
  class ClientSession {
    constructor(connectedChannel) {
      assert.equal(connectedChannel, channel);
      created++;
      this.options = { clientName: 'CAIOS test', background: true };
    }
    didInitialize() {}
    close() {}
  }
  const listeners = { add() {}, setEnabled() {} };
  const registry = {
    reserve: async () => { reserved++; },
    unreserve: () => { released++; },
    releaseAll: async () => {},
    tabIdsOf: () => [43],
  };
  const groups = {
    ungroup: async () => {}, register() {}, orphan: async () => {},
  };
  const picker = { apply: async () => [{ id: 43, windowId: 1 }] };
  const chrome = {
    tabs: { onRemoved: {}, update: async () => {}, remove: async () => {} },
    windows: { update: async () => {} },
    runtime: { getPlatformInfo: async () => ({}) },
  };
  const exports = {};
  vm.runInNewContext(compiled, {
    exports,
    require: name => {
      if (name === './channel') return { Channel };
      if (name === './clientSession') return { ClientSession };
      throw new Error('Unexpected import: ' + name);
    },
    chrome, setTimeout, clearTimeout, setInterval: () => 0, clearInterval: () => {},
  }, { filename: 'connectionBroker.js' });
  const broker = new exports.ConnectionBroker(registry, groups, picker, listeners);
  return { broker, get state() { return { attempts, reserved, released, created }; } };
}

test('one Allow action survives one transient local relay failure', async () => {
  const env = setup(1);
  await env.broker.request(42, 'ws://127.0.0.1:12345/extension/test');
  await env.broker.connect(42, { clientName: 'CAIOS test', background: true }, { tabIds: [43] });
  assert.deepEqual(env.state, { attempts: 2, reserved: 1, released: 1, created: 1 });
  assert.equal(env.broker.status().length, 1);
});

test('persistent relay failure releases only pending request, never attaches tab', async () => {
  const env = setup(2);
  await env.broker.request(42, 'ws://127.0.0.1:12345/extension/test');
  await assert.rejects(
    env.broker.connect(42, { clientName: 'CAIOS test', background: true }, { tabIds: [43] }),
    /MCP relay unavailable after automatic retry/,
  );
  assert.deepEqual(env.state, { attempts: 2, reserved: 1, released: 1, created: 0 });
  assert.equal(env.broker.status().length, 0);
});
