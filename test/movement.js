const assert = require('assert');
const character = require('../character');
const World = require('../world');

const Zombie = character.Zombie, Human = character.Human;

describe('movement', function() {
  it('moves the zombie towards the human', function() {
    const zombie = new Zombie();
    const human = new Human();
    const characters = [
      {x: 0, y: 0, character: zombie},
      {x: 2, y: 2, character: human}
    ];
    let world = new World(3, 3, characters);

    world = world.tick();

    assert.deepEqual(
      world.rows,
      [[null, null, null],
       [null, zombie, null],
       [null, null, human]]
    );
  });

  it('does not move zombies onto one another', function() {
    const zombie = new Zombie();
    const zombie2 = new Zombie();
    const human = new Human();
    const characters = [
      {x: 1, y: 0, character: zombie},
      {x: 2, y: 0, character: zombie2},
      {x: 2, y: 2, character: human}
    ];
    let world = new World(3, 3, characters);

    world = world.tick();

    assert.deepEqual(
      world.rows,
      [[null, null, zombie2],
       [null, null, zombie],
       [null, null, human]]
    );
  });
});
