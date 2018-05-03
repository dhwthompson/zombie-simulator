class Zombie {
  constructor() { }

  get living() { return false; }

  move(environment) {
    let dx = 0, dy = 0;

    let bestDistance = Infinity;
    let bestTarget = null;
    let bitingRange = false;

    const targets = environment.filter(t => t.character.living);

    targets.forEach(function(target) {
      /* Given we can move diagonally, Manhattan distance is fine */

      const xDistance = Math.abs(target.dx);
      const yDistance = Math.abs(target.dy);
      const distance = xDistance + yDistance;
      if (distance < bestDistance) {
        bestDistance = distance;
        bestTarget = target;
        if (Math.max(xDistance, yDistance) < 2) {
          bitingRange = true;
        }
      }
    });

    if (bitingRange) {
      return {dx: 0, dy: 0};
    }

    let moves;

    if (bestTarget !== null) {
      dx = Math.sign(bestTarget.dx);
      dy = Math.sign(bestTarget.dy);

      if (dx == 0) {
        moves = [{dx: 0, dy: dy}, {dx: -1, dy: dy}, {dx: 1, dy: dy}];
      }
      else if (dy == 0) {
        moves = [{dx: dx, dy: 0}, {dx: dx, dy: -1}, {dx: dx, dy: 1}];
      }
      else {
        moves = [{dx: dx, dy: dy}, {dx: 0, dy: dy}, {dx: dx, dy: 0}];
      }

      moves = moves.filter(function(move) {
        return !environment.some(t => t.dx == move.dx && t.dy == move.dy);
      });

      if (moves.length > 0) {
        return moves[0];
      } else {
        return {dx: 0, dy: 0};
      }
    }
    return {dx, dy};
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
