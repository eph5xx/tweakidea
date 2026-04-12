'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { parseFrontmatter, repoRoot } = require('./helpers.cjs');

const VALID_MODELS = new Set(['sonnet', 'opus', 'haiku']);

function loadFrontmatter(absPath) {
  const content = fs.readFileSync(absPath, 'utf8');
  try {
    return parseFrontmatter(content);
  } catch (err) {
    throw new Error(
      `${path.relative(repoRoot, absPath)}: ${err.message}`
    );
  }
}

test('agents: every .md file has canonical frontmatter', () => {
  const agentsDir = path.join(repoRoot, 'agents');
  const files = fs.readdirSync(agentsDir).filter((f) => f.endsWith('.md'));
  assert.ok(files.length > 0, 'expected at least one agent file');

  for (const file of files) {
    const abs = path.join(agentsDir, file);
    const fm = loadFrontmatter(abs);
    const rel = `agents/${file}`;

    assert.equal(typeof fm.name, 'string', `${rel}: name must be string`);
    assert.equal(
      fm.name,
      file.replace(/\.md$/, ''),
      `${rel}: name must match filename stem`
    );
    assert.equal(
      typeof fm.description,
      'string',
      `${rel}: description must be string`
    );
    assert.ok(
      fm.description.length > 0,
      `${rel}: description must not be empty`
    );
    assert.ok(
      VALID_MODELS.has(fm.model),
      `${rel}: model must be one of sonnet|opus|haiku (got ${fm.model})`
    );
    assert.ok(
      Array.isArray(fm.tools),
      `${rel}: tools must be an array`
    );
    assert.equal(
      typeof fm.permissionMode,
      'string',
      `${rel}: permissionMode must be string`
    );
    assert.equal(
      typeof fm.maxTurns,
      'number',
      `${rel}: maxTurns must be number`
    );
    if (fm.skills !== undefined) {
      assert.ok(
        Array.isArray(fm.skills),
        `${rel}: skills must be an array when present`
      );
    }
  }
});

test('commands: every .md file has canonical frontmatter', () => {
  const commandsDir = path.join(repoRoot, 'commands', 'tweak');
  const files = fs.readdirSync(commandsDir).filter((f) => f.endsWith('.md'));
  assert.ok(files.length > 0, 'expected at least one command file');

  for (const file of files) {
    const abs = path.join(commandsDir, file);
    const fm = loadFrontmatter(abs);
    const rel = `commands/tweak/${file}`;

    assert.equal(typeof fm.name, 'string', `${rel}: name must be string`);
    assert.ok(
      fm.name.startsWith('tweak:'),
      `${rel}: name must start with 'tweak:' (got ${fm.name})`
    );
    assert.equal(
      typeof fm.description,
      'string',
      `${rel}: description must be string`
    );
    assert.ok(
      fm.description.length > 0,
      `${rel}: description must not be empty`
    );
    assert.ok(
      Array.isArray(fm['allowed-tools']),
      `${rel}: allowed-tools must be an array`
    );
    if (fm['argument-hint'] !== undefined) {
      assert.equal(
        typeof fm['argument-hint'],
        'string',
        `${rel}: argument-hint must be string when present`
      );
    }
    if (fm.skills !== undefined) {
      assert.ok(
        Array.isArray(fm.skills),
        `${rel}: skills must be an array when present`
      );
    }
  }
});

test('skills: every SKILL.md has canonical frontmatter', () => {
  const skillsDir = path.join(repoRoot, 'skills');
  const entries = fs
    .readdirSync(skillsDir, { withFileTypes: true })
    .filter((e) => e.isDirectory());
  assert.ok(entries.length > 0, 'expected at least one skill directory');

  for (const entry of entries) {
    const skillFile = path.join(skillsDir, entry.name, 'SKILL.md');
    assert.ok(
      fs.existsSync(skillFile),
      `skills/${entry.name}/SKILL.md must exist`
    );
    const fm = loadFrontmatter(skillFile);
    const rel = `skills/${entry.name}/SKILL.md`;

    assert.equal(typeof fm.name, 'string', `${rel}: name must be string`);
    assert.equal(
      fm.name,
      entry.name,
      `${rel}: name must match directory name`
    );
    assert.equal(
      typeof fm.description,
      'string',
      `${rel}: description must be string`
    );
    assert.ok(
      fm.description.length > 0,
      `${rel}: description must not be empty`
    );
    assert.equal(
      typeof fm['user-invocable'],
      'boolean',
      `${rel}: user-invocable must be boolean`
    );
  }
});
