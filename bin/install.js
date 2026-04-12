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

// ── File manifest ───────────────────────────────────────────────────────────────

const {
  AGENT_FILES,
  SKILL_DIRS,
  COMMAND_FILES,
  cmdSrcToSkillName,
} = require('./manifest');

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

// ── File utilities ──────────────────────────────────────────────────────────────

function mkdirp(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function copyFileSync(src, dest) {
  mkdirp(path.dirname(dest));
  fs.copyFileSync(src, dest);
}

function copyDirSync(src, dest) {
  mkdirp(dest);
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
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

// ── Cleanup ─────────────────────────────────────────────────────────────────────

function cleanupPreviousInstall(targetDir) {
  let removed = 0;

  // Remove agents
  for (const file of AGENT_FILES) {
    const p = path.join(targetDir, 'agents', file);
    if (fs.existsSync(p)) {
      fs.unlinkSync(p);
      removed++;
    }
  }

  // Remove skill directories
  for (const dir of SKILL_DIRS) {
    const p = path.join(targetDir, 'skills', dir);
    if (fs.existsSync(p)) {
      rmrf(p);
      removed++;
    }
  }

  // Remove commands (local install format)
  for (const cmdSrc of COMMAND_FILES) {
    const cmdPath = path.join(targetDir, cmdSrc);
    if (fs.existsSync(cmdPath)) {
      fs.unlinkSync(cmdPath);
      removed++;
    }
  }
  // Clean empty parent dirs
  const tweakDir = path.join(targetDir, 'commands', 'tweak');
  if (fs.existsSync(tweakDir) && fs.readdirSync(tweakDir).length === 0) {
    fs.rmSync(tweakDir, { recursive: true, force: true });
  }

  // Remove command skills (global install format)
  for (const cmdSrc of COMMAND_FILES) {
    const skillName = cmdSrcToSkillName(cmdSrc);
    const skillPath = path.join(targetDir, 'skills', skillName);
    if (fs.existsSync(skillPath)) {
      rmrf(skillPath);
      removed++;
    }
  }

  // Remove version tracking
  const versionDir = path.join(targetDir, 'tweakidea');
  if (fs.existsSync(versionDir)) {
    rmrf(versionDir);
    removed++;
  }

  return removed;
}

// ── Settings merger ─────────────────────────────────────────────────────────────

function mergeSettings(targetDir) {
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
  const requiredAllow = ['WebSearch', 'WebFetch'];
  for (const perm of requiredAllow) {
    if (!settings.permissions.allow.includes(perm)) {
      settings.permissions.allow.push(perm);
    }
  }

  const requiredDirs = ['~/.tweakidea/*'];
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
  const versionDir = path.join(targetDir, 'tweakidea');
  mkdirp(versionDir);
  fs.writeFileSync(path.join(versionDir, 'VERSION'), version + '\n');
}

function readInstalledVersion(targetDir) {
  const versionFile = path.join(targetDir, 'tweakidea', 'VERSION');
  if (!fs.existsSync(versionFile)) return null;
  return fs.readFileSync(versionFile, 'utf8').trim();
}

// ── Install ─────────────────────────────────────────────────────────────────────

function install(isGlobal) {
  const targetDir = resolveTargetDir(isGlobal);
  const sourceDir = getSourceDir();
  const location = isGlobal ? 'global' : 'local';
  const displayPath = isGlobal
    ? '~/.claude'
    : path.relative(process.cwd(), targetDir) || '.claude';

  // Check existing version
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

  // Clean previous install
  const removed = cleanupPreviousInstall(targetDir);
  if (removed > 0) {
    console.log(`${dim}Cleaned ${removed} previous TweakIdea file(s).${reset}`);
  }

  // Copy agents
  mkdirp(path.join(targetDir, 'agents'));
  for (const file of AGENT_FILES) {
    copyFileSync(
      path.join(sourceDir, 'agents', file),
      path.join(targetDir, 'agents', file)
    );
  }

  // Copy skills
  for (const dir of SKILL_DIRS) {
    copyDirSync(
      path.join(sourceDir, 'skills', dir),
      path.join(targetDir, 'skills', dir)
    );
  }

  // Copy commands
  if (isGlobal) {
    // Global: install as skills (Claude Code discovers skills/*/SKILL.md)
    for (const cmdSrc of COMMAND_FILES) {
      const skillName = cmdSrcToSkillName(cmdSrc);
      const skillDir = path.join(targetDir, 'skills', skillName);
      mkdirp(skillDir);
      copyFileSync(
        path.join(sourceDir, cmdSrc),
        path.join(skillDir, 'SKILL.md')
      );
    }
  } else {
    // Local: install as commands (Claude Code discovers commands/**/*.md)
    for (const cmdSrc of COMMAND_FILES) {
      copyFileSync(
        path.join(sourceDir, cmdSrc),
        path.join(targetDir, cmdSrc)
      );
    }
  }

  // Merge settings
  mergeSettings(targetDir);

  // Write version
  writeVersion(targetDir, pkg.version);

  // Verify
  const agentCount = AGENT_FILES.filter((f) =>
    fs.existsSync(path.join(targetDir, 'agents', f))
  ).length;
  const skillCount = SKILL_DIRS.filter((d) =>
    fs.existsSync(path.join(targetDir, 'skills', d))
  ).length;
  const commandCount = COMMAND_FILES.filter((cmdSrc) => {
    if (isGlobal) {
      const skillName = cmdSrcToSkillName(cmdSrc);
      return fs.existsSync(path.join(targetDir, 'skills', skillName, 'SKILL.md'));
    } else {
      return fs.existsSync(path.join(targetDir, cmdSrc));
    }
  }).length;

  console.log('');
  console.log(`${green}${bold}TweakIdea v${pkg.version} installed successfully!${reset}`);
  console.log('');
  console.log(`  ${dim}Location:${reset}  ${displayPath} (${location})`);
  console.log(`  ${dim}Agents:${reset}    ${agentCount} installed`);
  console.log(`  ${dim}Skills:${reset}    ${skillCount} installed`);
  console.log(`  ${dim}Commands:${reset}  ${commandCount} installed`);
  console.log('');
  // Check for uv (needed by suggest-from-hn)
  try {
    require('child_process').execSync('command -v uv', { stdio: 'ignore' });
  } catch {
    console.log(`  ${yellow}Note:${reset} /tweak:suggest-from-hn requires 'uv' (Python package runner)`);
    console.log(`  ${dim}Install: curl -LsSf https://astral.sh/uv/install.sh | sh${reset}`);
    console.log(`  ${dim}Or: brew install uv${reset}`);
    console.log('');
  }

  console.log(`${cyan}Get started:${reset}`);
  console.log(`  ${bold}/tweak:evaluate${reset} ${dim}"Your startup idea description"${reset}`);
  console.log(`  ${bold}/tweak:suggest-from-hn${reset} ${dim}<hn-url-or-id>${reset}`);
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

  cleanupPreviousInstall(targetDir);

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
