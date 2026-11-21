#!/usr/bin/env node
// Ruflo pinned skill importer. No shell commands, no package install.
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve,relative,dirname,join,isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';

const a=process.argv.slice(2);
const arg=(k,d)=>{const i=a.indexOf(k);return i<0?d:a[i+1];};
const scope=arg('--scope','all');
const apply=a.includes('--apply');
if(!['published','all','core'].includes(scope))throw Error('Invalid scope');
if(apply&&scope!=='all')throw Error('Refusing to bulk-activate external skills. Import --scope all into passive vendor/ruflo/source, then promote individually after review.');
if(apply&&!a.includes('--i-reviewed-these-skills'))throw Error('Review before use and pass --i-reviewed-these-skills');
const base=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const m=JSON.parse(await readFile(join(base,'vendor/ruflo/skills-catalog.json'),'utf8'));
if(m.source!=='https://github.com/ruvnet/ruflo'||!/^[a-f0-9]{40}$/.test(m.sourceCommit))throw Error('Unexpected source revision');
const dest=resolve(arg('--dest',process.cwd()));
const files=[...m.files,...(scope==='all'?m.supportingFiles:[])].filter(x=>
 scope==='all'||(scope==='core'?x.path==='SKILL.md':x.kind==='plugin'&&x.advertised_group));
const destFor=x=>scope==='all'?join('vendor','ruflo','source',...x.path.split('/')):
 scope==='core'?join('.agents','skills','ruflo','SKILL.md'):join('.agents','skills','ruflo-'+x.name,'SKILL.md');
console.log('Scope='+scope+', files='+files.length+', apply='+apply+', destination='+dest);
if(files.length>419)throw Error('Invalid source inventory size');
if(!apply){for(const x of files)console.log(x.path+' -> '+destFor(x));process.exit(0);}
let added=0,unchanged=0;
for(const x of files){
 if(!/^[a-f0-9]{40}$/.test(x.blobSha)||x.mode!=='100644'||x.path.split('/').some(p=>!p||p==='.'||p==='..'||p.includes('\\')))throw Error('Invalid catalog path '+x.path);
 const outfile=resolve(dest,destFor(x)),rel=relative(dest,outfile);
 if(rel.startsWith('..')||isAbsolute(rel))throw Error('Refusing path escape');
 const url='https://raw.githubusercontent.com/ruvnet/ruflo/'+m.sourceCommit+'/'+x.path.split('/').map(encodeURIComponent).join('/');
 const res=await fetch(url,{signal:AbortSignal.timeout(20000),redirect:'error'});
 if(!res.ok)throw Error('Failed '+res.status+': '+x.path);
 const bytes=Buffer.from(await res.arrayBuffer());
 if(bytes.length>256*1024)throw Error('Oversized: '+x.path);
 const sha=createHash('sha1').update('blob '+bytes.length+'\0').update(bytes).digest('hex');
 if(sha!==x.blobSha)throw Error('SHA mismatch: '+x.path);
 await mkdir(dirname(outfile),{recursive:true});
 try{
  const old=await readFile(outfile);
  if(!old.equals(bytes))throw Error('Refusing to overwrite '+outfile);
  unchanged++;continue;
 }catch(e){if(e.code!=='ENOENT')throw e;}
 await writeFile(outfile,bytes,{flag:'wx'});added++;
}
console.log('Imported='+added+', identical='+unchanged+'. Runtime/MCP not installed.');
