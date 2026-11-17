import type { Candidates, Selection } from '../types';

// A tab that has closed must never remain implicitly selected after a refresh.
export function reconcileSelection(selection: Selection, candidates: Candidates): Selection {
  if (selection.groupId !== undefined)
    return candidates.groups.some(group => group.id === selection.groupId) ? selection : {};
  const available = new Set(candidates.tabs.map(tab => tab.id).filter((id): id is number => id !== undefined));
  const retained = (selection.tabIds ?? []).filter(id => available.has(id));
  return retained.length ? { tabIds: retained } : {};
}
