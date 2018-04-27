"use strict";

const sleep = require('sleep');

const character = require('./character');
const Renderer = require('./renderer');
const World = require('./world');

const Population = character.Population;

const worldWidth = 40, worldHeight = 20;
const humanDensity = 0.1, zombieProbability = 0.1;

const population = new Population(humanDensity, zombieProbability);

let world = World.populatedBy(worldWidth, worldHeight, population);
let renderer = new Renderer(world);

while(true) {
  console.clear();
  for (let line of renderer.lines) {
    console.log(line);
  }
  sleep.msleep(200);
  world = world.tick();
  renderer = new Renderer(world);
}
