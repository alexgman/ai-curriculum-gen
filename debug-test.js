const { chromium } = require('playwright');

(async () => {
    console.log('🚀 Debug test - watching network and console...');
    
    const browser = await chromium.launch({ headless: false, slowMo: 100 });
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    // Log console messages
    page.on('console', msg => {
        if (msg.text().includes('text') || msg.text().includes('char') || msg.text().includes('📝')) {
            console.log(`Browser: ${msg.text()}`);
        }
    });
    
    await page.goto('http://localhost:3000');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForTimeout(2000);
    
    console.log('1. Typing topic...');
    const textarea = await page.waitForSelector('textarea');
    await textarea.fill('HVAC technician training');
    await page.keyboard.press('Enter');
    
    console.log('2. Waiting 35s for clarification...');
    await page.waitForTimeout(35000);
    
    console.log('3. Answering...');
    const textarea2 = await page.waitForSelector('textarea');
    await textarea2.fill('Beginners, USA');
    await page.keyboard.press('Enter');
    
    console.log('4. Waiting 3min for research...');
    await page.waitForTimeout(180000);
    
    // Scroll to see content
    await page.evaluate(() => {
        const scrollArea = document.querySelector('.overflow-y-auto');
        if (scrollArea) scrollArea.scrollTop = 500;
    });
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'debug-result.png', fullPage: true });
    
    console.log('Done!');
    await page.waitForTimeout(30000);
    await browser.close();
})();
