const { chromium } = require('playwright');

(async () => {
    console.log('🚀 Opening app to capture full content...');
    
    const browser = await chromium.launch({ headless: false, slowMo: 100 });
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(2000);
    
    // Scroll up to see the beginning of content
    console.log('📜 Scrolling to top of content...');
    await page.evaluate(() => {
        const scrollArea = document.querySelector('.overflow-y-auto');
        if (scrollArea) scrollArea.scrollTop = 0;
    });
    await page.waitForTimeout(1000);
    
    await page.screenshot({ path: 'content-top.png', fullPage: false });
    console.log('📸 Screenshot 1: Top of content');
    
    // Scroll down a bit
    await page.evaluate(() => {
        const scrollArea = document.querySelector('.overflow-y-auto');
        if (scrollArea) scrollArea.scrollTop = 800;
    });
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'content-mid1.png', fullPage: false });
    console.log('📸 Screenshot 2: Middle 1');
    
    // Scroll more
    await page.evaluate(() => {
        const scrollArea = document.querySelector('.overflow-y-auto');
        if (scrollArea) scrollArea.scrollTop = 1600;
    });
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'content-mid2.png', fullPage: false });
    console.log('📸 Screenshot 3: Middle 2');
    
    console.log('✅ Done!');
    await page.waitForTimeout(30000);
    await browser.close();
})();
