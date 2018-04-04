const assert = require('assert');
const World = require('../world');

describe('World', () => {
  it('has a single-cell row', function() {
    let world = new World(1, 1);
    assert.deepEqual(world.rows(), [[null]]);
  });

  it('has a single-row world', function() {
    let world = new World(3, 1);
    assert.deepEqual(world.rows(), [[null, null, null]]);
  });

  it('has a multi-row world', function() {
    let world = new World(2, 2);
    assert.deepEqual(world.rows(), [[null, null], [null, null]]);
  });

  it('returns null for empty spaces', function() {
    let world = new World(2, 2);
    assert.equal(world.at(1, 1), null);
  });

  it('adds a character', function() {
    let world = new World(2, 2);
    let character = {};
    let populatedWorld = world.addCharacter(character, 1, 1);
    assert.equal(populatedWorld.at(1, 1), character);
  });
});
