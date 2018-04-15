const assert = require('assert');
const character = require('../character');

const Population = character.Population;
const Zombie = character.Zombie;

describe('Zombie', function() {
  it('stays still if nothing is nearby', function() {
    let zombie = new Zombie();
    const environment = [];

    assert.deepEqual(zombie.move(environment), {dx: 0, dy: 0});
  });
});

describe('Population', function() {
  it('generates no humans', function() {
    let population = new Population(0, 0);
    let generated = [];
    for (let i = 0; i < 100; i++) {
      generated.push(population.next());
    }

    for (let g of generated) {
      assert.strictEqual(g, null);
    }
  });

  it('generates no zombies', function() {
    let population = new Population(0, 1);
    let generated = [];
    for (let i = 0; i < 100; i++) {
      generated.push(population.next());
    }

    for (let g of generated) {
      assert.strictEqual(g, null);
    }
  });

  it('generates humans', function() {
    let population = new Population(1, 0);
    let generated = [];
    for (let i = 0; i < 100; i++) {
      generated.push(population.next());
    }

    for (let g of generated) {
      assert(g instanceof character.Human);
    }
  });

  it('generates zombies', function() {
    let population = new Population(1, 1);
    let generated = [];
    for (let i = 0; i < 100; i++) {
      generated.push(population.next());
    }

    for (let g of generated) {
      assert(g instanceof character.Zombie);
    }
  });
});
