/**
 * Copyright (c) Microsoft Corporation.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


import React, { useCallback, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Button, ListItem, PageHeader, TabItem } from './tabItem';
import { getOrCreateAuthToken } from './authToken';
import { reconcileSelection } from './selection';
import * as icons from './icons';

import type { CandidateGroup, Candidates, PageMessage, Selection, SessionOptions } from '../types';

type Status =
  | { type: 'connecting' | 'connected' | 'error', message: string }
  | { type: 'error', versionMismatch: { extensionVersion: string } };

const SUPPORTED_PROTOCOL_VERSION = 2;
const params = new URLSearchParams(window.location.search);
const options = sessionOptions();

function sessionOptions(): SessionOptions {
  let clientName = 'unknown';
  try {
    clientName = JSON.parse(params.get('client') || '{}').name || clientName;
  } catch {
  }
  const tabGroup = params.get('tabGroup') === 'false' ? undefined : {
    title: params.get('tabGroupTitle') ?? undefined,
    color: params.get('tabGroupColor') ?? undefined,
  };
  return { clientName, tabGroup, background: params.get('background') === 'true' };
}

function relayUrlError(relayUrl: string | null): string | undefined {
  if (!relayUrl)
    return 'Missing mcpRelayUrl parameter in URL.';
  try {
    const host = new URL(relayUrl).hostname;
    if (host !== '127.0.0.1' && host !== '[::1]')
      return `CAIOS only accepts local browser connections (127.0.0.1 or [::1]). Received host: ${host}`;
  } catch (e) {
    return `Invalid mcpRelayUrl parameter in URL: ${relayUrl}. ${e}`;
  }
}

function protocolVersionError(): Status | undefined {
  const parsedVersion = parseInt(params.get('protocolVersion') ?? '', 10);
  const requestedVersion = isNaN(parsedVersion) ? 1 : parsedVersion;
  if (requestedVersion > SUPPORTED_PROTOCOL_VERSION)
    return { type: 'error', versionMismatch: { extensionVersion: chrome.runtime.getManifest().version } };
  if (requestedVersion < SUPPORTED_PROTOCOL_VERSION)
    return { type: 'error', message: 'This CAIOS browser client uses an incompatible protocol. Update the matching CAIOS client and extension together.' };
}

const ConnectApp: React.FC = () => {
  const [status, setStatus] = useState<Status | null>(null);
  const [candidates, setCandidates] = useState<Candidates | null>(null);
  const [selection, setSelection] = useState<Selection>({});
  const [refreshing, setRefreshing] = useState(false);

  const refreshCandidates = useCallback(async () => {
    setRefreshing(true);
    try {
      const response = await chrome.runtime.sendMessage<PageMessage>({ type: 'getCandidates' });
      if (!response?.success)
        throw new Error(response?.error || 'Unable to read available tabs.');
      const available = response as Candidates;
      setCandidates(available);
      setSelection(previous => reconcileSelection(previous, available));
      setStatus({ type: 'connecting', message: 'Tabs are up to date. Choose the tabs you want CAIOS to use.' });
    } catch (error) {
      setStatus({ type: 'error', message: `Unable to refresh tabs: ${String(error)}` });
    } finally {
      setRefreshing(false);
    }
  }, []);

  // The consent picker stays live if the user opens or closes a tab after this page appears.
  // Debouncing avoids extra work during page loads; no extra tab is authorized automatically.
  useEffect(() => {
    if (!candidates || status?.type !== 'connecting')
      return;
    let pending: ReturnType<typeof setTimeout> | undefined;
    const scheduleRefresh = () => {
      if (pending)
        clearTimeout(pending);
      pending = setTimeout(() => void refreshCandidates(), 300);
    };
    chrome.tabs.onCreated.addListener(scheduleRefresh);
    chrome.tabs.onUpdated.addListener(scheduleRefresh);
    chrome.tabs.onRemoved.addListener(scheduleRefresh);
    return () => {
      if (pending)
        clearTimeout(pending);
      chrome.tabs.onCreated.removeListener(scheduleRefresh);
      chrome.tabs.onUpdated.removeListener(scheduleRefresh);
      chrome.tabs.onRemoved.removeListener(scheduleRefresh);
    };
  }, [!!candidates, status?.type, refreshCandidates]);

  const connect = useCallback(async (selection: Selection) => {
    setCandidates(null);
    const started = performance.now();
    setStatus({ type: 'connecting', message: 'Selection approved. Connecting CAIOS to the chosen tab…' });
    // Only surface progress locally; do not log tab content, local relay URLs or authentication tokens.
    const slowNotice = setTimeout(() => {
      setStatus({
        type: 'connecting',
        message: 'Still connecting after 12 seconds. The tab is not confirmed accessible yet. Check Manage clients and the MCP client response before retrying.'
      });
    }, 12_000);
    try {
      const response = await chrome.runtime.sendMessage<PageMessage>({ type: 'connect', options, selection });
      if (response?.success)
        setStatus({ type: 'connected', message: `CAIOS connected in ${((performance.now() - started) / 1000).toFixed(1)}s after approval. Verify the chosen tab in your CAIOS client.` });
      else
        setStatus({ type: 'error', message: `Connection or selected-tab attachment failed: ${response?.error || 'unknown error'}` });
    } catch (error) {
      setStatus({ type: 'error', message: `Chrome could not complete the selected-tab connection: ${String(error)}` });
    } finally {
      clearTimeout(slowNotice);
    }
  }, []);

  useEffect(() => {
    const start = async () => {
      const relayUrl = params.get('mcpRelayUrl');
      const urlError = relayUrlError(relayUrl);
      if (urlError) {
        setStatus({ type: 'error', message: urlError });
        return;
      }
      const versionError = protocolVersionError();
      if (versionError) {
        setStatus(versionError);
        return;
      }
      let phase = 'registering the local connection request';
      try {
        setStatus({ type: 'connecting', message: `"${options.clientName}" is requesting a CAIOS Chrome connection.` });
        await chrome.runtime.sendMessage<PageMessage>({ type: 'connectionRequested', mcpRelayUrl: relayUrl! });
        phase = 'loading available tabs';
        setStatus({ type: 'connecting', message: 'Local connection request received. Loading available tabs…' });
        const token = params.get('token');
        if (!token) {
          await refreshCandidates();
          return;
        }
      // With a token, this page becomes the blank tab of the client; keep the token out of its history.
      const url = new URL(window.location.href);
      url.searchParams.delete('token');
      window.history.replaceState(null, '', url);
        if (token === getOrCreateAuthToken())
          await connect({});
        else
          setStatus({ type: 'error', message: 'Invalid token provided.' });
      } catch (error) {
        setStatus({ type: 'error', message: `CAIOS connection failed while ${phase}: ${String(error)}` });
      }
    };
    void start();
    // The service worker holds the pending request and stops after 30s without messages.
    const keepalive = setInterval(() => void chrome.runtime.sendMessage<PageMessage>({ type: 'keepalive' }).catch(() => {}), 20_000);
    return () => clearInterval(keepalive);
  }, [connect, refreshCandidates]);

  const toggleGroup = (groupId: number) => setSelection(selection.groupId === groupId ? {} : { groupId });
  const toggleTab = (tabId: number) => {
    const tabIds = selection.tabIds ?? [];
    setSelection({ tabIds: tabIds.includes(tabId) ? tabIds.filter(id => id !== tabId) : [...tabIds, tabId] });
  };

  return (
    <div className='page'>
      <PageHeader>
        <a className='page-header-link' href='manage.html' target='_blank' rel='noreferrer'>Manage CAIOS connections</a>
      </PageHeader>
      <div className='card'>
        {status && <StatusBanner status={status} />}

        {status?.type === 'connecting' && (
          <div className='card-body'>
            <div className='warning-banner'>
              {icons.alert()}
              <div>
                Allowing this connection exposes the entire browser to the client,
                including any signed-in sessions, cookies, and content in other tabs and windows.
                Once approved, the client may also be able to reconnect later without showing this dialog again,
                unless you rotate the token on the <a href='manage.html' target='_blank' rel='noreferrer'>Manage CAIOS connections</a> page and then restart the browser.
              </div>
            </div>

            {candidates && <>
              <div className='muted'>
                Choose the exact tab to share with CAIOS. This list updates when tabs open or close.
                {options.tabGroup && <> You can drag more tabs into the tab group later.</>}
              </div>
              {candidates.groups.length > 0 && (
                <div>
                  <h2 className='list-title'>Tab groups</h2>
                  <div className='list'>
                    {candidates.groups.map(group => (
                      <GroupItem
                        key={group.id}
                        group={group}
                        checked={selection.groupId === group.id}
                        onClick={() => toggleGroup(group.id)}
                      />
                    ))}
                  </div>
                </div>
              )}
              {candidates.tabs.length > 0 && (
                <div>
                  <h2 className='list-title'>Tabs</h2>
                  <div className='list'>
                    {candidates.tabs.map(tab => (
                      <TabItem
                        key={tab.id}
                        tab={tab}
                        checked={!!selection.tabIds?.includes(tab.id!)}
                        onClick={() => toggleTab(tab.id!)}
                      />
                    ))}
                  </div>
                </div>
              )}
            </>}
          </div>
        )}

        {candidates && (
          <div className='card-footer'>
            <div className='muted'>{selectionSummary(selection)}</div>
            <Button variant='default' disabled={refreshing} onClick={() => void refreshCandidates()}>{refreshing ? 'Refreshing…' : 'Refresh tabs'}</Button>
            <Button variant='primary' disabled={refreshing} onClick={() => void connect(selection)}>
              {selection.groupId !== undefined || selection.tabIds?.length ? 'Allow selected tabs' : 'Connect blank tab'}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

function selectionSummary(selection: Selection): string {
  if (selection.groupId !== undefined)
    return '1 tab group selected.';
  const count = selection.tabIds?.length ?? 0;
  if (count)
    return count === 1 ? '1 tab selected.' : `${count} tabs selected.`;
  return 'Nothing selected. The client gets a new blank tab.';
}

// The colors that Chrome uses for tab groups.
const GROUP_COLORS: Record<string, string> = {
  grey: '#5f6368',
  blue: '#1a73e8',
  red: '#d93025',
  yellow: '#f9ab00',
  green: '#188038',
  pink: '#d01884',
  purple: '#a142f4',
  cyan: '#007b83',
  orange: '#fa903e',
};

const GroupItem: React.FC<{ group: CandidateGroup, checked: boolean, onClick: () => void }> = ({ group, checked, onClick }) => {
  return (
    <ListItem
      icon={<span className='tab-favicon group-dot' style={{ backgroundColor: GROUP_COLORS[group.color] }} />}
      title={group.title || 'Unnamed group'}
      subtitle={`Tab group, ${group.tabs.length === 1 ? '1 tab' : `${group.tabs.length} tabs`}`}
      checked={checked}
      onClick={onClick}
    />
  );
};

const VersionMismatchError: React.FC<{ extensionVersion: string }> = ({ extensionVersion }) => {
  const readmeUrl = 'https://github.com/Tokenkauph/caios-chrome-extension/blob/main/packages/extension/CAIOS.md';
  return (
    <div>
      The CAIOS browser client needs a newer CAIOS Chrome Extension (installed version: {extensionVersion}).{' '}
      Reload the matching CAIOS extension after installing a verified update.{' '}
      See <a href={readmeUrl} target='_blank' rel='noopener noreferrer'>CAIOS installation instructions</a> for details.
    </div>
  );
};

const StatusBanner: React.FC<{ status: Status }> = ({ status }) => {
  return (
    <div className={`status-banner ${status.type}`}>
      {status.type === 'connected' && icons.check()}
      {status.type === 'error' && icons.cross()}
      {'versionMismatch' in status ? (
        <VersionMismatchError extensionVersion={status.versionMismatch.extensionVersion} />
      ) : (
        <div>{status.message}</div>
      )}
    </div>
  );
};

const container = document.getElementById('root');
if (container)
  createRoot(container).render(<ConnectApp />);
