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

  static populatedBy(width, height, populator) {
    let world = new World(width, height);
    for (let x = 0; x < width; x++) {
      for (let y = 0; y < height; y++) {
        const newCharacter = populator.next();
        if (newCharacter !== null) {
          world = world.withCharacterAt(newCharacter, x, y);
        }
      }
    }

    return world;
  }

  get rows() {
    let rows = [];
    for (let rowNum = 0; rowNum < this.height; rowNum++) {
      let row = new Array(this.width);
      for (let colNum = 0; colNum < this.width; colNum++) {
        row[colNum] = this._at(colNum, rowNum);
      }
      rows.push(row);
    }
    return rows;
  }

  withCharacterAt(character, x, y) {
    if (character === null) {
      throw new Error('Attempted to add a null character at (' + x + ', ' + y + ')');
    }
    let newCharacters = this.characters.filter(cr => cr.character !== character);
    if (newCharacters.some(cr => cr.x === x && cr.y === y)) {
      throw new Error('Invalid move to occupied space (' + x + ', ' + y + ')');
    }

    newCharacters.push({x: x, y: y, character: character});

    return new World(this.width, this.height, newCharacters);
  }

  viewpoint(x, y) {
    return this.characters.map(function(charRecord) {
      return {
        dx: charRecord.x - x,
        dy: charRecord.y - y,
        character: charRecord.character
      };
    });
  }

  tick() {
    // Give each character a move, in order, and return the resulting world
    return this.characters.reduce(
      function(world, charRecord) {
        const viewpoint = world.viewpoint(charRecord.x, charRecord.y);
        const move = charRecord.character.move(viewpoint);
        return world.withCharacterAt(
          charRecord.character,
          charRecord.x + move.dx,
          charRecord.y + move.dy
        );
      },
      this
    );
  }

  _at(x, y) {
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
