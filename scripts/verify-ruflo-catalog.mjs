#!/usr/bin/env node
// Ruflo source catalog integrity. Read-only: it does not execute upstream code.
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const expected = '87f612cef121b50c2e31e2d3f88e46d88963a377';
const catalog = JSON.parse(await readFile(resolve(root, 'vendor/ruflo/skills-catalog.json'), 'utf8'));
if (catalog.source !== 'https://github.com/ruvnet/ruflo' ||
    catalog.sourceCommit !== expected ||
    catalog.sourceSubmodule?.revision !== expected ||
    catalog.sourceSubmodule?.path !== 'vendor/ruflo/upstream' ||
    catalog.sourceSubmodule?.inert !== true) throw Error('Pinned source/submodule contract mismatch');
const sourceFiles = catalog.files;
const helpers = catalog.supportingFiles;
if (catalog.sourceSkillFiles !== 403 || sourceFiles.length !== 403 ||
    catalog.supportingFileCount !== 16 || helpers.length !== 16) throw Error('Unexpected full source inventory size');
const all = [...sourceFiles, ...helpers];
const names = new Set();
let sourceBytes = 0;
for (const f of all) {
  if (typeof f.path !== 'string' || f.path.startsWith('/') ||
      f.path.includes('\\') || f.path.split('/').some(p => !p || p === '.' || p === '..') ||
      !/^[a-f0-9]{40}$/.test(f.blobSha || '') || f.mode !== '100644' ||
      !Number.isSafeInteger(f.bytes) || f.bytes < 0 || f.bytes > 256 * 1024 ||
      names.has(f.path)) throw Error('Unsafe/duplicate catalog entry: ' + f.path);
  names.add(f.path);
  sourceBytes += f.bytes;
}
if (sourceFiles.some(f => !f.path.endsWith('SKILL.md'))) throw Error('Non-skill path in SKILL.md source list');
const groups = catalog.groups || [];
const published = groups.flatMap(g => g.skills || []);
if (groups.length !== 34 || published.length !== 134 || new Set(published).size !== 134 ||
    catalog.advertisedSkills !== 134) throw Error('Official featured catalog mismatch');
for (const name of published) {
  if (!sourceFiles.some(f => f.kind === 'plugin' && f.name === name && f.advertised_group))
    throw Error('Featured skill missing in plugin tree: ' + name);
}
const rootSkill = sourceFiles.find(f => f.path === 'SKILL.md');
if (!rootSkill) throw Error('Root SKILL.md missing');
const bytes = await readFile(resolve(root, 'vendor/ruflo/source/SKILL.md'));
const sha = createHash('sha1').update('blob ' + bytes.length + '\0').update(bytes).digest('hex');
if (sha !== rootSkill.blobSha) throw Error('Root SKILL.md blob changed');
const modules = await readFile(resolve(root,'.gitmodules'),'utf8');
if (!modules.includes('path = vendor/ruflo/upstream') ||
    !modules.includes('url = https://github.com/ruvnet/ruflo.git')) throw Error('Submodule declaration missing');
console.log(JSON.stringify({
  status:'PASS',sourceCommit:expected,files:sourceFiles.length,
  supportingFiles:helpers.length,totalBytes:sourceBytes,
  featured:published.length,categories:groups.length,rootSkillSha:sha,
  limitation:'Full upstream source is a git submodule. This validates the inventory, not execution or security of each skill.'
},null,2));
