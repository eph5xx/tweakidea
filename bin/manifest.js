'use strict';

const AGENT_FILES = [
  'ti-evaluator.md',
  'ti-extractor.md',
  'ti-narrative.md',
  'ti-researcher.md',
];

const SKILL_DIRS = [
  'ti-scoring',
  'ti-founder',
  'ti-report',
  'ti-hnparse',
];

const COMMAND_FILES = [
  'commands/tweak/browse-hn.md',
  'commands/tweak/diff.md',
  'commands/tweak/evaluate.md',
  'commands/tweak/improve.md',
  'commands/tweak/list.md',
  'commands/tweak/show.md',
  'commands/tweak/analyze-hn-post.md',
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
