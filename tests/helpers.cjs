'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const {
  AGENT_FILES,
  SKILL_DIRS,
  COMMAND_FILES,
} = require('../bin/manifest');

const repoRoot = path.join(__dirname, '..');

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

function assertInstallShape(claudeDir, pkgVersion) {
  assert.ok(
    fs.existsSync(claudeDir),
    `.claude/ directory should exist (looked at ${claudeDir})`
  );

  for (const agent of AGENT_FILES) {
    const p = path.join(claudeDir, 'agents', agent);
    assert.ok(fs.existsSync(p), `missing agent: .claude/agents/${agent}`);
  }

  for (const skill of SKILL_DIRS) {
    const skillMd = path.join(claudeDir, 'skills', skill, 'SKILL.md');
    assert.ok(
      fs.existsSync(skillMd),
      `missing skill: .claude/skills/${skill}/SKILL.md`
    );
  }

  for (const cmd of COMMAND_FILES) {
    const p = path.join(claudeDir, cmd);
    assert.ok(fs.existsSync(p), `missing command: .claude/${cmd}`);
  }

  const versionFile = path.join(claudeDir, 'tweakidea', 'VERSION');
  assert.ok(fs.existsSync(versionFile), 'missing .claude/tweakidea/VERSION');
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
  for (const perm of ['WebSearch', 'WebFetch']) {
    assert.ok(
      settings.permissions.allow.includes(perm),
      `settings.permissions.allow must include ${perm}`
    );
  }

  assert.ok(
    Array.isArray(settings.permissions.additionalDirectories),
    'settings.permissions.additionalDirectories must be an array'
  );
  assert.ok(
    settings.permissions.additionalDirectories.includes('~/.tweakidea/*'),
    "settings.permissions.additionalDirectories must include '~/.tweakidea/*'"
  );
}

module.exports = {
  parseFrontmatter,
  createTempDir,
  assertInstallShape,
  repoRoot,
};
