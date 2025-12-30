const { chromium } = require('playwright');

(async () => {
    console.log('🚀 Starting visible test...');
    
    const browser = await chromium.launch({ headless: false, slowMo: 200 });
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    await page.goto('http://localhost:3000');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForTimeout(2000);
    
    console.log('✍️ Typing...');
    const textarea = await page.waitForSelector('textarea');
    await textarea.fill('HVAC technician training');
    await page.keyboard.press('Enter');
    
    console.log('⏳ Waiting 45s for clarification...');
    await page.waitForTimeout(45000);
    
    console.log('✍️ Answering...');
    const textarea2 = await page.waitForSelector('textarea');
    await textarea2.fill('Beginners, USA');
    await page.keyboard.press('Enter');
    
    console.log('⏳ Waiting 4min for research...');
    await page.waitForTimeout(240000);
    
    await page.screenshot({ path: 'visible-result.png', fullPage: true });
    console.log('📸 Done!');
    
    await page.waitForTimeout(30000);
    await browser.close();
})();
