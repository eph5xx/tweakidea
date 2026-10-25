'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { parseFrontmatter, repoRoot } = require('./helpers.cjs');
const { SKILL_NAME, SKILL_SOURCE, COMMANDS, AGENTS } = require('../../bin/manifest');

const skillDir = path.join(repoRoot, SKILL_SOURCE);
const skillMdPath = path.join(skillDir, 'SKILL.md');

test('skills/ contains only the tweakidea skill', () => {
  const dirs = fs
    .readdirSync(path.join(repoRoot, 'skills'), { withFileTypes: true })
    .filter((e) => e.isDirectory())
    .map((e) => e.name);
  assert.deepEqual(dirs, [SKILL_NAME]);
});

test('SKILL.md has canonical frontmatter', () => {
  const fm = parseFrontmatter(fs.readFileSync(skillMdPath, 'utf8'));
  assert.equal(fm.name, SKILL_NAME, 'name must match directory name');
  assert.equal(typeof fm.description, 'string');
  assert.ok(fm.description.length > 0, 'description must not be empty');
  assert.equal(fm['user-invocable'], true, 'user-invocable must be true');
  assert.equal(typeof fm['argument-hint'], 'string');
  for (const cmd of COMMANDS) {
    assert.ok(fm['argument-hint'].includes(cmd), `argument-hint must list ${cmd}`);
  }
  assert.ok(Array.isArray(fm['allowed-tools']), 'allowed-tools must be an array');
  for (const tool of ['Read', 'Write', 'Bash', 'Glob', 'Agent', 'AskUserQuestion']) {
    assert.ok(fm['allowed-tools'].includes(tool), `allowed-tools must include ${tool}`);
  }
});

test('skill root holds only SKILL.md, scripts, references, assets', () => {
  const entries = fs.readdirSync(skillDir).filter((e) => e !== '.DS_Store').sort();
  assert.deepEqual(entries, ['SKILL.md', 'assets', 'references', 'scripts']);
});

test('every relative link in SKILL.md resolves', () => {
  const body = fs.readFileSync(skillMdPath, 'utf8');
  const links = [...body.matchAll(/\]\(([^)]+)\)/g)].map((m) => m[1]);
  assert.ok(links.length > 0, 'SKILL.md should link its references');
  for (const link of links) {
    assert.ok(
      fs.existsSync(path.join(skillDir, link)),
      `SKILL.md links to missing path: ${link}`
    );
  }
});

test('SKILL.md links every command and agent reference', () => {
  const body = fs.readFileSync(skillMdPath, 'utf8');
  for (const cmd of COMMANDS) {
    assert.ok(body.includes(`references/commands/${cmd}.md`), `SKILL.md must link ${cmd}`);
  }
  for (const agent of AGENTS) {
    assert.ok(body.includes(`references/agents/${agent}.md`), `SKILL.md must link ${agent}`);
  }
});

test('reference files are plain markdown without frontmatter', () => {
  const refs = fs
    .readdirSync(path.join(skillDir, 'references'), { recursive: true })
    .filter((f) => f.endsWith('.md'));
  assert.ok(refs.length > 0);
  for (const f of refs) {
    const content = fs.readFileSync(path.join(skillDir, 'references', f), 'utf8');
    assert.ok(!content.startsWith('---'), `references/${f} must not have frontmatter`);
  }
});

test('skill source does not contain tests', () => {
  const all = fs.readdirSync(skillDir, { recursive: true });
  for (const f of all) {
    assert.ok(!f.split(path.sep).includes('tests'), `test file inside skill: ${f}`);
  }
});
