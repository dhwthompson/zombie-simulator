class Renderer {
  constructor(world) {
    this.world = world;
  }

  get lines() {
    let lines = [];
    for(let row of this.world.rows) {
      let line = '';
      for(let cell of row) {
        line += '. ';
      }
      lines.push(line);
    }
    return lines;
  }
}

module.exports = Renderer;
