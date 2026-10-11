import {build} from 'esbuild';
await build({entryPoints:['src/console.js'],outfile:'public/app.js',bundle:true,minify:true,format:'esm',target:['chrome109'],legalComments:'linked'});
console.log('Lisa owner console built.');
