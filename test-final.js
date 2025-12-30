const { chromium } = require('playwright');

(async () => {
    console.log('🚀 Testing improved prompts - Watch screen!');
    
    const browser = await chromium.launch({ headless: false, slowMo: 100 });
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('chars') || text.includes('CONTENT') || text.includes('Phase')) {
            console.log(`  ${text}`);
        }
    });
    
    await page.goto('http://localhost:3000');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForTimeout(2000);
    
    console.log('1. Typing...');
    const textarea = await page.waitForSelector('textarea');
    await textarea.fill('HVAC technician training');
    await page.keyboard.press('Enter');
    
    console.log('2. Waiting 35s...');
    await page.waitForTimeout(35000);
    
    console.log('3. Answering...');
    const textarea2 = await page.waitForSelector('textarea');
    await textarea2.fill('Beginners, USA');
    await page.keyboard.press('Enter');
    
    console.log('4. Waiting 5min...');
    await page.waitForTimeout(300000);
    
    // Get message lengths
    const lengths = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('.markdown-content')).map(el => el.innerText.length);
    });
    console.log(`\n📊 Message lengths: ${lengths.join(', ')}`);
    
    await page.screenshot({ path: 'final-result.png', fullPage: true });
    console.log('✅ Done!');
    await page.waitForTimeout(30000);
    await browser.close();
})();
