#!/usr/bin/env node
'use strict';

const { execFileSync } = require('node:child_process');
const { readdirSync } = require('node:fs');
const { join, relative } = require('node:path');

const repoRoot = join(__dirname, '..');
const testDir = join(repoRoot, 'tests');

const files = readdirSync(testDir)
  .filter((f) => f.endsWith('.test.cjs'))
  .sort()
  .map((f) => relative(repoRoot, join(testDir, f)));

if (files.length === 0) {
  console.error('No test files found in tests/');
  process.exit(1);
}

try {
  execFileSync(
    process.execPath,
    ['--test', '--test-concurrency=4', ...files],
    { stdio: 'inherit', cwd: repoRoot }
  );
} catch (err) {
  process.exit(err.status ?? 1);
}
