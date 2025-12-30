const { chromium } = require('playwright');

(async () => {
    console.log('🚀 Testing full output - Watch your screen!');
    
    const browser = await chromium.launch({ headless: false, slowMo: 100 });
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    // Log text content accumulation
    let textCount = 0;
    page.on('console', msg => {
        const text = msg.text();
        if (text.includes('chars') || text.includes('CONTENT')) {
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
    
    console.log('2. Waiting for clarification (35s)...');
    await page.waitForTimeout(35000);
    
    console.log('3. Answering...');
    const textarea2 = await page.waitForSelector('textarea');
    await textarea2.fill('Beginners, USA');
    await page.keyboard.press('Enter');
    
    console.log('4. Waiting for research (5min)...');
    console.log('   Should see course details streaming in...');
    await page.waitForTimeout(300000);
    
    // Get text content
    const content = await page.evaluate(() => {
        const msgs = document.querySelectorAll('.markdown-content');
        if (msgs.length > 0) {
            return msgs[msgs.length - 1].innerText.substring(0, 2000);
        }
        return '';
    });
    console.log('\n📄 Last message content (first 2000 chars):');
    console.log(content);
    
    await page.screenshot({ path: 'output-test.png', fullPage: true });
    console.log('\n✅ Done!');
    await page.waitForTimeout(30000);
    await browser.close();
})();
