#!/usr/bin/env node

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');

const pkg = require('../package.json');

// ── ANSI helpers ────────────────────────────────────────────────────────────────

const cyan = '\x1b[36m';
const green = '\x1b[32m';
const yellow = '\x1b[33m';
const red = '\x1b[31m';
const dim = '\x1b[2m';
const bold = '\x1b[1m';
const reset = '\x1b[0m';

// ── uv hard requirement (Phase 1) ───────────────────────────────────────────────

function verifyUvOrExit() {
  const { spawnSync } = require('child_process');
  const result = spawnSync('uv', ['--version'], { stdio: 'pipe' });
  if (result.error || result.status !== 0) {
    console.error('');
    console.error(`${red}${bold}TweakIdea requires 'uv' for the evaluate pipeline.${reset}`);
    console.error('');
    console.error(`  ${bold}Install uv:${reset}`);
    console.error(`  ${dim}macOS/Linux:${reset}  curl -LsSf https://astral.sh/uv/install.sh | sh`);
    console.error(`  ${dim}macOS (brew):${reset} brew install uv`);
    console.error('');
    console.error(`  Then re-run: ${cyan}npx tweakidea${reset}`);
    console.error('');
    process.exit(1);
  }
  const version = result.stdout.toString().trim();
  console.log(`${dim}Verified: ${version}${reset}`);
}

// ── File manifest ───────────────────────────────────────────────────────────────

const { SKILL_NAME, SKILL_SOURCE, COMMANDS, AGENTS } = require('./manifest');

// ── CLI argument parsing ────────────────────────────────────────────────────────

const args = process.argv.slice(2);

function hasFlag(...flags) {
  return flags.some((f) => args.includes(f));
}

const wantGlobal = hasFlag('--global', '-g');
const wantLocal = hasFlag('--local', '-l');
const wantUninstall = hasFlag('--uninstall', '-u');
const wantHelp = hasFlag('--help', '-h');
const wantVersion = hasFlag('--version', '-v');

// ── Path resolution ─────────────────────────────────────────────────────────────

function getGlobalDir() {
  return path.join(os.homedir(), '.claude');
}

function getLocalDir() {
  return path.join(process.cwd(), '.claude');
}

function resolveTargetDir(isGlobal) {
  return isGlobal ? getGlobalDir() : getLocalDir();
}

function getSourceDir() {
  return path.join(__dirname, '..');
}

function skillTargetDir(targetDir) {
  return path.join(targetDir, 'skills', SKILL_NAME);
}

// ── File utilities ──────────────────────────────────────────────────────────────

const COPY_SKIP = new Set(['__pycache__', '.DS_Store']);

function mkdirp(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function copyDirSync(src, dest) {
  mkdirp(dest);
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    if (COPY_SKIP.has(entry.name)) continue;
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirSync(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function rmrf(target) {
  if (!fs.existsSync(target)) return;
  fs.rmSync(target, { recursive: true, force: true });
}

function removeIfExists(target) {
  if (!fs.existsSync(target)) return 0;
  rmrf(target);
  return 1;
}

function pruneIfEmpty(dir) {
  if (fs.existsSync(dir) && fs.readdirSync(dir).length === 0) {
    fs.rmdirSync(dir);
  }
}

// ── Legacy cleanup (past-version upgrades) ──────────────────────────────────────

// Up to v3, TweakIdea installed separate agents, commands, ti-* skills, and
// top-level scripts/ and schemas/ dirs. Only known TweakIdea files are removed
// so user-owned files in shared dirs like .claude/scripts survive.
const LEGACY_AGENT_FILES = [...AGENTS, 'ti-merger'].map((a) => `${a}.md`);
const LEGACY_SKILL_DIRS = ['ti-scoring', 'ti-founder', 'ti-report', 'ti-hnparse', 'ti-html-report'];
const LEGACY_COMMANDS = [...COMMANDS, 'suggest-from-hn'];
const LEGACY_SCRIPT_ENTRIES = ['compute.py', 'render_report.py', 'run-tests.cjs', 'lib', 'tests', '__pycache__'];
const LEGACY_SCHEMA_FILES = [
  'assumptions.json',
  'dimension-evaluation.json',
  'hypotheses.json',
  'idea.json',
  'next-steps.json',
  'numbers.json',
  'potential.json',
  'research.json',
  'strengths-weaknesses.json',
  'version.json',
];
const LEGACY_VERSION_DIR = 'tweakidea';

function legacyCleanup(targetDir) {
  let removed = 0;
  for (const file of LEGACY_AGENT_FILES) {
    removed += removeIfExists(path.join(targetDir, 'agents', file));
  }
  for (const dir of LEGACY_SKILL_DIRS) {
    removed += removeIfExists(path.join(targetDir, 'skills', dir));
  }
  for (const cmd of LEGACY_COMMANDS) {
    // Local installs used commands/tweak/*.md; global installs used skills/tweak-*/.
    removed += removeIfExists(path.join(targetDir, 'commands', 'tweak', `${cmd}.md`));
    removed += removeIfExists(path.join(targetDir, 'skills', `tweak-${cmd}`));
  }
  for (const entry of LEGACY_SCRIPT_ENTRIES) {
    removed += removeIfExists(path.join(targetDir, 'scripts', entry));
  }
  for (const file of LEGACY_SCHEMA_FILES) {
    removed += removeIfExists(path.join(targetDir, 'schemas', file));
  }
  removed += removeIfExists(path.join(targetDir, LEGACY_VERSION_DIR));

  pruneIfEmpty(path.join(targetDir, 'commands', 'tweak'));
  pruneIfEmpty(path.join(targetDir, 'commands'));
  pruneIfEmpty(path.join(targetDir, 'agents'));
  pruneIfEmpty(path.join(targetDir, 'scripts'));
  pruneIfEmpty(path.join(targetDir, 'schemas'));
  return removed;
}

// ── Settings merger ─────────────────────────────────────────────────────────────

function mergeSettings(targetDir, isGlobal) {
  const settingsPath = path.join(targetDir, 'settings.json');
  let settings = {};

  if (fs.existsSync(settingsPath)) {
    try {
      settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
    } catch {
      console.log(
        `${yellow}Warning: ${settingsPath} contains invalid JSON. Skipping settings merge.${reset}`
      );
      console.log(
        `${dim}Fix the file manually, then re-run the installer to add TweakIdea permissions.${reset}`
      );
      return;
    }
  }

  // Ensure permissions structure
  if (!settings.permissions) settings.permissions = {};
  if (!Array.isArray(settings.permissions.allow)) settings.permissions.allow = [];
  if (!Array.isArray(settings.permissions.additionalDirectories)) {
    settings.permissions.additionalDirectories = [];
  }

  // Add required permissions (deduplicated)
  // Path rules must use Read/Edit: Claude Code only checks those for file
  // access, and Edit covers Write. Subagents deny anything not explicitly
  // allowed, even inside additionalDirectories.
  const requiredAllow = [
    'WebSearch',
    'WebFetch',
    'Read(~/.tweakidea/**)',
    'Edit(~/.tweakidea/**)',
  ];
  // Subagents read references and schemas from the skill dir. A local install
  // lives inside the project, which is readable already.
  if (isGlobal) {
    requiredAllow.push(`Read(~/.claude/skills/${SKILL_NAME}/**)`);
  }
  for (const perm of requiredAllow) {
    if (!settings.permissions.allow.includes(perm)) {
      settings.permissions.allow.push(perm);
    }
  }

  // Older installs wrote a glob, which additionalDirectories does not accept.
  const legacyDirs = ['~/.tweakidea/*'];
  settings.permissions.additionalDirectories =
    settings.permissions.additionalDirectories.filter((d) => !legacyDirs.includes(d));

  const requiredDirs = ['~/.tweakidea'];
  for (const dir of requiredDirs) {
    if (!settings.permissions.additionalDirectories.includes(dir)) {
      settings.permissions.additionalDirectories.push(dir);
    }
  }

  mkdirp(targetDir);
  fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + '\n');
}

// ── Version tracking ────────────────────────────────────────────────────────────

function writeVersion(targetDir, version) {
  fs.writeFileSync(path.join(skillTargetDir(targetDir), 'VERSION'), version + '\n');
}

function readInstalledVersion(targetDir) {
  const candidates = [
    path.join(skillTargetDir(targetDir), 'VERSION'),
    path.join(targetDir, LEGACY_VERSION_DIR, 'VERSION'),
  ];
  for (const file of candidates) {
    if (fs.existsSync(file)) return fs.readFileSync(file, 'utf8').trim();
  }
  return null;
}

// ── Install ─────────────────────────────────────────────────────────────────────

function countFiles(dir, predicate) {
  if (!fs.existsSync(dir)) return 0;
  return fs
    .readdirSync(dir, { recursive: true })
    .filter((f) => typeof f === 'string' && predicate(f)).length;
}

function install(isGlobal) {
  const targetDir = resolveTargetDir(isGlobal);
  const sourceDir = getSourceDir();
  const location = isGlobal ? 'global' : 'local';
  const displayPath = isGlobal
    ? '~/.claude'
    : path.relative(process.cwd(), targetDir) || '.claude';

  verifyUvOrExit();

  const existingVersion = readInstalledVersion(targetDir);
  if (existingVersion) {
    if (existingVersion === pkg.version) {
      console.log(
        `\n${dim}TweakIdea v${existingVersion} already installed. Reinstalling...${reset}`
      );
    } else {
      console.log(
        `\n${cyan}Upgrading TweakIdea from v${existingVersion} to v${pkg.version}...${reset}`
      );
    }
  }

  const skillDir = skillTargetDir(targetDir);
  rmrf(skillDir);

  const removed = legacyCleanup(targetDir);
  if (removed > 0) {
    console.log(`${dim}Removed ${removed} legacy file(s) from older TweakIdea layouts.${reset}`);
  }

  copyDirSync(path.join(sourceDir, SKILL_SOURCE), skillDir);

  mergeSettings(targetDir, isGlobal);
  writeVersion(targetDir, pkg.version);

  const commandCount = COMMANDS.filter((c) =>
    fs.existsSync(path.join(skillDir, 'references', 'commands', `${c}.md`))
  ).length;
  const agentCount = AGENTS.filter((a) =>
    fs.existsSync(path.join(skillDir, 'references', 'agents', `${a}.md`))
  ).length;
  const schemaCount = countFiles(path.join(skillDir, 'assets', 'schemas'), (f) => f.endsWith('.json'));
  const scriptCount = countFiles(path.join(skillDir, 'scripts'), (f) => f.endsWith('.py'));

  console.log('');
  console.log(`${green}${bold}TweakIdea v${pkg.version} installed successfully!${reset}`);
  console.log('');
  console.log(`  ${dim}Location:${reset}  ${displayPath}/skills/${SKILL_NAME} (${location})`);
  console.log(`  ${dim}Commands:${reset}  ${commandCount} available via /${SKILL_NAME}`);
  console.log(`  ${dim}Agents:${reset}    ${agentCount} references`);
  console.log(`  ${dim}Schemas:${reset}   ${schemaCount} installed`);
  console.log(`  ${dim}Scripts:${reset}   ${scriptCount} installed`);
  console.log('');

  console.log(`${cyan}Get started:${reset}`);
  console.log(`  ${bold}/tweakidea browse-hn${reset} ${dim}[topic] [today|week|month|all]${reset}`);
  console.log(`  ${bold}/tweakidea diff${reset} ${dim}<run1> <run2> or latest${reset}`);
  console.log(`  ${bold}/tweakidea analyze-hn-post${reset} ${dim}<hn-url-or-id>${reset}`);
  console.log(`  ${bold}/tweakidea evaluate${reset} ${dim}"Your startup idea description"${reset}`);
  console.log(`  ${bold}/tweakidea improve${reset} ${dim}latest${reset}`);
  console.log(`  ${bold}/tweakidea list${reset} ${dim}runs 20${reset}`);
  console.log(`  ${bold}/tweakidea share${reset} ${dim}latest${reset}`);
  console.log(`  ${bold}/tweakidea show${reset} ${dim}latest${reset}`);
  console.log('');
  console.log(`${dim}Legacy installer. Recommended: npx skills add eph5xx/tweakidea${reset}`);
  console.log('');
}

// ── Uninstall ───────────────────────────────────────────────────────────────────

function uninstall(isGlobal) {
  const targetDir = resolveTargetDir(isGlobal);
  const displayPath = isGlobal ? '~/.claude' : '.claude';

  const existingVersion = readInstalledVersion(targetDir);
  if (!existingVersion) {
    console.log(`\n${yellow}TweakIdea is not installed in ${displayPath}.${reset}\n`);
    return;
  }

  rmrf(skillTargetDir(targetDir));
  legacyCleanup(targetDir);

  console.log('');
  console.log(
    `${green}TweakIdea v${existingVersion} uninstalled from ${displayPath}.${reset}`
  );
  console.log(`${dim}Your evaluation data in ~/.tweakidea/ was not removed.${reset}`);
  console.log('');
}
// ── Interactive prompts ─────────────────────────────────────────────────────────

function prompt(question) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    });
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

async function promptLocation() {
  console.log('');
  console.log(`  ${bold}Where should TweakIdea be installed?${reset}`);
  console.log('');
  console.log(`  ${cyan}1)${reset} Global ${dim}(~/.claude)${reset} - available in all projects`);
  console.log(`  ${cyan}2)${reset} Local  ${dim}(./.claude)${reset} - this project only`);
  console.log('');

  const answer = await prompt(`  ${bold}Select [1]:${reset} `);
  return answer === '2' ? false : true;
}

// ── Help ────────────────────────────────────────────────────────────────────────

function printHelp() {
  console.log(`
${bold}TweakIdea v${pkg.version}${reset}
14-dimension startup idea evaluator for Claude Code
${dim}Legacy installer. Recommended: npx skills add eph5xx/tweakidea${reset}

${bold}Usage:${reset}
  npx tweakidea [options]

${bold}Options:${reset}
  -g, --global      Install globally (~/.claude)
  -l, --local       Install locally (./.claude)
  -u, --uninstall   Remove TweakIdea files
  -v, --version     Show version
  -h, --help        Show this help

${bold}Examples:${reset}
  npx tweakidea              Interactive install
  npx tweakidea -g           Global install (no prompt)
  npx tweakidea -l           Local install (no prompt)
  npx tweakidea -u -g        Uninstall from global
`);
}

// ── Entry point ─────────────────────────────────────────────────────────────────

async function main() {
  // Banner
  console.log('');
  console.log(
    `${cyan}${bold}TweakIdea${reset} ${dim}v${pkg.version}${reset}`
  );

  if (wantHelp) {
    printHelp();
    return;
  }

  if (wantVersion) {
    console.log(pkg.version);
    return;
  }

  if (wantUninstall) {
    const isGlobal = wantLocal ? false : true; // default to global for uninstall
    uninstall(isGlobal);
    return;
  }

  // Determine install location
  let isGlobal;
  if (wantGlobal) {
    isGlobal = true;
  } else if (wantLocal) {
    isGlobal = false;
  } else if (!process.stdin.isTTY) {
    // Non-interactive: default to global
    isGlobal = true;
  } else {
    isGlobal = await promptLocation();
  }

  install(isGlobal);
}

main().catch((err) => {
  console.error(`\n${red}Error: ${err.message}${reset}\n`);
  process.exit(1);
});
