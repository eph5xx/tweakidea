'use strict';

const AGENT_FILES = [
  'ti-evaluator.md',
  'ti-extractor.md',
  'ti-merger.md',
  'ti-researcher.md',
];

const SKILL_DIRS = [
  'ti-scoring',
  'ti-founder',
  'ti-html-report',
  'ti-hnparse',
];

const COMMAND_FILES = [
  'commands/tweak/evaluate.md',
  'commands/tweak/suggest-from-hn.md',
];

function cmdSrcToSkillName(cmdSrc) {
  return cmdSrc.replace('commands/', '').replace('.md', '').split('/').join('-');
}

module.exports = {
  AGENT_FILES,
  SKILL_DIRS,
  COMMAND_FILES,
  cmdSrcToSkillName,
};
