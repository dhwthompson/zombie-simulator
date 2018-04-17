const assert = require('assert');
const World = require('../world');

describe('World', () => {
  describe('constructor', function() {
    it('creates a single-cell world', function() {
      let world = new World(1, 1);
      assert.deepEqual(world.rows, [[null]]);
    });

    it('creates a single-row world', function() {
      let world = new World(3, 1);
      assert.deepEqual(world.rows, [[null, null, null]]);
    });

    it('creates a multi-row world', function() {
      let world = new World(2, 2);
      assert.deepEqual(world.rows, [[null, null], [null, null]]);
    });

    it('creates an explicitly empty world', function() {
      let world = new World(2, 2, []);
      assert.deepEqual(world.rows, [[null, null], [null, null]]);
    });

    it('creates a world with a character', function() {
      const character = {};
      let world = new World(2, 2, [{x: 0, y: 0, character: character}]);

      assert.deepEqual(world.rows, [[character, null], [null, null]]);
    });
  });

  describe('withCharacterAt', function() {
    it('adds a character', function() {
      let world = new World(1, 1);
      let character = {};
      world = world.withCharacterAt(character, 0, 0);
      assert.deepEqual(world.rows, [[character]]);
    });

    it('adds a character to a multi-cell world', function() {
      let world = new World(2, 2);
      let character = {};
      world = world.withCharacterAt(character, 0, 0);
      assert.deepEqual(world.rows, [[character, null], [null, null]]);
    });
  });

  describe('populatedBy', function() {
    it('populates the world', function() {
      let populator = { next: function() { return {c: 1}; } };
      world = World.populatedBy(2, 2, populator);
      assert.deepEqual(world.rows, [[{c: 1},{c: 1}],[{c: 1}, {c: 1}]]);
    });
  });
});
