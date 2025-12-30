const { chromium } = require('playwright');

(async () => {
    console.log('');
    console.log('╔══════════════════════════════════════════════════════════════╗');
    console.log('║  FINAL DEMO - Watch the complete curriculum research flow!   ║');
    console.log('║  Browser opens in 3 seconds...                               ║');
    console.log('╚══════════════════════════════════════════════════════════════╝');
    console.log('');
    
    await new Promise(r => setTimeout(r, 3000));
    
    const browser = await chromium.launch({
        headless: false,
        slowMo: 150,
    });
    
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    // Step 1: Open app
    console.log('');
    console.log('═══════════════════════════════════════════════════');
    console.log('  STEP 1: Opening the app');
    console.log('═══════════════════════════════════════════════════');
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(2000);
    
    // Step 2: Type topic
    console.log('');
    console.log('═══════════════════════════════════════════════════');
    console.log('  STEP 2: Entering research topic');
    console.log('═══════════════════════════════════════════════════');
    const textarea = await page.waitForSelector('textarea', { timeout: 10000 });
    await textarea.click();
    await textarea.fill('HVAC technician training course');
    await page.waitForTimeout(1000);
    await page.keyboard.press('Enter');
    
    // Step 3: Wait for clarifying questions
    console.log('');
    console.log('═══════════════════════════════════════════════════');
    console.log('  STEP 3: Watching Claude ask clarifying questions');
    console.log('  (Watch the thinking indicator and response)');
    console.log('═══════════════════════════════════════════════════');
    await page.waitForTimeout(60000);
    
    // Step 4: Answer questions
    console.log('');
    console.log('═══════════════════════════════════════════════════');
    console.log('  STEP 4: Answering clarification questions');
    console.log('═══════════════════════════════════════════════════');
    const textarea2 = await page.waitForSelector('textarea', { timeout: 5000 });
    await textarea2.click();
    await textarea2.fill('Target: complete beginners. Region: USA. Focus: both residential and commercial HVAC. Duration: 3-6 months.');
    await page.waitForTimeout(1000);
    await page.keyboard.press('Enter');
    
    // Step 5: Watch Phase 1
    console.log('');
    console.log('═══════════════════════════════════════════════════');
    console.log('  STEP 5: Phase 1 - Competitive Market Research');
    console.log('  Watch courses, pricing, lessons stream in...');
    console.log('═══════════════════════════════════════════════════');
    await page.waitForTimeout(300000); // 5 minutes
    
    // Screenshot
    await page.screenshot({ path: 'final-demo-result.png', fullPage: true });
    console.log('📸 Screenshot saved');
    
    console.log('');
    console.log('✅ Demo complete! Browser stays open for 2 minutes...');
    console.log('   You can continue interacting with the app!');
    console.log('   Type "continue" to go to Phase 2, etc.');
    await page.waitForTimeout(120000);
    
    await browser.close();
})();
