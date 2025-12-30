const { chromium } = require('playwright');

(async () => {
    console.log('');
    console.log('╔══════════════════════════════════════════════════════════════╗');
    console.log('║  FINAL VISIBLE TEST - WATCH YOUR SCREEN!                     ║');
    console.log('║  You should see the full research results this time.         ║');
    console.log('╚══════════════════════════════════════════════════════════════╝');
    console.log('');
    
    await new Promise(r => setTimeout(r, 2000));
    
    const browser = await chromium.launch({
        headless: false,
        slowMo: 150,
    });
    
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    // Clear localStorage for fresh start
    console.log('📍 Opening app...');
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(1000);
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForTimeout(2000);
    
    console.log('✍️ Typing "HVAC technician training"...');
    const textarea = await page.waitForSelector('textarea', { timeout: 10000 });
    await textarea.click();
    await textarea.fill('HVAC technician training');
    await page.waitForTimeout(1000);
    await page.keyboard.press('Enter');
    
    console.log('⏳ Waiting for clarifying questions (45 seconds)...');
    await page.waitForTimeout(45000);
    
    console.log('✍️ Answering clarification questions...');
    const textarea2 = await page.waitForSelector('textarea', { timeout: 5000 });
    await textarea2.click();
    await textarea2.fill('Complete beginners targeting residential and commercial HVAC. Based in USA. 6 month program.');
    await page.waitForTimeout(1000);
    await page.keyboard.press('Enter');
    
    console.log('⏳ Watching Phase 1 Research (watch the screen - 5 minutes)...');
    console.log('');
    console.log('   You should see:');
    console.log('   - Search status indicators');
    console.log('   - Thinking steps');
    console.log('   - Course listings with pricing streaming in');
    console.log('');
    
    // Wait 5 minutes for research
    await page.waitForTimeout(300000);
    
    await page.screenshot({ path: 'final-visible-result.png', fullPage: true });
    console.log('📸 Screenshot saved');
    
    console.log('✅ Done! Browser stays open for 60 more seconds...');
    console.log('   You can continue interacting - type "continue" for Phase 2!');
    await page.waitForTimeout(60000);
    
    await browser.close();
})();
