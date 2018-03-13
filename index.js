"use strict";

var clear = require("clear");

var humanDensity = 0.1;
var zombieProbability = 0.1;

function initGrid(gridSizeX, gridSizeY) {
  var grid = [];

  for (var i = 0; i < gridSizeY; i++) {
    var row = new Array(gridSizeX);
    row.fill(null);
    grid.push(row);
  }
  return grid;
}

function populateCharacters(grid) {
  for (var row of grid) {
    for (var x = 0; x < row.length; x++) {
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
  var rendered = "";
  for (var row of grid) {
    for (var cell of row) {
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

var grid = initGrid(40, 20);
populateCharacters(grid);
clear();
console.log(renderGrid(grid));
