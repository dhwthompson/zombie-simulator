const assert = require('assert');
const character = require('../character');

const Population = character.Population;


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
