const assert = require('assert');
const Renderer = require('../renderer');
const World = require('../world');

describe('Renderer', () => {
  it('renders a single-cell world', function() {
    let world = new World(1, 1);
    let renderer = new Renderer(world);
    assert.deepEqual(renderer.lines, ['. ']);
  });

  it('renders a single-row world', function() {
    let world = new World(5, 1);
    let renderer = new Renderer(world);
    assert.deepEqual(renderer.lines, ['. . . . . ']);
  });

  it('renders a muti-row world', function() {
    let world = new World(5, 3);
    let renderer = new Renderer(world);
    assert.deepEqual(renderer.lines,
      ['. . . . . ', '. . . . . ', '. . . . . ']);
  });
});
