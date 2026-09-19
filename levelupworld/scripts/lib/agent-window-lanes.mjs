/**
 * Agents Window lanes on top of the Needs Attention classifier.
 *
 * Working is still running. Read is finished work that can be reviewed.
 * Needs Attention stays the blocked / unread bucket. A running agent is not
 * sent a follow-up; Cloud Agents reject that while the run is in progress.
 */
import { loadRails, triageFleet } from './needs-attention-rails.mjs';

function ageMs(agent, now) {
  const stamp = agent?.lastMessageActivityAtMs || agent?.updatedAtMs || agent?.createdAtMs || now;
  return Math.max(0, now - Number(stamp));
}

export function laneFor(agent) {
  const status = agent?.status;
  if (status === 'RUNNING' || status === 'NOT_YET_STARTED' || status === 'WAITING_FOR_BACKGROUND_WORK') {
    return 'working';
  }
  if (agent?.isArchived || agent?.isKilled || status === 'ARCHIVED' || status === 'EXPIRED') {
    return 'read';
  }
  if (status === 'IDLE' && (agent?.didCreatePullRequest || agent?.didMakeCodeChanges)) {
    return 'read';
  }
  return 'needs_attention';
}

export function applyLane(agent, classified, { now = Date.now(), rails = loadRails() } = {}) {
  const lane = laneFor(agent);
  const next = { ...classified, lane };
  if (lane === 'read') {
    if (agent?.didCreatePullRequest || agent?.didMakeCodeChanges) next.action = 'read_check';
    return next;
  }
  if (lane !== 'working') return next;

  const stall = Number(rails.stallAfterMs);
  const budget = Number(rails.workingBudgetMs || stall * 2);
  const age = ageMs(agent, now);
  if (age > budget) {
    return {
      ...next,
      disposition: 'page_human',
      reason: 'working_over_budget',
      action: 'notify_slack',
      human_only: null,
    };
  }
  if (age > stall) {
    return {
      ...next,
      disposition: 'watch',
      reason: 'stalled_running',
      action: 'subscribe_timer',
    };
  }
  if (next.action === 'followup_run') next.action = 'none';
  return next;
}

export function triageWithLanes(input = {}) {
  const now = typeof input.now === 'number' ? input.now : Date.now();
  const rails = input.rails || loadRails();
  const report = triageFleet({ ...input, now, rails });
  const agents = Array.isArray(input.agents) ? input.agents : [];
  report.results = report.results.map((row, index) => applyLane(agents[index], row, { now, rails }));
  report.summary = { working: 0, needs_attention: 0, read: 0 };
  for (const row of report.results) {
    if (report.summary[row.lane] !== undefined) report.summary[row.lane] += 1;
  }
  return report;
}
