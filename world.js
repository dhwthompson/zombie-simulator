class World {
  constructor(width, height, characters) {
    this.width = width;
    this.height = height;
    if(characters === undefined) {
      this.characters = [];
    }
    else {
      this.characters = characters;
    }
  }

  rows() {
    let rows = [];
    for (let rowNum = 0; rowNum < this.height; rowNum++) {
      let row = new Array(this.width);
      row.fill(null);
      rows.push(row);
    }
    return rows;
  }

  addCharacter(character, x, y) {
    const newChars = this.characters.concat([{x: x, y: y, character: character}]);
    return new World(this.width, this.height, newChars);
  }

  at(x, y) {
    const record = this.characters.find((r) => r.x == x && r.y == y);
    if(record === undefined) {
      return null;
    }
    return record.character;
  }
}

module.exports = World;
