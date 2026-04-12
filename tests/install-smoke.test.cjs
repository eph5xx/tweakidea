'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
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
