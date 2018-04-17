const assert = require('assert');
const Renderer = require('../renderer');

describe('Renderer', () => {
  it('renders a single-cell world', function() {
    let world = {rows: [[null]]};
    let renderer = new Renderer(world);
    assert.deepEqual(renderer.lines, ['. ']);
  });

  it('renders a single-row world', function() {
    let world = {rows: [[null, null, null, null, null]]};
    let renderer = new Renderer(world);
    assert.deepEqual(renderer.lines, ['. . . . . ']);
  });

  it('renders a muti-row world', function() {
    let world = {
      rows: [
        [null, null, null, null, null],
        [null, null, null, null, null],
        [null, null, null, null, null]
      ]
    };
    let renderer = new Renderer(world);
    assert.deepEqual(renderer.lines,
      ['. . . . . ', '. . . . . ', '. . . . . ']);
  });
});
