"use strict";

const clear = require("clear");

const humanDensity = 0.1;
const zombieProbability = 0.1;

function initGrid(gridSizeX, gridSizeY) {
  let grid = [];

  for (var i = 0; i < gridSizeY; i++) {
    let row = new Array(gridSizeX);
    row.fill(null);
    grid.push(row);
  }
  return grid;
}

function populateCharacters(grid) {
  for (let row of grid) {
    for (let x = 0; x < row.length; x++) {
      if (Math.random() < humanDensity) {
        if (Math.random() < zombieProbability) {
          row[x] = '🧟';
        } else {
          row[x] = '👱';
        }
      }
    }
  }
}

function renderGrid(grid) {
  let rendered = "";
  for (let row of grid) {
    for (let cell of row) {
      if (cell === null) {
        rendered += ". ";
      } else {
        rendered += cell + " ";
      }
    }
    rendered += "\n";
  }
  return rendered;
}

let grid = initGrid(40, 20);
populateCharacters(grid);
clear();
console.log(renderGrid(grid));
