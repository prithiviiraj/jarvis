// Real Tauri WebView2 DOM/IPC test through test-only CDP, not a Chrome surrogate.
import {chromium} from 'playwright';import fs from 'node:fs';
let browser;
for(let i=0;i<60;i++){try{browser=await chromium.connectOverCDP('http://127.0.0.1:9222');break}catch(e){if(i===59)throw e;await new Promise(r=>setTimeout(r,500));}}
const context=browser.contexts()[0];let page;
for(let i=0;i<40;i++){page=context.pages().find(p=>!p.url().includes('overlay=1'));if(page&&await page.locator('#root .app').count())break;await new Promise(r=>setTimeout(r,500));}
if(!page)throw Error('No actual Tauri webview');let errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.getByRole('heading',{name:'A calm place to think.'}).waitFor({timeout:15000});
if(!await page.evaluate(()=>!!window.__TAURI_INTERNALS__))throw Error('Not native Tauri');
await page.getByRole('button',{name:'Connect local core'}).click();
await page.waitForFunction(()=>document.querySelector('.toolbar>span')?.textContent==='off');
await page.getByRole('button',{name:'DEX Coder'}).click();
await page.getByRole('heading',{name:'DEX',exact:true}).waitFor();
await page.getByLabel('Font selector').selectOption('Verdana');
await page.getByRole('button',{name:'Pause all'}).click();
await page.getByRole('button',{name:'Floating faces'}).click();
let faces;
for(let i=0;i<30;i++){faces=context.pages().find(p=>p.url().includes('overlay=1'));if(faces)break;await new Promise(r=>setTimeout(r,500));}
if(!faces)throw Error('Native floating window absent');
await faces.locator('.floating-team').waitFor();await faces.getByRole('button',{name:'LINK',exact:true}).click();
await faces.getByRole('button',{name:'STOP',exact:true}).click();
await faces.screenshot({path:'ui-evidence/tauri-floating-renderer.png'});
await page.screenshot({path:'ui-evidence/tauri-connected-renderer.png'});
if(errors.length)throw Error(errors.join('\n'));
fs.writeFileSync('ui-evidence/native-checks.json',JSON.stringify({host:'actual Tauri2/WebView2',checks:['native frontend loaded','explicit backend connect','persona select','font select','pause all','native floating window','overlay link','overlay stop'],models:0,sensors:0,unrun:['physical laptop resources','microphone/audio','real model answer','pixel transparency on user desktop']},null,2));
process.exit(0); // Leave host alive for the physical window screenshot/WM_CLOSE.
