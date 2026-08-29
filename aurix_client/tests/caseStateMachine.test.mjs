import test from 'node:test';
import assert from 'node:assert/strict';

test('CaseStateMachine: Transitions through Valid Resolution Lifecycle', () => {
  const VALID_TRANSITIONS = {
    OPEN: ['IN_TRIAGE', 'CANCELLED'],
    IN_TRIAGE: ['ROOT_CAUSE_IDENTIFIED', 'OPEN'],
    ROOT_CAUSE_IDENTIFIED: ['RESOLUTION_DISPATCHED'],
    RESOLUTION_DISPATCHED: ['CLOSED', 'IN_TRIAGE'],
    CLOSED: []
  };

  const canTransition = (current, next) => {
    return (VALID_TRANSITIONS[current] || []).includes(next);
  };

  assert.equal(canTransition('OPEN', 'IN_TRIAGE'), true);
  assert.equal(canTransition('IN_TRIAGE', 'ROOT_CAUSE_IDENTIFIED'), true);
  assert.equal(canTransition('ROOT_CAUSE_IDENTIFIED', 'CLOSED'), false);
  assert.equal(canTransition('RESOLUTION_DISPATCHED', 'CLOSED'), true);
});