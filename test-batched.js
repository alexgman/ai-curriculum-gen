const { chromium } = require('playwright');

(async () => {
    console.log('');
    console.log('🧪 TESTING WITH BATCHED UPDATES - Watch for full content!');
    console.log('');
    
    await new Promise(r => setTimeout(r, 2000));
    
    const browser = await chromium.launch({
        headless: false,
        slowMo: 150,
    });
    
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    // Clear and reload
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(1000);
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForTimeout(2000);
    
    console.log('✍️ Typing topic...');
    const textarea = await page.waitForSelector('textarea', { timeout: 10000 });
    await textarea.click();
    await textarea.fill('HVAC technician training');
    await page.waitForTimeout(1000);
    await page.keyboard.press('Enter');
    
    console.log('⏳ Waiting for clarifying questions (45s)...');
    await page.waitForTimeout(45000);
    
    console.log('✍️ Answering...');
    const textarea2 = await page.waitForSelector('textarea', { timeout: 5000 });
    await textarea2.click();
    await textarea2.fill('Beginners, USA, residential and commercial HVAC, 6 month program');
    await page.waitForTimeout(1000);
    await page.keyboard.press('Enter');
    
    console.log('⏳ Watching Phase 1 research (5 minutes)...');
    console.log('   Look for course listings with pricing!');
    await page.waitForTimeout(300000);
    
    await page.screenshot({ path: 'test-batched-result.png', fullPage: true });
    console.log('📸 Screenshot saved');
    
    console.log('✅ Done! Browser stays open 60s...');
    await page.waitForTimeout(60000);
    
    await browser.close();
})();
