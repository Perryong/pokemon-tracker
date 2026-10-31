import { useCallback, useEffect, useRef, useState } from 'react';
import { z } from 'zod';
import { Button } from './ui/button';

const text = z.string().max(2000);
const id = z.string().min(1).max(300);
const amount = z.string().regex(/^-?\d+(?:\.\d+)?$/).max(80);
const timestamp = z.string().datetime({ offset: true }).refine(value => Number.isFinite(Date.parse(value)));
const time = z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/);
const version = z.number().int().nonnegative().max(Number.MAX_SAFE_INTEGER);
const cardIdentity = z.object({
  set: id, number: id, language: id, printing: id, finish: id, category: z.enum(['raw', 'graded']),
  grading_company: id.nullable(), grade: id.nullable(),
}).refine(card => card.category === 'graded' ? !!card.grading_company && !!card.grade : card.grading_company === null && card.grade === null);
const evidenceSchema = z.object({
  id, source: id, basis: z.enum(['completed_sale', 'asking', 'reference']), observed_at: timestamp,
  currency: z.string().regex(/^[A-Z]{3}$/), gross_amount: amount,
});
const inventorySchema = z.object({
  units: z.array(z.object({ id, status: text, age_days: z.number().int().nonnegative(), sale_eligible: z.boolean(), cost_basis: amount })).max(1000),
  outcomes: z.array(z.object({ id, unit_id: id, realized_profit: amount.nullable(), cash_result: amount.nullable() })).max(1000),
  unsold_cost_basis: amount, realized_profit: amount, pending_outcomes: z.array(id).max(1000),
});
const scenarioValue = z.object({ gross_resale: amount, net_resale: amount, economic_ceiling: amount });
const scenariosSchema = z.object({
  mode: z.literal('simulation'), status: z.enum(['available', 'unavailable']), currency: z.literal('SGD'),
  method: z.enum(['observed_sales', 'reviewed_assumption']).nullable(),
  conservative: scenarioValue.nullable(), base: scenarioValue.nullable(), upside: scenarioValue.nullable(),
});
const stateSchema = z.object({
  mode: z.literal('simulation'), peer: z.literal('fixture'), live_ready: z.literal(false), paused: z.boolean(),
  captured_at: timestamp.optional(), next_scheduled_at: timestamp.nullable().optional(),
  scope: z.object({ policy_version: id, allowed_cards: z.array(cardIdentity).min(1).max(100), allowed_conditions: z.array(id).min(1).max(20), max_evidence_age_seconds: z.number().int().positive().max(Number.MAX_SAFE_INTEGER) }).optional(),
  sales_connection: z.object({ configured: z.boolean(), last_dispatch: z.object({ status: z.enum(['succeeded', 'failed']), at: timestamp }).nullable() }).optional(),
  schedule: z.object({ times: z.array(time).max(8), timezone: z.literal('Asia/Singapore') }),
  listings: z.array(z.object({ id, version: version.optional(), card: cardIdentity.nullable().optional(), condition: text.nullable().optional(), condition_reviewed: z.boolean().optional() })).max(1000).optional(),
  runs: z.array(z.object({ id, status: text, scheduled_for: timestamp.optional(), completed_at: timestamp.nullable().optional(), error: text.nullable().optional() })).max(1000),
  assessments: z.array(z.object({ id, listing_id: id, version: version.optional(), card: cardIdentity.nullable().optional(), condition: text.nullable().optional(), evidence: z.array(evidenceSchema).max(1000).optional(), assumption: z.object({ id, policy_version: id, reviewed_at: timestamp, expires_at: timestamp }).nullable().optional(), decision: z.enum(['qualified', 'questions_only', 'review', 'rejected']), reasons: z.array(text).max(100), pending_questions: z.array(text).max(100).optional(), expires_at: timestamp, item_ceiling: amount.nullable().optional(), scenarios: z.unknown().optional() })).max(1000),
  mandates: z.array(z.object({ id, listing_id: id, mode: z.literal('simulation'), status: z.enum(['active', 'revoked', 'expired']), expires_at: timestamp, ceiling: amount.nullable(), assessment_version: version.optional(), conversation_version: version.optional(), policy_version: id.optional(), exposure: amount.optional() })).max(1000),
  inventory: z.record(z.unknown()), blocked_reasons: z.array(text).max(100),
});
type OperationsState = z.infer<typeof stateSchema>;
const unavailable = 'Private operations unavailable. Open the configured private operator service; the public preview has no private records.';
const singaporeTime = new Intl.DateTimeFormat('en-SG', { timeZone: 'Asia/Singapore', day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });

function RecordedTime({ value }: { value: string }) {
  return <time dateTime={value}>{singaporeTime.format(new Date(value))} SGT</time>;
}

function Identity({ card }: { card: z.infer<typeof cardIdentity> | null | undefined }) {
  return <p className="market-meta">{card ? `${card.set} #${card.number} · ${card.language} · ${card.printing} · ${card.finish} · ${card.category}${card.category === 'graded' ? ` · ${card.grading_company} ${card.grade}` : ''}` : 'Exact card identity unavailable.'}</p>;
}

function InspectionSummary({ data }: { data: OperationsState }) {
  const connection = data.sales_connection;
  return <div className="operations-grid">
    <div className="operations-card"><h3>Scope and watchlist</h3>{data.scope ? <>
      <p>Policy version: {data.scope.policy_version}</p>
      <p>Allowed conditions: {data.scope.allowed_conditions.map(value => value.replace(/_/g, ' ')).join(', ')}</p>
      <details><summary>Watchlist ({data.scope.allowed_cards.length} exact cards)</summary>{data.scope.allowed_cards.map((card, index) => <Identity key={index} card={card} />)}</details>
      <p className="market-meta">Read-only synthetic policy. Geographic trading scope: not configured.</p>
    </> : <p className="market-meta">Scope unavailable from this service version.</p>}</div>
    <div className="operations-card"><h3>Connections and readiness</h3>
      <p>Discovery: seeded fixtures · available</p><p>Model: controlled test model</p><p>Live marketplace: not configured</p>
      {connection ? <><p>{connection.configured ? 'Fixture Sales transport configured' : 'Fixture Sales transport not configured'}</p>
        {connection.last_dispatch ? <p>Last recorded dispatch: {connection.last_dispatch.status} · <RecordedTime value={connection.last_dispatch.at} /></p> : <p>No dispatch evidence in recent runs.</p>}
      </> : <p>Connection evidence unavailable.</p>}
      <p className="market-meta">Configuration and historical dispatch do not prove current connectivity. Live operation is not ready.</p>
    </div>
    <div className="operations-card"><h3>Run timing</h3>
      {data.captured_at ? <p>Snapshot: <RecordedTime value={data.captured_at} /></p> : <p>Snapshot time unavailable.</p>}
      {data.paused ? <p>Scheduled work paused</p> : data.next_scheduled_at ? <p>{data.captured_at && Date.parse(data.next_scheduled_at) <= Date.parse(data.captured_at) ? 'Due scheduled slot (latest catch-up)' : 'Next scheduled slot'}: <RecordedTime value={data.next_scheduled_at} /></p> : <p>{data.schedule.times.length ? 'Schedule timing unavailable.' : 'No schedule configured.'}</p>}
      {data.runs[0] ? <p>Most recent recorded run: {data.runs[0].status}{data.runs[0].scheduled_for && <> · <RecordedTime value={data.runs[0].scheduled_for} /></>}</p> : <p>No runs recorded.</p>}
      <p className="market-meta">Refresh operations to update this snapshot. The worker catches up only the latest missed scheduled slot.</p>
    </div>
  </div>;
}

function AssessmentEvidence({ assessment, data }: { assessment: OperationsState['assessments'][number]; data: OperationsState }) {
  return <details><summary>Assessment evidence ({assessment.evidence?.length ?? 0})</summary>
    <p className="market-meta">Synthetic business evidence. Freshness is measured at the displayed snapshot; it does not turn reference or asking prices into completed sales.</p>
    <ul className="operations-records">{assessment.evidence?.map(item => {
      const age = data.captured_at ? (Date.parse(data.captured_at) - Date.parse(item.observed_at)) / 1000 : undefined;
      const freshness = age === undefined || !data.scope ? 'Freshness unavailable' : age < 0 ? 'Future observation at snapshot' : age <= data.scope.max_evidence_age_seconds ? 'Fresh at snapshot' : 'Stale at snapshot';
      return <li key={item.id}><strong>{item.id} · {item.source}</strong><p>{item.currency} {item.gross_amount} · {item.basis.replace(/_/g, ' ')}</p><p>Observed: <RecordedTime value={item.observed_at} /></p><p>{freshness}</p></li>;
    })}</ul>
    {!assessment.evidence?.length && <p>No comparable evidence recorded.</p>}
    {assessment.assumption && <><p>Reviewed assumption: {assessment.assumption.id} · Policy {assessment.assumption.policy_version}</p><p>Reviewed: <RecordedTime value={assessment.assumption.reviewed_at} /></p><Expiry value={assessment.assumption.expires_at} /></>}
  </details>;
}

function Expiry({ value }: { value: string }) {
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    const expiry = Date.parse(value);
    if (expiry <= now) return;
    const timer = setTimeout(() => setNow(Date.now()), Math.min(Math.max(0, expiry - Date.now()), 2147483647));
    return () => clearTimeout(timer);
  }, [value, now]);
  return <p className="market-meta" aria-live="polite">{Date.parse(value) <= now ? 'Expired' : 'Expires'}: <time dateTime={value}>{value}</time></p>;
}

function ScenarioComparison({ value, listingId }: { value: unknown; listingId: string }) {
  const parsed = scenariosSchema.safeParse(value);
  if (!parsed.success || parsed.data.status !== 'available' || !parsed.data.conservative || !parsed.data.base || !parsed.data.upside) {
    return <p className="market-meta">Scenario comparison unavailable.</p>;
  }
  const scenarios = parsed.data;
  return <div className="operations-scenarios">
    <table><caption>{listingId} scenario comparison · SGD</caption>
      <thead><tr><th scope="col">Scenario</th><th scope="col">Gross resale</th><th scope="col">Net resale</th><th scope="col">Economic ceiling</th></tr></thead>
      <tbody>{(['conservative', 'base', 'upside'] as const).map(name => <tr key={name}><th scope="row">{name[0].toUpperCase() + name.slice(1)}</th><td>{scenarios[name]!.gross_resale}</td><td>{scenarios[name]!.net_resale}</td><td>{scenarios[name]!.economic_ceiling}</td></tr>)}</tbody>
    </table>
    <p className="market-meta">Simulation · Method: {scenarios.method?.replace('_', ' ') ?? 'unavailable'}. Descriptive upper scenarios do not raise the current mandate ceiling.</p>
  </div>;
}

export default function MarketOperations() {
  const [data, setData] = useState<OperationsState | null>(null);
  const [auth, setAuth] = useState(false);
  const [token, setToken] = useState('');
  const [times, setTimes] = useState('');
  const [listing, setListing] = useState('');
  const [loading, setLoading] = useState(true);
  const [mutating, setMutating] = useState(false);
  const [stale, setStale] = useState(false);
  const [error, setError] = useState('');
  const generation = useRef(0);
  const controller = useRef<AbortController>();
  const mutationLock = useRef(false);

  const request = useCallback(async (operation = 'state', body?: object) => {
    if (mutationLock.current) return;
    const mutation = operation !== 'state';
    mutationLock.current = mutation;
    controller.current?.abort();
    const version = ++generation.current;
    const abort = new AbortController();
    controller.current = abort;
    setLoading(true); setMutating(mutation); setError('');
    const timer = setTimeout(() => abort.abort(), 12000);
    const current = () => version === generation.current && !abort.signal.aborted;
    const send = async (path: string, payload?: object) => {
      const response = await fetch(`/api/operations/${path}`, {
        credentials: 'same-origin', cache: 'no-store', signal: abort.signal,
        ...(payload !== undefined ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) } : {}),
      });
      if (!response.ok) throw response.status;
      return response;
    };
    try {
      if (mutation) {
        await send(operation, body ?? {});
        if (!current()) return;
        if (operation === 'logout') { setData(null); setAuth(true); setStale(false); return; }
      }
      const response = await send('state');
      const parsed = stateSchema.parse(await response.json());
      if (!current()) return;
      setData(parsed); setAuth(false); setStale(false);
      setTimes(parsed.schedule.times.join(', '));
      setListing(previous => parsed.listings?.some(item => item.id === previous) ? previous : parsed.listings?.[0]?.id ?? '');
    } catch (failure) {
      if (version !== generation.current) return;
      if (failure === 401) {
        setData(null); setAuth(true); setStale(false);
        if (operation === 'login') setError('Access key rejected. Try again.');
      } else if (failure === 404 || failure === 503 || operation === 'state' || operation === 'login') {
        setData(null); setAuth(false); setError(unavailable);
      } else { setStale(true); setError('Operation failed. Its outcome is unconfirmed. Refresh operations before continuing.'); }
    } finally {
      clearTimeout(timer);
      if (version === generation.current) { mutationLock.current = false; setLoading(false); setMutating(false); }
    }
  }, []);

  useEffect(() => {
    void request();
    // Invalidate request generations on unmount; this ref is a counter, not a DOM node.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    return () => { generation.current++; controller.current?.abort(); mutationLock.current = false; };
  }, [request]);

  const disabled = loading || stale;
  const inventory = inventorySchema.safeParse(data?.inventory);
  const selectedListing = data?.listings?.find(item => item.id === listing);
  function saveSchedule() {
    const selected = times.split(',').map(value => value.trim());
    if (!selected.length || selected.length > 8 || new Set(selected).size !== selected.length || selected.some(value => !time.safeParse(value).success)) {
      setError('Enter 1–8 unique times in HH:MM format, separated by commas.'); return;
    }
    void request('schedule', { times: selected, timezone: 'Asia/Singapore' });
  }

  return <section className="market-operations" aria-label="Private Market operations" aria-busy={loading}>
    <div className="operations-heading"><div><h2>Private Market operations</h2><p className="market-meta">Simulation only. No live trading permission, seller contact or completed-sale evidence is supplied by this panel.</p></div>
      <Button type="button" variant="outline" disabled={mutating} onClick={() => void request()}>Refresh operations</Button>
    </div>
    {loading && <p role="status" className="market-meta">Loading private operations…</p>}
    {error && <p role="alert" className="alert-message">{error}</p>}
    {auth && <form aria-label="Private operations login" className="operations-form" onSubmit={event => { event.preventDefault(); if (token && token.length <= 512) { void request('login', { token }); setToken(''); } }}>
      <div className="filter-field grow"><label htmlFor="operations-key">Access key</label><input id="operations-key" className="control" type="password" value={token} autoComplete="off" maxLength={512} required disabled={loading} onChange={event => setToken(event.target.value)} /></div>
      <Button type="submit" disabled={loading || !token}>Unlock operations</Button>
    </form>}
    {data && <>
      <p className="operations-mode">Simulation · fixture Sales peer</p>
      {stale && <p role="status" className="market-previous">Previous operations state — refresh to confirm the latest result.</p>}
      <div className="operations-actions">
        <Button type="button" disabled={disabled} onClick={() => void request('pause', { paused: !data.paused })}>{data.paused ? 'Resume schedule' : 'Pause schedule'}</Button>
        <Button type="button" disabled={disabled || data.paused} onClick={() => void request('run', {})}>Run due work</Button>
        <Button type="button" variant="outline" disabled={loading} onClick={() => void request('logout', {})}>Log out of operations</Button>
      </div>
      <p className="market-meta">Schedule {data.paused ? 'paused' : 'running'}. Run due work processes scheduled work that is due.</p>
      <InspectionSummary data={data} />
      <div className="operations-grid">
        <form aria-label="Operations schedule" className="operations-card" onSubmit={event => { event.preventDefault(); if (!disabled) saveSchedule(); }}>
          <h3>Schedule</h3><p className="market-meta">Timezone: <span>Asia/Singapore</span></p>
          <label htmlFor="operations-times">Run times</label><input id="operations-times" className="control" value={times} maxLength={62} disabled={loading} aria-describedby="operations-times-help" onChange={event => setTimes(event.target.value)} />
          <p id="operations-times-help" className="market-meta">Up to 8 unique HH:MM times, separated by commas.</p>
          <Button type="submit" disabled={disabled}>Save schedule</Button>
        </form>
        <form aria-label="Assess listing" className="operations-card" onSubmit={event => { event.preventDefault(); if (!disabled && !data.paused && data.listings?.some(item => item.id === listing)) void request('assess', { listing_id: listing }); }}>
          <h3>Assess a listing</h3><label htmlFor="operations-listing">Listing to assess</label>
          <select id="operations-listing" className="control" value={listing} disabled={loading || data.paused || !data.listings?.length} onChange={event => setListing(event.target.value)}>{!data.listings?.length && <option value="">No listings available</option>}{data.listings?.map(item => <option key={item.id} value={item.id}>{item.id}</option>)}</select>
          {selectedListing && <><Identity card={selectedListing.card} /><p className="market-meta">Current listing version: {selectedListing.version ?? 'unavailable'}</p><p className="market-meta">Current condition: {selectedListing.condition?.replace(/_/g, ' ') ?? 'unknown'} · {selectedListing.condition_reviewed === true ? 'reviewed' : selectedListing.condition_reviewed === false ? 'unreviewed' : 'review status unavailable'}</p></>}
          <Button type="submit" disabled={disabled || data.paused || !listing}>Assess selected listing</Button>
        </form>
      </div>
      <div className="operations-grid">
        <div className="operations-card"><h3>Runs</h3>{!data.runs.length && <p className="market-meta">No runs recorded.</p>}<ul className="operations-records">{data.runs.map(run => <li key={run.id}><strong>{run.id}</strong><p>{run.status} · simulation</p>{run.scheduled_for && <p className="market-meta">Scheduled: <time dateTime={run.scheduled_for}>{run.scheduled_for}</time></p>}{run.completed_at && <p className="market-meta">Completed: <time dateTime={run.completed_at}>{run.completed_at}</time></p>}{run.error && <p>Run failed: {run.error}</p>}</li>)}</ul></div>
        <div className="operations-card"><h3>Assessments</h3>{!data.assessments.length && <p className="market-meta">No assessments recorded.</p>}<ul className="operations-records">{data.assessments.map(assessment => <li key={assessment.id}><strong>{assessment.listing_id}</strong><p>Decision: {assessment.decision.replace('_', ' ')}</p><p className="market-meta">Assessment version: {assessment.version ?? 'unavailable'}</p><Identity card={assessment.card} /><p className="market-meta">Assessed condition: {assessment.condition?.replace(/_/g, ' ') ?? 'unknown'}</p>{assessment.item_ceiling != null && <p>Simulated item ceiling: {assessment.item_ceiling}</p>}<Expiry value={assessment.expires_at} /><AssessmentEvidence assessment={assessment} data={data} /><ScenarioComparison value={assessment.scenarios} listingId={assessment.listing_id} /><ul>{assessment.reasons.map((reason, index) => <li key={index}>{reason}</li>)}{assessment.pending_questions?.map((question, index) => <li key={`q-${index}`}>{question}</li>)}</ul></li>)}</ul></div>
        <div className="operations-card"><h3>Mandates</h3>{!data.mandates.length && <p className="market-meta">No mandates recorded.</p>}<ul className="operations-records">{data.mandates.map(mandate => <li key={mandate.id}><strong>{mandate.listing_id}</strong><p>{mandate.ceiling === null ? 'Questions only · no price authority' : `Simulated price ceiling: ${mandate.ceiling}`}</p><p className="market-meta">Assessment {mandate.assessment_version ?? 'unavailable'} · Conversation {mandate.conversation_version ?? 'unavailable'} · Policy {mandate.policy_version ?? 'unavailable'}</p><p className="market-meta">Recorded status: {mandate.status}</p>{mandate.exposure !== undefined && <p className="market-meta">Simulated exposure: SGD {mandate.exposure}</p>}<Expiry value={mandate.expires_at} /></li>)}</ul></div>
        <div className="operations-card"><h3>Fixture inventory and outcomes</h3>{inventory.success ? <><p className="market-meta">Unsold cost basis: {inventory.data.unsold_cost_basis} · Realized fixture profit: {inventory.data.realized_profit}</p><ul className="operations-records">{inventory.data.units.map(unit => <li key={unit.id}><strong>{unit.id}</strong><p>{unit.status} · <span>{unit.age_days} days</span></p><p>{unit.sale_eligible ? 'Fixture sale eligible' : 'Not sale eligible'}</p><p className="market-meta">Cost basis: {unit.cost_basis}</p></li>)}{inventory.data.outcomes.map(outcome => <li key={outcome.id}><strong>{outcome.unit_id}</strong><p>{outcome.realized_profit === null || outcome.cash_result === null ? 'Outcome pending · no reconciled result' : `Fixture profit: ${outcome.realized_profit} · Cash result: ${outcome.cash_result}`}</p></li>)}</ul>{inventory.data.pending_outcomes.length > 0 && <p className="market-meta">Pending outcomes: {inventory.data.pending_outcomes.join(', ')}</p>}{!inventory.data.units.length && <p className="market-meta">No inventory recorded.</p>}</> : <p className="market-meta">Inventory summary unavailable.</p>}</div>
      </div>
      <div className="operations-card"><h3>Blocked reasons</h3>{data.blocked_reasons.length ? <ul>{data.blocked_reasons.map((reason, index) => <li key={index}>{reason}</li>)}</ul> : <p className="market-meta">No additional blockers reported. Simulation restrictions still apply.</p>}</div>
    </>}
  </section>;
}
