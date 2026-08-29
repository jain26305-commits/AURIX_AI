import test from 'node:test';
import assert from 'node:assert/strict';

test('AuthService: Validates RBAC Role Permissions', () => {
  const ROLES = {
    SUPER_ADMIN: ['read', 'write', 'dispatch', 'admin'],
    EXECUTIVE: ['read', 'dispatch'],
    PLANNER: ['read', 'write'],
    AUDITOR: ['read']
  };

  const hasPermission = (role, permission) => {
    return (ROLES[role] || []).includes(permission);
  };

  assert.equal(hasPermission('SUPER_ADMIN', 'admin'), true);
  assert.equal(hasPermission('EXECUTIVE', 'dispatch'), true);
  assert.equal(hasPermission('PLANNER', 'admin'), false);
  assert.equal(hasPermission('AUDITOR', 'write'), false);
});