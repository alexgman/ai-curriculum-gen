const { chromium } = require('playwright');

(async () => {
    console.log('');
    console.log('🚀 QUICK TEST - Watch browser for results');
    console.log('');
    
    await new Promise(r => setTimeout(r, 2000));
    
    const browser = await chromium.launch({
        headless: false,
        slowMo: 150,
    });
    
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    console.log('📍 Opening app...');
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(2000);
    
    // Click "New Research" to start fresh
    console.log('🆕 Starting new research session...');
    const newResearchBtn = await page.$('button:has-text("New Research")');
    if (newResearchBtn) {
        await newResearchBtn.click();
        await page.waitForTimeout(1000);
    }
    
    console.log('✍️ Typing topic...');
    const textarea = await page.waitForSelector('textarea', { timeout: 10000 });
    await textarea.click();
    await textarea.fill('HVAC technician training');
    await page.waitForTimeout(1000);
    await page.keyboard.press('Enter');
    
    console.log('⏳ Waiting for clarifying questions (45s)...');
    await page.waitForTimeout(45000);
    
    await page.screenshot({ path: 'quick-test-1.png', fullPage: true });
    console.log('📸 Screenshot 1: Clarifying questions');
    
    // Answer
    console.log('✍️ Answering...');
    const textarea2 = await page.waitForSelector('textarea', { timeout: 5000 });
    await textarea2.click();
    await textarea2.fill('Beginners, USA, residential and commercial, 6 months');
    await page.waitForTimeout(1000);
    await page.keyboard.press('Enter');
    
    console.log('⏳ Watching Phase 1 research (5 minutes)...');
    
    // Take screenshots every minute
    for (let i = 1; i <= 5; i++) {
        await page.waitForTimeout(60000);
        await page.screenshot({ path: `quick-test-phase1-${i}min.png`, fullPage: true });
        console.log(`📸 Screenshot at ${i} minute(s)`);
    }
    
    console.log('✅ Test complete! Browser stays open 60s...');
    await page.waitForTimeout(60000);
    
    await browser.close();
})();
