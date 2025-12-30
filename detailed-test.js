const { chromium } = require('playwright');

(async () => {
    console.log('🚀 Detailed test - checking content display');
    
    const browser = await chromium.launch({ headless: false, slowMo: 100 });
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    let eventCount = 0;
    let textEventCount = 0;
    let totalTextLength = 0;
    
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
    
    console.log('4. Waiting 4min for research...');
    await page.waitForTimeout(240000);
    
    // Get ALL message content from UI
    const messages = await page.evaluate(() => {
        const allContent = [];
        document.querySelectorAll('.markdown-content').forEach((el, i) => {
            allContent.push({
                index: i,
                length: el.innerText.length,
                preview: el.innerText.substring(0, 300),
                hasHVAC: el.innerText.includes('HVAC') || el.innerText.includes('Course'),
            });
        });
        return allContent;
    });
    
    console.log('\n📄 UI Messages found:');
    messages.forEach(m => {
        console.log(`  [${m.index}] Length: ${m.length}, HasHVAC: ${m.hasHVAC}`);
        console.log(`      Preview: ${m.preview.slice(0, 150)}...`);
    });
    
    // Scroll up to see content
    console.log('\n📜 Scrolling to top...');
    await page.evaluate(() => {
        const scrollArea = document.querySelector('.overflow-y-auto');
        if (scrollArea) scrollArea.scrollTop = 0;
    });
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'detailed-top.png' });
    
    // Scroll down
    await page.evaluate(() => {
        const scrollArea = document.querySelector('.overflow-y-auto');
        if (scrollArea) scrollArea.scrollTop = 2000;
    });
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'detailed-mid.png' });
    
    console.log('\n✅ Done!');
    await page.waitForTimeout(30000);
    await browser.close();
})();
