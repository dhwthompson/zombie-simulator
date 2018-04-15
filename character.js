class Zombie {
  constructor() { }

  move(environment) {
    let dx = 0, dy = 0;

    if (environment.length > 0) {
      if (environment[0].dx > 0) {
        dx = 1;
      }
      if (environment[0].dx < 0) {
        dx = -1;
      }
      if (environment[0].dy > 0) {
        dy = 1;
      }
      if (environment[0].dy < 0) {
        dy = -1;
      }
    }
    return {dx, dy};
  }
}

class Human {
  constructor() { }
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
