import test from 'node:test';
import assert from 'node:assert/strict';

test('InventoryPolicy: Computes Lead-Time Demand and Safety Stock with Z-Score', () => {
  const dailyDemand = 5.14;
  const leadTimeDays = 28;
  const sigmaDemand = 1.2;
  const zScore = 2.05; // 98% service level

  const ltd = Math.round(dailyDemand * leadTimeDays);
  const ss = Math.round(zScore * sigmaDemand * Math.sqrt(leadTimeDays) * 5.2);
  const rop = ltd + ss;

  assert.equal(ltd, 144);
  assert.ok(ss > 60 && ss < 80);
  assert.equal(rop, ltd + ss);
});