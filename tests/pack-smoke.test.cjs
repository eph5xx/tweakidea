'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const { createTempDir, assertInstallShape, repoRoot } = require('./helpers.cjs');
const pkg = require('../package.json');

test('npm pack tarball installs cleanly and matches expected shape', (t) => {
  const { dir: work, cleanup } = createTempDir('tweakidea-pack-');
  t.after(cleanup);

  const tarballDir = path.join(work, 'tarball');
  const extractDir = path.join(work, 'extracted');
  const userDir = path.join(work, 'userproj');
  fs.mkdirSync(tarballDir);
  fs.mkdirSync(extractDir);
  fs.mkdirSync(userDir);

  const pack = spawnSync(
    'npm',
    ['pack', '--pack-destination', tarballDir, '--silent'],
    {
      cwd: repoRoot,
      stdio: 'pipe',
      encoding: 'utf8',
      timeout: 60_000,
    }
  );
  assert.equal(
    pack.status,
    0,
    `npm pack exited ${pack.status}\nstdout:\n${pack.stdout}\nstderr:\n${pack.stderr}`
  );

  const tarballs = fs.readdirSync(tarballDir).filter((f) => f.endsWith('.tgz'));
  assert.equal(
    tarballs.length,
    1,
    `expected exactly one .tgz in ${tarballDir}, got ${tarballs.length}`
  );
  const tarballPath = path.join(tarballDir, tarballs[0]);

  const extract = spawnSync('tar', ['-xzf', tarballPath, '-C', extractDir], {
    stdio: 'pipe',
    encoding: 'utf8',
    timeout: 30_000,
  });
  assert.equal(
    extract.status,
    0,
    `tar exited ${extract.status}\nstderr:\n${extract.stderr}`
  );

  const packageDir = path.join(extractDir, 'package');
  const installer = path.join(packageDir, 'bin', 'install.js');
  assert.ok(
    fs.existsSync(installer),
    `missing installer in packed tarball: ${installer}`
  );

  const install = spawnSync(process.execPath, [installer, '--local'], {
    cwd: userDir,
    stdio: 'pipe',
    encoding: 'utf8',
    timeout: 30_000,
  });
  assert.equal(
    install.status,
    0,
    `installer exited ${install.status}\nstdout:\n${install.stdout}\nstderr:\n${install.stderr}`
  );

  assertInstallShape(path.join(userDir, '.claude'), pkg.version);
});
