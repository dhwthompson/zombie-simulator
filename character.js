class Zombie {
  constructor() { }

  get living() { return false; }

  move(environment) {
    let dx = 0, dy = 0;

    let bestDistance = Infinity;
    let bestTarget = null;

    const targets = environment.filter(t => t.character.living);

    targets.forEach(function(target) {
      /* Given we can move diagonally, Manhattan distance is fine */
      const distance = Math.abs(target.dx) + Math.abs(target.dy);
      if (distance < bestDistance) {
        bestDistance = distance;
        bestTarget = target;
      }
    });

    if (bestTarget !== null) {
      if (bestTarget.dx > 0) {
        dx = 1;
      }
      if (bestTarget.dx < 0) {
        dx = -1;
      }
      if (bestTarget.dy > 0) {
        dy = 1;
      }
      if (bestTarget.dy < 0) {
        dy = -1;
      }
    }
    return {dx, dy};
  }
}

class Human {
  constructor() { }

  get living() { return true; }
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
