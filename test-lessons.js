const { chromium } = require('playwright');

(async () => {
    console.log('');
    console.log('🚀 Testing FULL lesson lists - Watch your screen!');
    console.log('');
    
    const browser = await chromium.launch({ headless: false, slowMo: 100 });
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
    
    console.log('2. Waiting for clarification (40s)...');
    await page.waitForTimeout(40000);
    
    console.log('3. Answering...');
    const textarea2 = await page.waitForSelector('textarea');
    await textarea2.fill('Complete beginners, USA, residential HVAC');
    await page.keyboard.press('Enter');
    
    console.log('4. Watching research (5min) - should see FULL lesson lists...');
    await page.waitForTimeout(300000);
    
    await page.screenshot({ path: 'full-lessons-test.png', fullPage: true });
    console.log('📸 Screenshot saved');
    
    console.log('✅ Done! Browser stays open 60s...');
    await page.waitForTimeout(60000);
    
    await browser.close();
})();
