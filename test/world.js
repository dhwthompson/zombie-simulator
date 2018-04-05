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

  it('adds a character', function() {
    let world = new World(1, 1);
    let character = {};
    world = world.addCharacter(character, 0, 0);
    assert.deepEqual(world.rows, [[character]]);
  });

  it('adds a character to a multi-cell world', function() {
    let world = new World(2, 2);
    let character = {};
    world = world.addCharacter(character, 0, 0);
    assert.deepEqual(world.rows, [[character, null], [null, null]]);
  });
});
