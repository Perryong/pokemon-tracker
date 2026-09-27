import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, renderHook, waitFor } from '@testing-library/react';
import { useCards, useSets } from '../api';
import * as client from '../tcgdex';
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
it('paginates and filters sets without requesting the same dataset again', async () => {
  const fetch = vi.spyOn(client, 'fetchAllSets').mockResolvedValue([
    { id: 'a', name: 'First', cardCount: { total: 1, official: 1 } },
    { id: 'b', name: 'Second', cardCount: { total: 1, official: 1 } },
  ]);
  const { result, rerender } = renderHook(({ page }) => useSets(page, 1), { initialProps: { page: 1 } });
  await waitFor(() => expect(result.current.loading).toBe(false));
  rerender({ page: 2 });
  expect(result.current.sets[0].id).toBe('b');
  expect(result.current.loading).toBe(false);
  expect(fetch).toHaveBeenCalledTimes(1);
});
it('paginates cards without requesting the same set again', async () => {
  const fetch = vi.spyOn(client, 'fetchSetWithCards').mockResolvedValue({
    id: 'base1', name: 'Base', cardCount: { total: 2, official: 2 },
    cards: [{ id: 'base1-1', localId: '1', name: 'First' }, { id: 'base1-2', localId: '2', name: 'Second' }],
  } as Awaited<ReturnType<typeof client.fetchSetWithCards>>);
  const { result, rerender } = renderHook(({ page }) => useCards('base1', page, 1), { initialProps: { page: 1 } });
  await waitFor(() => expect(result.current.cards).toHaveLength(1));
  rerender({ page: 2 });
  expect(result.current.cards[0].id).toBe('base1-2');
  expect(result.current.loading).toBe(false);
  expect(fetch).toHaveBeenCalledTimes(1);
});

it('loads the selected series before paginating its sets', async () => {
  vi.spyOn(client, 'fetchAllSets').mockResolvedValue([{ id: 'other', name: 'Other', cardCount: { official: 1, total: 1 } }]);
  const fetch = vi.spyOn(client.tcgdex, 'fetch').mockResolvedValue({
    id: 'base', name: 'Base', sets: [
      { id: 'base1', name: 'Base Set', cardCount: { official: 102, total: 102 } },
      { id: 'base2', name: 'Jungle', cardCount: { official: 64, total: 64 } },
    ],
  } as never);
  const { result, rerender } = renderHook(({ series, page }) => useSets(page, 1, series ? { series } : {}), { initialProps: { series: '', page: 1 } });
  await waitFor(() => expect(result.current.loading).toBe(false));
  rerender({ series: 'base', page: 1 });
  await waitFor(() => expect(result.current.sets[0]?.name).toBe('Base Set'));
  expect(result.current.sets[0].series).toBe('Base');
  expect(result.current.totalSets).toBe(2);
  expect(fetch).toHaveBeenCalledWith('series', 'base');
  rerender({ series: 'base', page: 2 });
  expect(result.current.sets[0].name).toBe('Jungle');
  expect(result.current.loading).toBe(false);
  expect(fetch).toHaveBeenCalledTimes(1);
  rerender({ series: '', page: 1 });
  await waitFor(() => expect(result.current.sets[0]?.name).toBe('Other'));
});
