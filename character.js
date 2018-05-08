const Vector = require('./vector');

class Zombie {
  constructor() { }

  get living() { return false; }

  get _moves() {
    let singleMoves = [];

    [-1, 0, 1].forEach(function(dx) {
      singleMoves = singleMoves.concat([-1, 0, 1].map(dy => new Vector(dx, dy)));
    });

    return singleMoves;
  }

  move(environment) {
    let bestDistance = Infinity;
    let bestTarget = null;

    const noMove = new Vector(0, 0);

    environment = environment.map(function(envRecord) {
      return { offset: new Vector(envRecord.dx, envRecord.dy), character: envRecord.character};
    });

    const targets = environment.filter(t => t.character.living);

    targets.forEach(function(target) {
      if (target.offset.distance < bestDistance) {
        bestDistance = target.offset.distance;
        bestTarget = target;
      }
    });

    if (bestDistance <= 2) {
      // Biting range: no more than 1 away in either direction
      return noMove;
    }

    if (bestTarget === null) {
      return noMove;
    }

    const freeMoves = this._moves.filter(function(move) {
      if (move.distance == 0) {
        return true;
      } else {
        return !environment.some(t => t.offset.equals(move));
      }
    });

    function compareMoves(moveA, moveB) {
      const distA = bestTarget.offset.sub(moveA).distance;
      const distB = bestTarget.offset.sub(moveB).distance;

      if (distA !== distB) {
        return distA - distB;
      }
      return moveA.distance - moveB.distance;
    }

    const sortedMoves = freeMoves.sort(compareMoves);

    return sortedMoves[0];
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
