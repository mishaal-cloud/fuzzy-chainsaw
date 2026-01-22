import { greet, version } from './index';

describe('fuzzy-chainsaw', () => {
  describe('greet', () => {
    it('should greet a person by name', () => {
      expect(greet('World')).toBe('Hello, World!');
    });

    it('should greet with custom name', () => {
      expect(greet('TypeScript')).toBe('Hello, TypeScript!');
    });
  });

  describe('version', () => {
    it('should have correct version', () => {
      expect(version).toBe('0.1.0');
    });
  });
});
