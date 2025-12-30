const { chromium } = require('playwright');

(async () => {
    console.log('');
    console.log('╔══════════════════════════════════════════════════════════════╗');
    console.log('║  WATCH YOUR SCREEN - Browser opening in 3 seconds!          ║');
    console.log('╚══════════════════════════════════════════════════════════════╝');
    console.log('');
    
    await new Promise(r => setTimeout(r, 3000));
    
    const browser = await chromium.launch({
        headless: false,
        slowMo: 300,
    });
    
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    console.log('📍 Opening app...');
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(3000);
    
    console.log('✍️ Typing "HVAC technician training"...');
    const textarea = await page.waitForSelector('textarea', { timeout: 10000 });
    await textarea.click();
    await textarea.fill('HVAC technician training');
    await page.waitForTimeout(1500);
    
    console.log('📤 Submitting...');
    await page.keyboard.press('Enter');
    
    console.log('⏳ Watching for Claude response (90 seconds)...');
    console.log('   You should see:');
    console.log('   - Thinking status updates');
    console.log('   - Research results streaming in');
    console.log('');
    
    await page.waitForTimeout(90000);
    
    // Take screenshot of result
    await page.screenshot({ path: 'test-result.png', fullPage: true });
    console.log('📸 Screenshot saved to test-result.png');
    
    console.log('✅ Test complete! Browser stays open for 30 more seconds...');
    await page.waitForTimeout(30000);
    
    await browser.close();
})();
