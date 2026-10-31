import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import MarketOperations from '../MarketOperations';
import MarketView from '../MarketView';
import userEvent from '@testing-library/user-event';

vi.mock('@/lib/exchange-rate', async () => ({ ...await vi.importActual('@/lib/exchange-rate'), useSgdExchangeRates: () => ({ rates: {}, errors: {} }) }));

const state = () => ({
  mode: 'simulation', peer: 'fixture', live_ready: false, paused: false,
  schedule: { times: ['09:00', '18:00'], timezone: 'Asia/Singapore' },
  listings: [{ id: 'listing-1' }, { id: 'listing-2' }],
  runs: [{ id: 'run-1', status: 'completed', scheduled_for: '2026-10-31T01:00:00Z' }],
  assessments: [{ id: 'assessment-1', listing_id: 'listing-1', decision: 'questions_only', reasons: ['Condition missing'], pending_questions: ['Which condition?'], expires_at: '2026-01-01T00:00:00Z' }],
  mandates: [{ mode: 'simulation', id: 'mandate-1', listing_id: 'listing-1', status: 'active', expires_at: '2026-01-01T00:00:00Z', ceiling: null }],
  inventory: { units: [{ id: 'unit-1', status: 'quarantined', age_days: 12, sale_eligible: false, cost_basis: '20.00' }], outcomes: [{ id: 'outcome-1', unit_id: 'unit-1', realized_profit: null, cash_result: null }], unsold_cost_basis: '20.00', realized_profit: '0.00', pending_outcomes: ['unit-1'] },
  blocked_reasons: ['Real peer pending'],
});
const response = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status });
const submit = (name: string) => fireEvent.submit(screen.getByRole('form', { name }));
beforeEach(() => vi.stubGlobal('fetch', vi.fn(async () => response(state()))));
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks(); });

it('requires a password access key on 401 and clears it after cookie login without storing it', async () => {
  const store = vi.spyOn(Storage.prototype, 'setItem');
  vi.mocked(fetch).mockResolvedValueOnce(response({}, 401));
  render(<MarketOperations />);
  const key = await screen.findByLabelText('Access key');
  expect(key).toHaveAttribute('type', 'password');
  fireEvent.change(key, { target: { value: 'secret-test-key' } });
  submit('Private operations login');
  await screen.findByRole('button', { name: 'Pause schedule' });
  expect(key).toHaveValue('');
  expect(fetch).toHaveBeenCalledWith('/api/operations/login', expect.objectContaining({ credentials: 'same-origin', method: 'POST', body: JSON.stringify({ token: 'secret-test-key' }) }));
  expect(store).not.toHaveBeenCalled();
  expect(document.body).not.toHaveTextContent('secret-test-key');
});

it.each([404, 503])('explains unavailable operations (%s) without showing fixture records', async status => {
  vi.mocked(fetch).mockResolvedValueOnce(response({}, status));
  render(<MarketOperations />);
  expect(await screen.findByRole('alert')).toHaveTextContent('Private operations unavailable');
  expect(screen.queryByRole('button', { name: 'Run due work' })).not.toBeInTheDocument();
  expect(screen.queryByText('listing-1')).not.toBeInTheDocument();
});

it('shows truthful simulation, expired questions-only authority and inventory ageing/outcomes', async () => {
  render(<MarketOperations />);
  await screen.findByText('Simulation · fixture Sales peer');
  expect(screen.getByText(/No live trading permission/)).toBeInTheDocument();
  expect(screen.getByText('Questions only · no price authority')).toBeInTheDocument();
  expect(screen.getAllByText(/Expired/).length).toBeGreaterThan(0);
  expect(screen.getByText('Which condition?')).toBeInTheDocument();
  expect(screen.getByText('12 days')).toBeInTheDocument();
  expect(screen.getByText('Not sale eligible')).toBeInTheDocument();
  expect(screen.getByText(/Outcome pending/)).toBeInTheDocument();
  expect(screen.getByText('Real peer pending')).toBeInTheDocument();
});

it('saves bounded Singapore schedule times and rejects malformed or duplicate times locally', async () => {
  render(<MarketOperations />); const times = await screen.findByLabelText('Run times');
  expect(times).toHaveValue('09:00, 18:00');
  expect(screen.getByText('Asia/Singapore')).toBeInTheDocument();
  for (const invalid of ['25:00', '9:00', '09:00, 09:00', Array(9).fill('12:00').join(',')]) {
    fireEvent.change(times, { target: { value: invalid } }); submit('Operations schedule');
    expect(await screen.findByRole('alert')).toHaveTextContent('Enter 1–8 unique times');
  }
  expect(fetch).toHaveBeenCalledTimes(1);
  fireEvent.change(times, { target: { value: '08:30, 21:00' } }); submit('Operations schedule');
  await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/operations/schedule', expect.objectContaining({ body: JSON.stringify({ times: ['08:30', '21:00'], timezone: 'Asia/Singapore' }) })));
});

it('pauses, resumes, runs due work and assesses only a listed selection with cookie requests', async () => {
  render(<MarketOperations />); await screen.findByRole('button', { name: 'Pause schedule' });
  vi.mocked(fetch).mockResolvedValueOnce(response({})).mockResolvedValueOnce(response({ ...state(), paused: true }));
  fireEvent.click(screen.getByRole('button', { name: 'Pause schedule' }));
  await screen.findByRole('button', { name: 'Resume schedule' });
  expect(fetch).toHaveBeenCalledWith('/api/operations/pause', expect.objectContaining({ body: '{"paused":true}' }));
  fireEvent.click(screen.getByRole('button', { name: 'Resume schedule' }));
  await screen.findByRole('button', { name: 'Pause schedule' });
  fireEvent.click(screen.getByRole('button', { name: 'Run due work' }));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Run due work' })).toBeEnabled());
  fireEvent.change(screen.getByLabelText('Listing to assess'), { target: { value: 'listing-2' } });
  submit('Assess listing');
  await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/operations/assess', expect.objectContaining({ method: 'POST', credentials: 'same-origin', body: '{"listing_id":"listing-2"}' })));
  expect(fetch).toHaveBeenCalledWith('/api/operations/run', expect.objectContaining({ body: '{}' }));
});

it('blocks double submissions while a mutation is pending', async () => {
  render(<MarketOperations />); const run = await screen.findByRole('button', { name: 'Run due work' });
  let finish!: (response: Response) => void;
  vi.mocked(fetch).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  fireEvent.click(run); fireEvent.click(run);
  expect(run).toBeDisabled();
  expect(fetch).toHaveBeenCalledTimes(2);
  await act(async () => finish(response({})));
  await waitFor(() => expect(run).toBeEnabled());
});

it('ignores stale refresh responses even when transport ignores abort', async () => {
  render(<MarketOperations />); await screen.findByRole('button', { name: 'Pause schedule' });
  let finish!: (response: Response) => void;
  vi.mocked(fetch).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  fireEvent.click(screen.getByRole('button', { name: 'Refresh operations' }));
  vi.mocked(fetch).mockResolvedValueOnce(response({ ...state(), paused: true }));
  fireEvent.click(screen.getByRole('button', { name: 'Refresh operations' }));
  await screen.findByRole('button', { name: 'Resume schedule' });
  await act(async () => finish(response(state())));
  expect(screen.getByRole('button', { name: 'Resume schedule' })).toBeInTheDocument();
});

it('announces failed mutations without reflecting server secrets and marks old records stale', async () => {
  render(<MarketOperations />); await screen.findByRole('button', { name: 'Run due work' });
  vi.mocked(fetch).mockResolvedValueOnce(response({ error: 'private-token-value' }, 500));
  fireEvent.click(screen.getByRole('button', { name: 'Run due work' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Operation failed');
  expect(screen.getByText(/Previous operations state/)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Run due work' })).toBeDisabled();
  expect(document.body).not.toHaveTextContent('private-token-value');
});

it('clears private records on expired authentication and logs out through the cookie endpoint', async () => {
  render(<MarketOperations />); await screen.findByRole('button', { name: 'Log out of operations' });
  fireEvent.click(screen.getByRole('button', { name: 'Log out of operations' }));
  await screen.findByLabelText('Access key');
  expect(fetch).toHaveBeenCalledWith('/api/operations/logout', expect.objectContaining({ method: 'POST', credentials: 'same-origin' }));
  expect(screen.queryByText('Real peer pending')).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Access key'), { target: { value: 'again' } }); submit('Private operations login');
  await screen.findByRole('button', { name: 'Refresh operations' });
  vi.mocked(fetch).mockResolvedValueOnce(response({}, 401));
  fireEvent.click(screen.getByRole('button', { name: 'Refresh operations' }));
  await screen.findByLabelText('Access key');
  expect(screen.queryByText('Real peer pending')).not.toBeInTheDocument();
});

it('fails closed for malformed/live states, supports missing inventory and disables absent listings', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(response({ ...state(), mode: 'live', live_ready: true }));
  render(<MarketOperations />); expect(await screen.findByRole('alert')).toHaveTextContent('Private operations unavailable');
  vi.mocked(fetch).mockResolvedValueOnce(response({ ...state(), inventory: {}, listings: [] }));
  fireEvent.click(screen.getByRole('button', { name: 'Refresh operations' }));
  await screen.findByText('Inventory summary unavailable.');
  expect(screen.getByRole('button', { name: 'Assess selected listing' })).toBeDisabled();
});


it('keeps public reference lookup usable and opens private operations only on request', async () => {
  render(<MarketView />);
  expect(screen.getByRole('form', { name: 'Price lookup' })).toBeInTheDocument();
  expect(fetch).not.toHaveBeenCalledWith('/api/operations/state', expect.anything());
  fireEvent.click(screen.getByRole('button', { name: 'Open private operations' }));
  await screen.findByRole('button', { name: 'Pause schedule' });
  expect(screen.getByRole('form', { name: 'Price lookup' })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Close private operations' }));
  expect(screen.queryByRole('region', { name: 'Private Market operations' })).not.toBeInTheDocument();
});

it('supports keyboard login and clears failed credentials without displaying them', async () => {
  const user = userEvent.setup();
  vi.mocked(fetch).mockResolvedValue(response({}, 401));
  render(<MarketOperations />);
  const key = await screen.findByLabelText('Access key');
  key.focus(); await user.type(key, 'wrong-key'); await user.tab();
  expect(screen.getByRole('button', { name: 'Unlock operations' })).toHaveFocus();
  await user.keyboard('{Enter}');
  expect(await screen.findByRole('alert')).toHaveTextContent('Access key rejected');
  expect(key).toHaveValue('');
  expect(document.body).not.toHaveTextContent('wrong-key');
});

it('aborts pending requests on unmount and ignores their late responses', async () => {
  let finish!: (response: Response) => void;
  vi.mocked(fetch).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const { unmount } = render(<MarketOperations />);
  const signal = vi.mocked(fetch).mock.calls[0][1]?.signal;
  unmount(); expect(signal?.aborted).toBe(true);
  await act(async () => finish(response(state())));
  expect(screen.queryByText('Real peer pending')).not.toBeInTheDocument();
});

it('compares scenario amounts without changing the recorded mandate ceiling', async () => {
  const data = state();
  vi.mocked(fetch).mockResolvedValueOnce(response({ ...data,
    assessments: [{ ...data.assessments[0], scenarios: {
      mode: 'simulation', status: 'available', currency: 'SGD', method: 'observed_sales', assessment: data.assessments[0],
      conservative: { gross_resale: '90.00', net_resale: '80.00', economic_ceiling: '70.00' },
      base: { gross_resale: '100.00', net_resale: '90.00', economic_ceiling: '80.00' },
      upside: { gross_resale: '120.00', net_resale: '110.00', economic_ceiling: '100.00' },
    } }],
    mandates: [{ ...data.mandates[0], ceiling: '50.00' }],
  }));
  render(<MarketOperations />);
  const table = await screen.findByRole('table', { name: 'listing-1 scenario comparison · SGD' });
  expect(table).toHaveTextContent('Conservative90.0080.0070.00');
  expect(table).toHaveTextContent('Base100.0090.0080.00');
  expect(table).toHaveTextContent('Upside120.00110.00100.00');
  expect(screen.getByText('Simulated price ceiling: 50.00')).toBeInTheDocument();
  expect(screen.getByText(/Descriptive upper scenarios do not raise the current mandate ceiling/)).toBeInTheDocument();
});

it.each([undefined, { mode: 'simulation', status: 'unavailable', currency: 'SGD', method: null, conservative: null, base: null, upside: null, assessment: {} }])('explains absent or unavailable scenarios without invented amounts (%s)', async scenarios => {
  const data = state();
  vi.mocked(fetch).mockResolvedValueOnce(response({ ...data, assessments: [{ ...data.assessments[0], scenarios }] }));
  render(<MarketOperations />);
  expect(await screen.findByText('Scenario comparison unavailable.')).toBeInTheDocument();
  expect(screen.queryByRole('table', { name: /scenario comparison/ })).not.toBeInTheDocument();
  expect(screen.getByText('Questions only · no price authority')).toBeInTheDocument();
});

it('shows the durable sanitized run failure instead of directing operators to nonexistent private logs', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(response({ ...state(), runs: [{ id: 'run-failed', status: 'failed', error: 'fixture_peer_unavailable' }] }));
  render(<MarketOperations />);
  expect(await screen.findByText('Run failed: fixture_peer_unavailable')).toBeInTheDocument();
  expect(screen.queryByText(/review the private service log/)).not.toBeInTheDocument();
});

it('accepts the backend contract’s 300-character IDs without hiding valid operations or inventory', async () => {
  const data = state(); const longId = 'x'.repeat(300);
  vi.mocked(fetch).mockResolvedValueOnce(response({ ...data, listings: [{ id: longId }],
    assessments: [{ ...data.assessments[0], id: longId, listing_id: longId }],
    mandates: [{ ...data.mandates[0], id: longId, listing_id: longId }],
    inventory: { ...data.inventory, units: [{ ...data.inventory.units[0], id: longId }] },
  }));
  render(<MarketOperations />);
  expect(await screen.findByRole('option', { name: longId })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Assess selected listing' })).toBeEnabled();
  expect(screen.getByText('12 days')).toBeInTheDocument();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

it('prevents manual assessment while the backend is paused', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(response({ ...state(), paused: true }));
  render(<MarketOperations />);
  await screen.findByRole('button', { name: 'Resume schedule' });
  expect(screen.getByRole('button', { name: 'Assess selected listing' })).toBeDisabled();
  submit('Assess listing');
  expect(fetch).toHaveBeenCalledTimes(1);
});

it('updates expiry at its boundary while idle and cleans up its timers on unmount', async () => {
  vi.useFakeTimers();
  try {
    vi.setSystemTime(new Date('2026-10-31T00:00:00Z'));
    const data = state(); const expires = '2026-10-31T00:00:01Z';
    vi.mocked(fetch).mockResolvedValueOnce(response({ ...data,
      assessments: [{ ...data.assessments[0], expires_at: expires }],
      mandates: [{ ...data.mandates[0], expires_at: expires }],
    }));
    let unmount!: () => void;
    await act(async () => { unmount = render(<MarketOperations />).unmount; });
    expect(screen.getAllByText(/Expires:/)).toHaveLength(2);
    await act(async () => { vi.advanceTimersByTime(1000); });
    expect(screen.getAllByText(/Expired:/)).toHaveLength(2);
    expect(screen.queryByText(/Expires:/)).not.toBeInTheDocument();
    unmount(); expect(vi.getTimerCount()).toBe(0);
  } finally { vi.useRealTimers(); }
});
