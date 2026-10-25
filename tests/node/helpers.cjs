'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { SKILL_NAME, COMMANDS, AGENTS } = require('../../bin/manifest');

const repoRoot = path.join(__dirname, '..', '..');

// Minimal YAML-subset parser for trusted project frontmatter. Supports string
// scalars, numbers, booleans, block arrays, and inline arrays only. Not safe
// for untrusted input — uses the first '\n---' as the terminator and does not
// handle quoted strings containing that sequence.
function parseFrontmatter(content) {
  if (!content.startsWith('---')) {
    throw new Error('Missing opening frontmatter delimiter (---)');
  }
  const end = content.indexOf('\n---', 3);
  if (end === -1) {
    throw new Error('Missing closing frontmatter delimiter (---)');
  }
  const block = content.slice(3, end).trim();
  const lines = block.split('\n');

  const result = {};
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.trim() === '' || line.trim().startsWith('#')) {
      i++;
      continue;
    }
    const match = line.match(/^([A-Za-z_][\w-]*)\s*:\s*(.*)$/);
    if (!match) {
      throw new Error(`Unparseable frontmatter line: ${line}`);
    }
    const key = match[1];
    const rawValue = match[2];

    if (rawValue === '') {
      const items = [];
      i++;
      while (i < lines.length && /^\s+-\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s+-\s+/, '').trim());
        i++;
      }
      result[key] = items;
      continue;
    }

    if (rawValue.startsWith('[') && rawValue.endsWith(']')) {
      const inner = rawValue.slice(1, -1).trim();
      result[key] = inner === ''
        ? []
        : inner.split(',').map((s) => s.trim().replace(/^["']|["']$/g, ''));
      i++;
      continue;
    }

    if (/^-?\d+$/.test(rawValue)) {
      result[key] = Number(rawValue);
      i++;
      continue;
    }

    if (rawValue === 'true' || rawValue === 'false') {
      result[key] = rawValue === 'true';
      i++;
      continue;
    }

    result[key] = rawValue.replace(/^["']|["']$/g, '');
    i++;
  }
  return result;
}

function createTempDir(prefix) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), prefix));
  const cleanup = () => {
    try {
      fs.rmSync(dir, { recursive: true, force: true });
    } catch {
      // best effort
    }
  };
  return { dir, cleanup };
}

function assertInstallShape(claudeDir, pkgVersion, { isGlobal = false } = {}) {
  assert.ok(
    fs.existsSync(claudeDir),
    `.claude/ directory should exist (looked at ${claudeDir})`
  );

  const skillDir = path.join(claudeDir, 'skills', SKILL_NAME);
  const rel = (p) => path.relative(claudeDir, p);

  assert.ok(fs.existsSync(path.join(skillDir, 'SKILL.md')), 'missing skill SKILL.md');

  for (const cmd of COMMANDS) {
    const p = path.join(skillDir, 'references', 'commands', `${cmd}.md`);
    assert.ok(fs.existsSync(p), `missing command reference: ${rel(p)}`);
  }
  for (const agent of AGENTS) {
    const p = path.join(skillDir, 'references', 'agents', `${agent}.md`);
    assert.ok(fs.existsSync(p), `missing agent reference: ${rel(p)}`);
  }
  for (const p of [
    path.join(skillDir, 'references', 'scoring', 'EVALUATION.md'),
    path.join(skillDir, 'references', 'founder.md'),
    path.join(skillDir, 'references', 'report.md'),
    path.join(skillDir, 'references', 'hn.md'),
    path.join(skillDir, 'scripts', 'compute.py'),
    path.join(skillDir, 'scripts', 'render_report.py'),
    path.join(skillDir, 'scripts', 'hnparse.py'),
    path.join(skillDir, 'scripts', 'hnsearch.py'),
    path.join(skillDir, 'scripts', 'lib', 'schema.py'),
    path.join(skillDir, 'assets', 'report', 'template.html.j2'),
    path.join(skillDir, 'assets', 'report', 'template.md.j2'),
    path.join(skillDir, 'assets', 'report', 'styles.css'),
  ]) {
    assert.ok(fs.existsSync(p), `missing skill file: ${rel(p)}`);
  }

  const dims = fs.readdirSync(path.join(skillDir, 'references', 'scoring', 'dimensions'));
  assert.equal(dims.filter((f) => f.endsWith('.md')).length, 14, 'expected 14 dimension files');
  const schemas = fs.readdirSync(path.join(skillDir, 'assets', 'schemas'));
  assert.equal(schemas.filter((f) => f.endsWith('.json')).length, 10, 'expected 10 schemas');

  const installed = fs.readdirSync(skillDir, { recursive: true });
  assert.ok(
    !installed.some((f) => f.split(path.sep).some((part) => part === 'tests' || part === '__pycache__')),
    'installed skill must not contain tests/ or __pycache__/'
  );

  for (const legacy of [
    path.join(claudeDir, 'agents', 'ti-evaluator.md'),
    path.join(claudeDir, 'commands', 'tweak'),
    path.join(claudeDir, 'skills', 'ti-scoring'),
    path.join(claudeDir, 'skills', 'tweak-evaluate'),
    path.join(claudeDir, 'scripts', 'compute.py'),
    path.join(claudeDir, 'schemas', 'idea.json'),
    path.join(claudeDir, 'tweakidea'),
  ]) {
    assert.ok(!fs.existsSync(legacy), `legacy path should not exist: ${rel(legacy)}`);
  }

  const versionFile = path.join(skillDir, 'VERSION');
  assert.ok(fs.existsSync(versionFile), `missing ${rel(versionFile)}`);
  assert.equal(
    fs.readFileSync(versionFile, 'utf8').trim(),
    pkgVersion,
    'VERSION file should match package.json version'
  );

  const settingsPath = path.join(claudeDir, 'settings.json');
  assert.ok(fs.existsSync(settingsPath), 'missing .claude/settings.json');
  const settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));

  assert.ok(
    settings.permissions && Array.isArray(settings.permissions.allow),
    'settings.permissions.allow must be an array'
  );
  const expectedAllow = [
    'WebSearch',
    'WebFetch',
    'Read(~/.tweakidea/**)',
    'Edit(~/.tweakidea/**)',
  ];
  const skillRead = `Read(~/.claude/skills/${SKILL_NAME}/**)`;
  if (isGlobal) expectedAllow.push(skillRead);
  for (const perm of expectedAllow) {
    assert.ok(
      settings.permissions.allow.includes(perm),
      `settings.permissions.allow must include ${perm}`
    );
  }
  if (!isGlobal) {
    assert.ok(
      !settings.permissions.allow.includes(skillRead),
      `local installs must not add ${skillRead}`
    );
  }

  assert.ok(
    Array.isArray(settings.permissions.additionalDirectories),
    'settings.permissions.additionalDirectories must be an array'
  );
  assert.ok(
    settings.permissions.additionalDirectories.includes('~/.tweakidea'),
    "settings.permissions.additionalDirectories must include '~/.tweakidea'"
  );
  assert.ok(
    !settings.permissions.additionalDirectories.includes('~/.tweakidea/*'),
    "settings.permissions.additionalDirectories must not include legacy '~/.tweakidea/*'"
  );
}

module.exports = {
  parseFrontmatter,
  createTempDir,
  assertInstallShape,
  repoRoot,
};
