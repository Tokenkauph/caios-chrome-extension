import assert from 'node:assert/strict';
import { test } from 'node:test';
import { reconcileSelection } from '../../packages/extension/src/ui/selection.ts';

const candidates = {
  groups: [{ id: 9, title: 'Work', color: 'blue', tabs: [] }],
  tabs: [{ id: 101, title: 'Wizard story' }, { id: 102, title: 'Other tab' }],
};

test('newly opened tab is eligible after refreshing', () => {
  assert.deepEqual(reconcileSelection({}, candidates), {});
  assert.deepEqual(reconcileSelection({ tabIds: [101] }, candidates), { tabIds: [101] });
});
test('closed tabs are removed from a pending selection', () => {
  assert.deepEqual(reconcileSelection({ tabIds: [99, 102] }, candidates), { tabIds: [102] });
  assert.deepEqual(reconcileSelection({ tabIds: [99] }, candidates), {});
});
test('group selections stay only if their group still exists', () => {
  assert.deepEqual(reconcileSelection({ groupId: 9 }, candidates), { groupId: 9 });
  assert.deepEqual(reconcileSelection({ groupId: 12 }, candidates), {});
});
