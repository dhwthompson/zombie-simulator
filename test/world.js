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

    it('moves an existing character', function() {
      const character = {};
      let world = new World(2, 2, [{x: 0, y: 0, character: character}]);

      world = world.withCharacterAt(character, 1, 1);

      assert.deepEqual(world.rows, [[null, null], [null, character]]);
    });

    it('leaves non-moving characters alone', function() {
      const character = {a: 1};
      const otherCharacter = {b: 1};
      let world = new World(2, 2, [
        {x: 0, y: 0, character: character},
        {x: 1, y: 1, character: otherCharacter}
      ]);

      world = world.withCharacterAt(character, 1, 0);

      assert.deepEqual(world.rows, [[null, character], [null, otherCharacter]]);
    });

    it('moves a character to the space they are in already', function() {
      const character = {a: 1};
      const otherCharacter = {b: 1};
      const world = new World(2, 2, [
        {x: 0, y: 0, character: character},
        {x: 1, y: 1, character: otherCharacter}
      ]);

      let newWorld = world.withCharacterAt(character, 0, 0);

      assert.deepEqual(newWorld.rows, world.rows);
    });

    it('refuses to move one character onto another', function() {
      const character = {a: 1};
      const otherCharacter = {b: 1};
      let world = new World(2, 2, [
        {x: 0, y: 0, character: character},
        {x: 1, y: 1, character: otherCharacter}
      ]);

      assert.throws(
        () => world.withCharacterAt(character, 1, 1),
        Error
      );
    });
  });

  describe('viewpoint', function() {
    it('shows an empty environment', function() {
      const world = new World(2, 2);
      assert.deepEqual(world.viewpoint(1, 1), []);
    });
    it('shows a character with their grid offset', function() {
      const world = new World(2, 2, [{x: 1, y: 1, character: {}}]);
      assert.deepEqual(world.viewpoint(1, 1), [{dx: 0, dy: 0, character: {}}]);
    });
    it('shows multiple characters', function() {
      const characters = [
        {x: 1, y: 1, character: {a: 1}},
        {x: 2, y: 0, character: {b: 1}}
      ];
      const world = new World(2, 2, characters);
      assert.deepEqual(world.viewpoint(0, 1),
        [
          {dx: 1, dy: 0, character: {a: 1}},
          {dx: 2, dy: -1, character: {b: 1}}
        ]
      );
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
