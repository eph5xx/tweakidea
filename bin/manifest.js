'use strict';

const SKILL_NAME = 'tweakidea';
const SKILL_SOURCE = 'skills/tweakidea';

const COMMANDS = [
  'analyze-hn-post',
  'browse-hn',
  'diff',
  'evaluate',
  'improve',
  'list',
  'share',
  'show',
];

const AGENTS = [
  'ti-evaluator',
  'ti-extractor',
  'ti-narrative',
  'ti-researcher',
];

module.exports = {
  SKILL_NAME,
  SKILL_SOURCE,
  COMMANDS,
  AGENTS,
};
