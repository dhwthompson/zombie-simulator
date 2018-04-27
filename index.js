"use strict";

const sleep = require('sleep');

const character = require('./character');
const Renderer = require('./renderer');
const World = require('./world');

const Population = character.Population;

const worldWidth = 60, worldHeight = 30;
const humanDensity = 0.05, zombieProbability = 0.9;

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
