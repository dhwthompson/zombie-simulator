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

  get rows() {
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
    if (x < 0 || x >= this.width || y < 0 || y >= this.height) {
      return undefined;
    }
    const record = this.characters.find((r) => r.x == x && r.y == y);
    if(record === undefined) {
      return null;
    }
    return record.character;
  }
}

module.exports = World;
