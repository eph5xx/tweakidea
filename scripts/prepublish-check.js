#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { spawnSync } = require('node:child_process');

const repoRoot = path.join(__dirname, '..');
const installer = path.join(repoRoot, 'bin', 'install.js');

try {
  new vm.Script(fs.readFileSync(installer, 'utf8'), {
    filename: 'bin/install.js',
  });
} catch (err) {
  console.error(`prepublish-check: bin/install.js failed to parse`);
  console.error(err.message);
  process.exit(1);
}

const result = spawnSync('npm', ['test'], {
  stdio: 'inherit',
  cwd: repoRoot,
});

if (result.error) {
  console.error(`prepublish-check: failed to run npm test: ${result.error.message}`);
  process.exit(1);
}

process.exit(result.status ?? 1);
