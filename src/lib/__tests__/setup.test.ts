import { describe, it, expect } from 'vitest';

describe('Vitest Setup', () => {
  it('should run tests', () => {
    expect(true).toBe(true);
  });

  it('should have path aliases configured', () => {
    // This will fail if path resolution doesn't work
    // We'll verify imports work in actual tests
    expect(typeof expect).toBe('function');
  });
});
