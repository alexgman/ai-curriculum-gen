const { chromium } = require('playwright');

(async () => {
    console.log('');
    console.log('🧹 CLEAN TEST - Watch the full flow!');
    console.log('');
    
    await new Promise(r => setTimeout(r, 2000));
    
    const browser = await chromium.launch({
        headless: false,
        slowMo: 200,
    });
    
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    // Open with hard refresh to clear any cached state
    console.log('📍 Opening app with fresh state...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // Clear localStorage to ensure fresh session
    await page.evaluate(() => {
        localStorage.clear();
    });
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    console.log('✍️ Typing topic...');
    const textarea = await page.waitForSelector('textarea', { timeout: 10000 });
    await textarea.click();
    await textarea.fill('HVAC technician training');
    await page.waitForTimeout(1000);
    
    console.log('📤 Submitting...');
    await page.keyboard.press('Enter');
    
    console.log('⏳ Waiting for clarifying questions (60s)...');
    await page.waitForTimeout(60000);
    
    await page.screenshot({ path: 'clean-test-1.png', fullPage: true });
    console.log('📸 Screenshot 1 saved');
    
    // Check if there's an error message
    const pageContent = await page.content();
    if (pageContent.includes('Error:')) {
        console.log('❌ Error detected on page!');
    }
    
    console.log('✍️ Answering clarification...');
    const textarea2 = await page.waitForSelector('textarea', { timeout: 5000 });
    await textarea2.click();
    await textarea2.fill('Complete beginners, USA, residential and commercial HVAC');
    await page.waitForTimeout(1000);
    await page.keyboard.press('Enter');
    
    console.log('⏳ Watching Phase 1 (3 minutes)...');
    await page.waitForTimeout(180000);
    
    await page.screenshot({ path: 'clean-test-2.png', fullPage: true });
    console.log('📸 Screenshot 2 saved');
    
    console.log('✅ Done! Browser stays open 60s...');
    await page.waitForTimeout(60000);
    
    await browser.close();
})();
