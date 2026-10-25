'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const { createTempDir, assertInstallShape, repoRoot } = require('./helpers.cjs');
const pkg = require('../../package.json');

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

test('install --local removes the v3 layout and keeps user files', (t) => {
  const { dir: tmp, cleanup } = createTempDir('tweakidea-legacy-');
  t.after(cleanup);

  const claudeDir = path.join(tmp, '.claude');
  const seed = {
    'agents/ti-evaluator.md': 'x',
    'agents/my-agent.md': 'user',
    'commands/tweak/evaluate.md': 'x',
    'skills/ti-scoring/SKILL.md': 'x',
    'skills/tweak-evaluate/SKILL.md': 'x',
    'skills/my-skill/SKILL.md': 'user',
    'scripts/compute.py': 'x',
    'scripts/lib/schema.py': 'x',
    'scripts/my-script.sh': 'user',
    'schemas/idea.json': '{}',
    'tweakidea/VERSION': '2.9.0\n',
  };
  for (const [rel, content] of Object.entries(seed)) {
    const p = path.join(claudeDir, rel);
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(p, content);
  }

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
  assert.match(result.stdout, /Upgrading TweakIdea from v2\.9\.0/);

  assertInstallShape(claudeDir, pkg.version);
  for (const rel of ['agents/my-agent.md', 'skills/my-skill/SKILL.md', 'scripts/my-script.sh']) {
    assert.ok(fs.existsSync(path.join(claudeDir, rel)), `user file removed: ${rel}`);
  }
  assert.ok(!fs.existsSync(path.join(claudeDir, 'schemas')), 'empty legacy schemas/ should be pruned');
  assert.ok(!fs.existsSync(path.join(claudeDir, 'commands')), 'empty legacy commands/ should be pruned');
});

test('install --global writes to HOME and allows reading the skill dir', (t) => {
  const { dir: home, cleanup } = createTempDir('tweakidea-global-');
  t.after(cleanup);

  const installer = path.join(repoRoot, 'bin', 'install.js');
  const result = spawnSync(process.execPath, [installer, '--global'], {
    cwd: home,
    env: { ...process.env, HOME: home },
    stdio: 'pipe',
    encoding: 'utf8',
    timeout: 30_000,
  });
  assert.equal(
    result.status,
    0,
    `installer exited ${result.status}\nstdout:\n${result.stdout}\nstderr:\n${result.stderr}`
  );

  assertInstallShape(path.join(home, '.claude'), pkg.version, { isGlobal: true });
});

test('uninstall removes the skill and VERSION', (t) => {
  const { dir: tmp, cleanup } = createTempDir('tweakidea-uninstall-');
  t.after(cleanup);

  const installer = path.join(repoRoot, 'bin', 'install.js');
  for (const flags of [['--local'], ['--uninstall', '--local']]) {
    const result = spawnSync(process.execPath, [installer, ...flags], {
      cwd: tmp,
      stdio: 'pipe',
      encoding: 'utf8',
      timeout: 30_000,
    });
    assert.equal(result.status, 0, `installer ${flags.join(' ')} exited ${result.status}\n${result.stderr}`);
  }
  assert.ok(!fs.existsSync(path.join(tmp, '.claude', 'skills', 'tweakidea')));
});
