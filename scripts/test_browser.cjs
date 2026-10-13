/* npm install --no-save playwright; node scripts/test_browser.cjs URL
   Optional PLAYWRIGHT_MODULE and CHROME_PATH for an existing local runtime. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const url=process.argv[2] || 'http://127.0.0.1:8766/';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{}),args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try {
 const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
 const errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
 await page.goto(url);
 await page.waitForFunction(()=>!document.querySelector('#wood-toggle').disabled,null,{timeout:60000});
 assert.equal(await page.locator('.material-control button').count(),3);
 await page.evaluate(()=>{
   const m=document.querySelector('model-viewer').model;
   const w=m.getMaterialByName('Madera'),s=m.getMaterialByName('Acero'),b=m.getMaterialByName('Bronce');
   window.originalTest={wc:w.pbrMetallicRoughness.baseColorTexture.texture,wr:w.pbrMetallicRoughness.metallicRoughnessTexture.texture,wn:w.normalTexture.texture,sc:[...s.pbrMetallicRoughness.baseColorFactor],sm:s.pbrMetallicRoughness.metallicFactor,bn:b.normalTexture.texture};
 });
 // Gray code walks all eight combinations without resetting the page.
 const sequence=[0,1,3,2,6,7,5,4,0];
 let current=0, checks=0;
 for(let cycle=0;cycle<3;cycle++) for(const mask of sequence){
   const delta=current^mask;
   for(const [bit,id] of [[1,'wood'],[2,'steel'],[4,'bronze']]) if(delta&bit) await page.locator(`#${id}-toggle`).click();
   current=mask;
   const good=await page.evaluate(mask=>{
      const m=document.querySelector('model-viewer').model,o=window.originalTest;
      const w=m.getMaterialByName('Madera'),s=m.getMaterialByName('Acero'),b=m.getMaterialByName('Bronce');
      const worn=Boolean(mask&1),dark=Boolean(mask&2),relief=!(mask&4);
      return (w.pbrMetallicRoughness.baseColorTexture.texture!==o.wc)===worn && (w.pbrMetallicRoughness.metallicRoughnessTexture.texture!==o.wr)===worn && (w.normalTexture.texture!==o.wn)===worn && JSON.stringify(s.pbrMetallicRoughness.baseColorFactor)===JSON.stringify(dark?[.25,.29,.32,1]:o.sc) && s.pbrMetallicRoughness.metallicFactor===o.sm && b.normalTexture.texture===(relief?o.bn:null) && document.querySelector('#wood-toggle').getAttribute('aria-pressed')===String(worn) && document.querySelector('#steel-toggle').getAttribute('aria-pressed')===String(dark) && document.querySelector('#bronze-toggle').getAttribute('aria-pressed')===String(relief);
   },mask);
   assert.ok(good,`Material state failed at ${mask}`);checks++;
 }
 await page.locator('#wood-toggle').focus();await page.keyboard.press('Space');
 assert.equal(await page.locator('#wood-toggle').getAttribute('aria-pressed'),'true');
 await page.keyboard.press('Space');
 const out=path.resolve(__dirname,'../work/qa');fs.mkdirSync(out,{recursive:true});
 await page.screenshot({path:path.join(out,'desktop.png'),fullPage:true});
 await page.locator('#wood-toggle').click();await page.locator('#steel-toggle').click();await page.locator('#bronze-toggle').click();
 await page.screenshot({path:path.join(out,'alternative-materials.png'),fullPage:true});
 await page.locator('#wood-toggle').click();await page.locator('#steel-toggle').click();await page.locator('#bronze-toggle').click();
 await page.evaluate(()=>document.querySelector('model-viewer').cameraOrbit='180deg 85deg 2.3m');
 await page.waitForTimeout(800);await page.screenshot({path:path.join(out,'rear.png'),fullPage:true});
 await page.evaluate(()=>document.querySelector('model-viewer').cameraOrbit='-17deg 83deg 2.3m');
 for(const width of [390,768,1024,1440]){
   await page.setViewportSize({width,height:844});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`Overflow at ${width}`);
   if(width===390){await page.waitForTimeout(600);await page.screenshot({path:path.join(out,'mobile.png'),fullPage:true});}
 }
 assert.deepEqual(errors,[]);
 // A broken model must produce a readable error and disabled controls.
 const broken=await browser.newPage();
 await broken.route('**/*.glb',route=>route.abort());
 await broken.goto(url);await broken.locator('#viewer-error').waitFor({state:'visible'});
 assert.equal(await broken.locator('.material-control button:disabled').count(),3);
 await broken.close();
 const report={url,passed:true,material_state_checks:checks,combinations:8,repetitions:3,keyboard:true,widths:[390,768,1024,1440],load_error_handling:true,console_errors:errors,browser:await browser.version()};
 fs.writeFileSync(path.resolve(__dirname,'../docs/browser-verification.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
