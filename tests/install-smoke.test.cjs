'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const { createTempDir, assertInstallShape, repoRoot } = require('./helpers.cjs');
const pkg = require('../package.json');

test('install --local populates .claude/ with all shipped files', (t) => {
  const { dir: tmp, cleanup } = createTempDir('tweakidea-smoke-');
  t.after(cleanup);

  const installer = path.join(repoRoot, 'bin', 'install.js');
  const result = spawnSync(process.execPath, [installer, '--local'], {
    cwd: tmp,
    stdio: 'pipe',
    encoding: 'utf8',
    timeout: 30_000,
  });

  assert.equal(
    result.status,
    0,
    `installer exited ${result.status}\nstdout:\n${result.stdout}\nstderr:\n${result.stderr}`
  );

  assertInstallShape(path.join(tmp, '.claude'), pkg.version);
});

test('install --local upgrades legacy settings and preserves user rules', (t) => {
  const { dir: tmp, cleanup } = createTempDir('tweakidea-upgrade-');
  t.after(cleanup);

  const claudeDir = path.join(tmp, '.claude');
  fs.mkdirSync(claudeDir, { recursive: true });
  const settingsPath = path.join(claudeDir, 'settings.json');
  fs.writeFileSync(
    settingsPath,
    JSON.stringify({
      permissions: {
        allow: ['WebSearch', 'WebFetch', 'Bash(ls *)'],
        additionalDirectories: ['~/.tweakidea/*'],
      },
    })
  );

  const installer = path.join(repoRoot, 'bin', 'install.js');
  for (let i = 0; i < 2; i++) {
    const result = spawnSync(process.execPath, [installer, '--local'], {
      cwd: tmp,
      stdio: 'pipe',
      encoding: 'utf8',
      timeout: 30_000,
    });
    assert.equal(
      result.status,
      0,
      `installer run ${i + 1} exited ${result.status}\nstdout:\n${result.stdout}\nstderr:\n${result.stderr}`
    );
  }

  assertInstallShape(claudeDir, pkg.version);

  const { allow, additionalDirectories } = JSON.parse(
    fs.readFileSync(settingsPath, 'utf8')
  ).permissions;
  const count = (arr, v) => arr.filter((x) => x === v).length;

  assert.ok(allow.includes('Bash(ls *)'), 'user allow rule must be preserved');
  for (const perm of ['WebSearch', 'WebFetch', 'Read(~/.tweakidea/**)', 'Edit(~/.tweakidea/**)']) {
    assert.equal(count(allow, perm), 1, `${perm} should appear exactly once`);
  }
  assert.equal(count(additionalDirectories, '~/.tweakidea'), 1);
  assert.equal(count(additionalDirectories, '~/.tweakidea/*'), 0);
});
