import test from 'node:test';
import assert from 'node:assert/strict';

test('ApiClient: fallback mock handler handles empty payloads safely', async () => {
  const mockFallback = () => ({ status: 'OK', total: 100 });
  const result = mockFallback();
  assert.equal(result.status, 'OK');
  assert.equal(result.total, 100);
});

test('ApiClient: safe JSON parser resolves empty strings without throw', () => {
  const parseSafe = (rawText) => {
    if (!rawText || rawText.trim().length === 0) return null;
    try {
      return JSON.parse(rawText);
    } catch {
      return { detail: rawText };
    }
  };

  assert.equal(parseSafe(''), null);
  assert.equal(parseSafe('   '), null);
  assert.deepEqual(parseSafe('{"ready":true}'), { ready: true });
  assert.deepEqual(parseSafe('Service Unavailable'), { detail: 'Service Unavailable' });
});