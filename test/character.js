const assert = require('assert');
const character = require('../character');

const Human = character.Human;
const Population = character.Population;
const Zombie = character.Zombie;

describe('Zombie', function() {
  it('stays still if nothing is nearby', function() {
    let zombie = new Zombie();
    const environment = [];

    assert.deepEqual(zombie.move(environment), {dx: 0, dy: 0});
  });

  const singleCases = [
    {desc: 'right', dx: 2, dy: 0, expectedMove: {dx: 1, dy: 0}},
    {desc: 'left', dx: -2, dy: 0, expectedMove: {dx: -1, dy: 0}},
    {desc: 'up', dx: 0, dy: 2, expectedMove: {dx: 0, dy: 1}},
    {desc: 'down', dx: 0, dy: -2, expectedMove: {dx: 0, dy: -1}},
    {desc: 'up-left', dx: -2, dy: 2, expectedMove: {dx: -1, dy: 1}},
    {desc: 'up-right', dx: 2, dy: 2, expectedMove: {dx: 1, dy: 1}},
    {desc: 'down-left', dx: -2, dy: -2, expectedMove: {dx: -1, dy: -1}},
    {desc: 'down-right', dx: 2, dy: -2, expectedMove: {dx: 1, dy: -1}},
  ];

  singleCases.forEach(function(testCase) {
    it('moves ' + testCase.desc + ' toward a human', function() {
      let zombie = new Zombie();
      const environment = [
        {dx: testCase.dx, dy: testCase.dy, character: new Human()}
      ];

      assert.deepEqual(zombie.move(environment), testCase.expectedMove);
    });
  });

  it('moves toward the nearest human', function() {
    let zombie = new Zombie();
    const environment = [
        {dx: 3, dy: -3, character: new Human()},
        {dx: 2, dy: 2, character: new Human()},
        {dx: -3, dy: 3, character: new Human()},
    ];

    assert.deepEqual(zombie.move(environment), {dx: 1, dy: 1});
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
