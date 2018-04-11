class Zombie {
  constructor() { }
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
