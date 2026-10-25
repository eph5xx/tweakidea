'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { repoRoot } = require('./helpers.cjs');
const { SKILL_NAME } = require('../../bin/manifest');
const pkg = require('../../package.json');

const PLATFORMS = ['.claude-plugin', '.codex-plugin', '.cursor-plugin'];

function readJson(rel) {
  return JSON.parse(fs.readFileSync(path.join(repoRoot, rel), 'utf8'));
}

// A skills entry may point at a skill dir or at a parent dir of skill dirs.
function skillMdPaths(entry) {
  const dir = path.resolve(repoRoot, entry);
  const rel = path.relative(repoRoot, dir);
  assert.ok(rel && !rel.startsWith('..') && !path.isAbsolute(rel), `skills path escapes repo: ${entry}`);
  assert.ok(fs.statSync(dir, { throwIfNoEntry: false })?.isDirectory(), `skills path is not a directory: ${entry}`);
  if (fs.existsSync(path.join(dir, 'SKILL.md'))) return [path.join(dir, 'SKILL.md')];
  return fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((e) => e.isDirectory() && fs.existsSync(path.join(dir, e.name, 'SKILL.md')))
    .map((e) => path.join(dir, e.name, 'SKILL.md'));
}

for (const platform of PLATFORMS) {
  test(`${platform}/plugin.json matches package.json`, () => {
    const manifest = readJson(`${platform}/plugin.json`);
    assert.equal(manifest.name, SKILL_NAME);
    assert.equal(manifest.version, pkg.version, 'plugin version must match package.json');
    assert.equal(manifest.license, pkg.license);
    assert.ok(Array.isArray(manifest.skills) && manifest.skills.length > 0, 'skills must be a non-empty array');
    const found = manifest.skills.flatMap(skillMdPaths);
    assert.deepEqual(
      found.map((p) => path.relative(repoRoot, p)),
      [path.join('skills', SKILL_NAME, 'SKILL.md')],
      'skills must resolve to exactly the tweakidea SKILL.md'
    );
  });

  test(`${platform}/marketplace.json lists the plugin from the repo root`, () => {
    const marketplace = readJson(`${platform}/marketplace.json`);
    assert.ok(Array.isArray(marketplace.plugins));
    assert.equal(marketplace.plugins.length, 1);
    assert.equal(marketplace.plugins[0].name, SKILL_NAME);
    assert.equal(marketplace.plugins[0].source, './');
  });
}
