const Vector = require('./vector');

class Zombie {
  constructor() { }

  get living() { return false; }

  move(environment) {
    let bestDistance = Infinity;
    let bestTarget = null;

    const noMove = new Vector(0, 0);

    environment = environment.map(function(envRecord) {
      return { offset: new Vector(envRecord.dx, envRecord.dy), character: envRecord.character};
    });

    const targets = environment.filter(t => t.character.living);

    function inBitingRange(offset) {
      return Math.abs(offset.dx) < 2 && Math.abs(offset.dy) < 2;
    }

    if (targets.some(target => inBitingRange(target.offset))) {
      return noMove;
    }

    targets.forEach(function(target) {
      if (target.offset.distance < bestDistance) {
        bestDistance = target.offset.distance;
        bestTarget = target;
      }
    });

    if (bestTarget === null) {
      return noMove;
    }

    let moves;

    const bestX = Math.sign(bestTarget.offset.dx);
    const bestY = Math.sign(bestTarget.offset.dy);

    if (bestX == 0) {
      moves = [0, -1, 1].map(dx => new Vector(dx, bestY));
    }
    else if (bestY == 0) {
      moves = [0, -1, 1].map(dy => new Vector(bestX, dy));
    }
    else {
      moves = [
        new Vector(bestX, bestY),
        new Vector(0, bestY),
        new Vector(bestX, 0)
      ];
    }

    moves = moves.filter(function(move) {
      return !environment.some(t => t.offset.equals(move));
    });

    if (moves.length > 0) {
      return moves[0];
    } else {
      return noMove;
    }
  }
}

class Human {
  constructor() { }

  get living() { return true; }

  move(environment) {
    return {dx: 0, dy: 0};
  }
}

class Population {
  constructor(humanDensity, zombieChance) {
    this.humanDensity = humanDensity;
    this.zombieChance = zombieChance;
  }

  next() {
    if (Math.random() >= this.humanDensity) {
      return null;
    }

    if (Math.random() < this.zombieChance) {
      return new Zombie();
    } else {
      return new Human();
    }
  }
}

module.exports = { Human, Population, Zombie };
