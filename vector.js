class Vector {
  constructor(dx, dy) {
    if (dx === undefined) {
      throw new Error('Missing x offset');
    }
    if (dy === undefined) {
      throw new Error('Missing y offset');
    }

    this.dx = dx;
    this.dy = dy;
  }

  get distance() {
    return Math.abs(this.dx) + Math.abs(this.dy);
  }

  equals(other) {
    return this.dx == other.dx && this.dy == other.dy;
  }

  add(other) {
    return new Vector(this.dx + other.dx, this.dy + other.dy);
  }

  sub(other) {
    return new Vector(this.dx - other.dx, this.dy - other.dy);
  }
}

module.exports = Vector;
