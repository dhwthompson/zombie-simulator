const character = require('./character');

class Renderer {
  constructor(world) {
    this.world = world;
  }

  get lines() {
    let lines = [];
    for(let row of this.world.rows) {
      let line = '';
      for(let cell of row) {
        if(cell instanceof character.Zombie) {
          line += '\u{1F9DF} ';
        }
        else if(cell instanceof character.Human) {
          line += '\u{1F468} ';
        }
        else {
          line += '. ';
        }
      }
      lines.push(line);
    }
    return lines;
  }
}

module.exports = Renderer;
