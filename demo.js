const { chromium } = require('playwright');

(async () => {
    console.log('');
    console.log('╔═══════════════════════════════════════════════════╗');
    console.log('║  WATCH YOUR SCREEN - Demo starting in 3 seconds! ║');
    console.log('╚═══════════════════════════════════════════════════╝');
    console.log('');
    
    await new Promise(r => setTimeout(r, 3000));
    
    const browser = await chromium.launch({ headless: false, slowMo: 200 });
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    console.log('1. Opening app...');
    await page.goto('http://localhost:3000');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForTimeout(2000);
    
    console.log('2. Typing topic...');
    const textarea = await page.waitForSelector('textarea');
    await textarea.fill('HVAC technician training');
    await page.keyboard.press('Enter');
    
    console.log('3. Waiting for clarification questions...');
    await page.waitForTimeout(50000);
    
    console.log('4. Answering questions...');
    const textarea2 = await page.waitForSelector('textarea');
    await textarea2.fill('Complete beginners, USA, both residential and commercial');
    await page.keyboard.press('Enter');
    
    console.log('5. Watching Phase 1 research (5 minutes)...');
    console.log('   You should see course listings streaming in!');
    await page.waitForTimeout(300000);
    
    console.log('');
    console.log('✅ Demo complete! Browser stays open 2 more minutes.');
    console.log('   Try scrolling to see full content.');
    console.log('   Type "continue" for Phase 2!');
    await page.waitForTimeout(120000);
    
    await browser.close();
})();
