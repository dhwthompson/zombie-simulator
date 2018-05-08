const assert = require('assert');
const Vector = require('../vector');

describe('Vector', () => {
  describe('constructor', () => {
    it('fails with no arguments', () => {
      assert.throws(() => new Vector(), /x offset/);
    });

    it('fails with a single argument', () => {
      assert.throws(() => new Vector(3), /y offset/);
    });

    it('succeeds with two arguments', () => {
      const v = new Vector(2, 6);
    });
  });

  describe('dx', () => {
    it('returns the x offset', () => {
      const v = new Vector(2, 6);
      assert.equal(v.dx, 2);
    });
  });

  describe('dy', () => {
    it('returns the y offset', () => {
      const v = new Vector(2, 6);
      assert.equal(v.dy, 6);
    });
  });

  describe('distance', () => {
    it('returns zero for a zero vector', () => {
      const v = new Vector(0, 0);
      assert.equal(v.distance, 0);
    });

    it('returns the squared Euclidean distance', () => {
      const v = new Vector(2, 1);
      assert.equal(v.distance, 5);
    });

    it('deals with a negative x offset', () => {
      const v = new Vector(-2, 1);
      assert.equal(v.distance, 5);
    });

    it('deals with a negative y offset', () => {
      const v = new Vector(2, -1);
      assert.equal(v.distance, 5);
    });

    it('deals with two negative offsets', () => {
      const v = new Vector(-2, -1);
      assert.equal(v.distance, 5);
    });
  });

  describe('equals', () => {
    it('returns true for an equal vector', () => {
      const v = new Vector(2, 5);
      assert(v.equals(new Vector(2, 5)));
    });

    it('returns false for an unequal vector', () => {
      const v = new Vector(2, 5);
      assert(!v.equals(new Vector(1, 5)));
    });
  });

  describe('add', () => {
    it('adds two vectors', () => {
      const v = new Vector(2, 5);
      const sum = v.add(new Vector(1, 2));
      assert.deepEqual([sum.dx, sum.dy], [3, 7]);
    });
  });

  describe('sub', () => {
    it('subtracts two vectors', () => {
      const v = new Vector(2, 5);
      const result = v.sub(new Vector(1, 2));
      assert.deepEqual([result.dx, result.dy], [1, 3]);
    });
  });
});
