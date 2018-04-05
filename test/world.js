const assert = require('assert');
const World = require('../world');

describe('World', () => {
  it('has a single-cell row', function() {
    let world = new World(1, 1);
    assert.deepEqual(world.rows, [[null]]);
  });

  it('has a single-row world', function() {
    let world = new World(3, 1);
    assert.deepEqual(world.rows, [[null, null, null]]);
  });

  it('has a multi-row world', function() {
    let world = new World(2, 2);
    assert.deepEqual(world.rows, [[null, null], [null, null]]);
  });

  it('returns null for empty spaces', function() {
    let world = new World(2, 2);
    assert.strictEqual(world.at(1, 1), null);
  });

  outOfBounds = [
    [-1, 0],
    [0, -1],
    [3, 2],
    [2, 3]
  ];

  outOfBounds.forEach(function(point) {
    it('returns undefined for point ' + point, function() {
      const world = new World(3, 3);
      const x = point[0], y = point[1];
      assert.strictEqual(world.at(x, y), undefined);
    });
  });

  it('adds a character', function() {
    let world = new World(2, 2);
    let character = {};
    let populatedWorld = world.addCharacter(character, 1, 1);
    assert.strictEqual(populatedWorld.at(1, 1), character);
  });
});
