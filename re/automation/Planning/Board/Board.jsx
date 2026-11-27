import React, { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './Board.css';

const data = window.KitPlanning;
const day = 86400000;
const stamp = value => Date.parse(value + 'T00:00:00Z');
const plain = value => typeof value === 'string' ? value : JSON.stringify(value, null, 2);

function promptFor(item) {
  return `use standard-pr-practice to investigate scope ${item.Id}: ${item.Name}

refresh main, live GitHub Project ownership, open PRs and the owning register before claiming work
do not start if another owner holds this scope or its prerequisites are unqualified
use a fresh feat/ or fix/ branch and the task's isolated registered checkout
read AGENTS.md, Documentation/Planning/README.md and the owning source: ${item.Source}
for CAD work read Documentation/Reference/Operations/CadSuccessCriteria.md and re/Playbook/README.md in full plus the applicable phase chapters
claim the task with owner, branch, dependencies, resource lease, delivery PR and exit condition
set native Assignees on the project item and delivery PR; record Agent and Runner
set native project Status to In Progress before starting and Done only after exact exit evidence; retain assignees
do not restart completed scopes; claim a bounded follow-up child if needed
reuse the existing research controller, CAD API workers and deterministic research CLI
inspect existing evidence before choosing missing contrasts; retain controls, independent holdouts, failures, documents and receipts
models stay off for research execution unless explicitly authorized
coordinate shared native oracles; no donor data or proprietary binaries may be committed
prove decoder rules from recorded evidence and counterexamples; keep decoding, semantics, writing and native acceptance separate
exit condition: ${plain(item.Exit)}
window: ${item.Start || 'unscheduled'} to ${item.Finish || 'unscheduled'} (${item.ScheduleKind})
update the owning register, project claim, scope links and generated planning views with exact revision evidence
open a scoped PR and address its configured reviews; do not merge without explicit administrator authorization`;
}

function Board() {
  const [query, setQuery] = useState('');
  const [area, setArea] = useState('All');
  const [kind, setKind] = useState('All');
  const [owner, setOwner] = useState('All');
  const [status, setStatus] = useState('All');
  const [mode, setMode] = useState('Current work');
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState(null);
  const [draft, setDraft] = useState(data.Links);
  const [notice, setNotice] = useState('');
  const [zoom, setZoom] = useState(180);
  const items = useMemo(() => data.Items.map(item => {
    const schedule = draft.Schedules.find(value => value.TaskId === item.Id);
    return schedule ? { ...item, Start: schedule.Start, Finish: schedule.Finish, ScheduleKind: 'Draft supplied window' } : item;
  }), [draft]);
  const filtered = items.filter(item => (area === 'All' || item.Area === area) &&
    (kind === 'All' || item.Kind === kind) && (status === 'All' || item.Status.toLowerCase() === status) && (owner === 'All' || item.Owner === owner) &&
    (mode !== 'SDK' || item.Area === 'SDK') &&
    (mode !== 'Scope inventory' || ['Decoding scope', 'API declaration', 'Native decoding domain'].includes(item.Kind)) &&
    (mode !== 'Current work' || ['active', 'checking', 'open'].includes(item.Status.toLowerCase())) &&
    `${item.Id} ${item.Name} ${item.Owner} ${item.Status}`.toLowerCase().includes(query.toLowerCase()));
  const visible = filtered.slice(page * 40, (page + 1) * 40);
  const start = stamp(data.Links.SchedulePolicy.Start);
  const end = zoom === 0 ? Math.max(start + 30 * day, ...filtered.map(item => item.Finish ? stamp(item.Finish) + day : start)) : start + zoom * day;
  const current = selected && items.find(item => item.Id === selected);
  const today = new Date().toISOString().slice(0, 10);
  const eligible = current && (!current.Start || current.Start <= today && current.Finish >= today) && current.Owner.startsWith('Unassigned') && current.Dependencies.length === 0;

  async function copyPrompt(item, target = "chosen agent") {
    try { await navigator.clipboard.writeText(`Target runner: ${target}\n\n${promptFor(item)}`); setNotice('Prompt copied; recipient must recheck ownership before claiming'); }
    catch { setNotice('Clipboard unavailable — select the prompt below and copy it'); }
  }

  function saveWindow(event) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    const entry = { TaskId: current.Id, Start: values.get('start'), Finish: values.get('finish'), Basis: values.get('basis') };
    if (entry.Finish < entry.Start) { setNotice('Finish must be on or after start'); return; }
    setDraft({ ...draft, Schedules: [...draft.Schedules.filter(value => value.TaskId !== current.Id), entry] });
    setNotice('Draft window updated — export Links.json and regenerate to persist in the repo');
  }

  function exportPlan() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(draft, null, 2) + '\n'], { type: 'application/json' }));
    const link = document.createElement('a'); link.href = url; link.download = 'Links.json'; link.click(); URL.revokeObjectURL(url);
    setNotice('Downloaded Links.json; review and apply it to Documentation/Planning before regenerating');
  }

  return <main>
    <header><h1>Kit planning</h1><button onClick={exportPlan}>Export schedule changes</button></header>
    <p><a href="https://github.com/orgs/TryUniCAD/projects/1">Open shared GitHub project</a></p>
    <p className="context">{data.Items.length} tracked entries · observed {data.ObservedOn} · scope, status and ownership · dates only where explicitly scheduled</p>
    <nav aria-label="Planning views">{['Schedule', 'Current work', 'Scope inventory', 'SDK'].map(value => <button key={value} aria-pressed={mode === value} onClick={() => { setMode(value); setKind(value === 'Current work' || value === 'Scope inventory' || value === 'SDK' ? 'All' : 'Milestone'); setPage(0); }}>{value}</button>)}</nav>
    <div className="filters">
      <label>Search scopes<input type="search" maxLength={200} value={query} onChange={event => { setQuery(event.target.value); setPage(0); }} placeholder="Feature, task or owner" /></label>
      <label>Area<select value={area} onChange={event => { setArea(event.target.value); setPage(0); }}>{['All', ...new Set(items.map(item => item.Area))].map(value => <option key={value}>{value}</option>)}</select></label>
      <label>Type<select value={kind} onChange={event => { setKind(event.target.value); setPage(0); }}>{['All', ...new Set(items.map(item => item.Kind))].map(value => <option key={value}>{value}</option>)}</select></label>
      <label>Owner / PR contact<select value={owner} onChange={event => { setOwner(event.target.value); setPage(0); }}>{['All', ...new Set(items.map(item => item.Owner))].map(value => <option key={value}>{value}</option>)}</select></label>
      <label>Recorded state<select value={status} onChange={event => { setStatus(event.target.value); setPage(0); }}>{['All', ...new Set(items.map(item => item.Status.toLowerCase()))].map(value => <option key={value} value={value}>{value === 'complete' ? 'Done (recorded scope)' : value === 'active' || value === 'checking' || value === 'open' ? 'In progress / ' + value : value}</option>)}</select></label>
      <label>Timeline<select value={zoom} onChange={event => setZoom(Number(event.target.value))}><option value={90}>Quarter</option><option value={180}>Six months</option><option value={365}>Year</option><option value={0}>Fit filtered work</option></select></label>
    </div>
    <p className="context">{filtered.length} matching entries · PR authors are contacts · unverified scopes require an ownership check · UI/UX entries are proposals</p>
    <div className="timeline" role="region" aria-label="Scheduled scopes" tabIndex={0}>
      <div className="row heading"><div>Scope / recorded owner</div><div className="months">{Array.from({ length: 6 }, (_, index) => <span key={index}>{new Date(start + (end - start) * index / 6).toLocaleDateString('en-GB', { month: 'short', year: '2-digit', timeZone: 'UTC' })}</span>)}</div></div>
      {visible.map(item => {
        const left = item.Start ? (stamp(item.Start) - start) / (end - start) * 100 : 0;
        const width = item.Start ? Math.max(0.5, (stamp(item.Finish) - stamp(item.Start) + day) / (end - start) * 100) : 0;
        return <button className="row task" key={item.Id} onClick={() => setSelected(item.Id)} aria-label={`Open ${item.Name}`}>
          <div className="task-name"><strong>{item.Name}</strong><span>{item.Id} · {item.Status} · {item.Owner}</span></div>
          <div className="track">{!item.Start ? <span className="unscheduled">Unscheduled</span> : left > 100 ? <span className="unscheduled">{item.Start} — use Fit filtered work</span> : <span title={`${item.Start} → ${item.Finish}: ${item.ScheduleKind}`} className={`bar ${item.Status.toLowerCase()}`} style={{ left: `${left}%`, width: `${Math.min(width, 100 - left)}%` }}>{width > 9 ? item.Start : ''}</span>}</div>
        </button>;
      })}
      {!visible.length && <p>No matching scopes — change the filters</p>}
    </div>
    <footer><button disabled={page === 0} onClick={() => setPage(page - 1)}>Previous</button><span>Page {page + 1} of {Math.max(1, Math.ceil(filtered.length / 40))}</span><button disabled={(page + 1) * 40 >= filtered.length} onClick={() => setPage(page + 1)}>Next</button></footer>
    <p role="status">{notice}</p>
    {current && <section className="details" aria-label="Scope details">
      <div className="detail-heading"><h2>{current.Name}</h2><button onClick={() => setSelected(null)}>Close details</button></div>
      <p>{current.Id} · {current.Status} · {current.Owner}</p><p><a href={current.Source.startsWith('https://') ? current.Source : `https://github.com/TryUniCAD/Kit/blob/${current.Source.startsWith("Documentation/Planning/") ? data.Links.ExtraTasks.find(task => task.Id === "PlanningViews").Branch : data.MainRevision}/${current.Source}`}>Owning source</a></p>
      <p>Dependencies: {current.Dependencies.join(', ') || 'No parent edges recorded; inspect source prerequisites'}</p>
      <details><summary>Exit condition and evidence</summary><pre>{plain(current.Exit)}</pre><pre>{plain(current.Stages)}</pre><h3>Read / write / conversion tracks</h3><pre>{plain(current.Tracks || current.Boundary || "See owning source")}</pre></details>
      <form key={current.Id} onSubmit={saveWindow}><label>Start<input name="start" type="date" required defaultValue={current.Start || today} /></label><label>Finish<input name="finish" type="date" required defaultValue={current.Finish || today} /></label><label>Estimate basis<input name="basis" required maxLength={500} defaultValue={current.Basis || 'Owner supplied investigation window'} /></label><button>Update draft window</button></form>
      <div className="actions"><button onClick={() => copyPrompt(current)}>Copy agent prompt</button><button onClick={() => copyPrompt(current, "local Codex")}>Copy local handoff</button><button onClick={() => copyPrompt(current, "Hoplite")}>Copy Hoplite handoff</button><button onClick={() => copyPrompt(current, "configured GitHub or T3 agent")}>Copy dispatch request</button></div>
      <p>{eligible ? 'Locally eligible for handoff; live claim and prerequisite checks are still required' : 'Dispatch blocked: scope needs a current window, no owner and verified prerequisites'}</p>
      <p>Copying does not claim or start work. Repository issues are disabled. Copy a handoff to an available runtime; direct local and Hoplite launch integrations are unavailable.</p>
      <label>Agent prompt<textarea readOnly rows={12} value={promptFor(current)} onFocus={event => event.target.select()} /></label>
    </section>}
  </main>;
}

createRoot(document.getElementById('root')).render(<Board />);
