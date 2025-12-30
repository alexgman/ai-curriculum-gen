const { chromium } = require('playwright');

(async () => {
    console.log('Opening app to check content...');
    
    const browser = await chromium.launch({ headless: false, slowMo: 100 });
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(2000);
    
    // Scroll to top of chat
    console.log('Scrolling to top...');
    await page.evaluate(() => {
        const scrollArea = document.querySelector('.overflow-y-auto');
        if (scrollArea) scrollArea.scrollTop = 0;
    });
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'scroll-top.png' });
    
    // Scroll down incrementally
    for (let i = 1; i <= 5; i++) {
        await page.evaluate((pos) => {
            const scrollArea = document.querySelector('.overflow-y-auto');
            if (scrollArea) scrollArea.scrollTop = pos * 800;
        }, i);
        await page.waitForTimeout(500);
        await page.screenshot({ path: `scroll-${i}.png` });
        console.log(`Screenshot ${i} saved`);
    }
    
    console.log('Done! Browser open 30s...');
    await page.waitForTimeout(30000);
    await browser.close();
})();
