import { apiFetch, apiJson } from './client';
import type { HistoryItem } from './types';

export interface StarredResponse {
  id: string;
  starred: boolean;
}

export async function listHistory(): Promise<HistoryItem[]> {
  return apiJson<HistoryItem[]>('/history');
}

export async function clearHistory(): Promise<void> {
  await apiFetch('/history', { method: 'DELETE' });
}

export async function deleteHistoryItem(id: string): Promise<void> {
  await apiFetch(`/history/${encodeURIComponent(id)}`, { method: 'DELETE' });
}

export async function setHistoryStarred(id: string, starred: boolean): Promise<StarredResponse> {
  return apiJson<StarredResponse>(`/history/${encodeURIComponent(id)}/starred`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ starred }),
  });
}

export interface NotesResponse {
  id: string;
  notes: string | null;
}

export async function setHistoryNotes(id: string, notes: string): Promise<NotesResponse> {
  return apiJson<NotesResponse>(`/history/${encodeURIComponent(id)}/notes`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes }),
  });
}
