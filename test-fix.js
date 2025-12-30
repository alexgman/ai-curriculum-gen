const { chromium } = require('playwright');

(async () => {
    console.log('');
    console.log('🚀 Testing FIXED version - Watch your screen!');
    console.log('');
    
    const browser = await chromium.launch({ headless: false, slowMo: 150 });
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    await page.goto('http://localhost:3000');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForTimeout(2000);
    
    console.log('1. Typing topic...');
    const textarea = await page.waitForSelector('textarea');
    await textarea.fill('HVAC technician training');
    await page.keyboard.press('Enter');
    
    console.log('2. Waiting for clarification (45s)...');
    await page.waitForTimeout(45000);
    
    await page.screenshot({ path: 'fix-step1.png' });
    console.log('📸 Step 1 saved');
    
    console.log('3. Answering...');
    const textarea2 = await page.waitForSelector('textarea');
    await textarea2.fill('Beginners, USA, residential');
    await page.keyboard.press('Enter');
    
    console.log('4. Watching research (4min) - content should stream in...');
    await page.waitForTimeout(240000);
    
    await page.screenshot({ path: 'fix-step2.png', fullPage: true });
    console.log('📸 Step 2 saved');
    
    console.log('✅ Done! Browser open 60s...');
    await page.waitForTimeout(60000);
    
    await browser.close();
})();
