// Optional real Tauri/WebView2 CDP acceptance. Does not claim physical sensor acceptance.
import {chromium} from 'playwright';import fs from 'node:fs';
let browser;
for(let i=0;i<60;i++){try{browser=await chromium.connectOverCDP('http://127.0.0.1:9222');break}catch(e){if(i===59)throw e;await new Promise(r=>setTimeout(r,500));}}
const context=browser.contexts()[0];let page;
for(let i=0;i<40;i++){page=context.pages().find(p=>!/[?&](overlay|pill|caption)(=|&|$)/.test(p.url()));if(page&&await page.locator('#root .app').count())break;await new Promise(r=>setTimeout(r,500));}
if(!page)throw Error('No actual Tauri workspace');const errors=[];page.on('pageerror',e=>errors.push(e.message));
if(!await page.evaluate(()=>!!window.__TAURI_INTERNALS__))throw Error('Not native Tauri');
const intro=page.getByRole('button',{name:'Skip intro',exact:true});if(await intro.isVisible())await intro.click();
await page.getByRole('button',{name:'DEX Coder',exact:true}).waitFor();
const connect=page.getByRole('button',{name:'Connect bundled core',exact:true});if(await connect.isVisible())await connect.click();
await page.getByRole('button',{name:'DEX Coder',exact:true}).click();
await page.getByRole('button',{name:'Settings',exact:true}).click();
await page.getByRole('button',{name:'Appearance',exact:true}).click();
await page.getByLabel('Font selector').selectOption('Verdana');
await page.getByRole('button',{name:'Privacy',exact:true}).click();
await page.getByRole('button',{name:'Allow app names',exact:true}).click();
await page.waitForFunction(()=>document.body.textContent.includes('Apps: on'));
await page.getByRole('button',{name:'Allow local context judgment',exact:true}).click();
await page.waitForFunction(()=>document.body.textContent.includes('Judgment on'));
await page.getByRole('button',{name:'Stop sensors and speech',exact:true}).click();
await page.waitForFunction(()=>document.body.textContent.includes('Apps: off')&&document.body.textContent.includes('Judgment off'));
if(context.pages().some(p=>p.url().includes('overlay=1')))throw Error('Removed avatar window recreated');
await page.screenshot({path:'ui-evidence/tauri-connected-renderer.png'});
if(errors.length)throw Error(errors.join('\n'));
fs.writeFileSync('ui-evidence/optional-native-cdp-checks.json',JSON.stringify({host:'actual Tauri2/WebView2',checks:['native frontend loaded','backend connection','persona select','font select','explicit process opt-in','local judgment opt-in','stop clears judgment/process state','avatar window absent'],model_requests:0,unrun:['physical laptop resources','microphone/audio','real model answer','native pill geometry','caption transparency']},null,2));
process.exit(0);
