const { chromium } = require('playwright');

(async () => {
    console.log('');
    console.log('╔══════════════════════════════════════════════════════════════╗');
    console.log('║  FULL TEST - Watch Phase 1 Research Results                  ║');
    console.log('╚══════════════════════════════════════════════════════════════╝');
    console.log('');
    
    await new Promise(r => setTimeout(r, 3000));
    
    const browser = await chromium.launch({
        headless: false,
        slowMo: 200,
    });
    
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    console.log('📍 Opening app...');
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(2000);
    
    console.log('✍️ Typing topic...');
    const textarea = await page.waitForSelector('textarea', { timeout: 10000 });
    await textarea.click();
    await textarea.fill('HVAC technician training');
    await page.waitForTimeout(1000);
    
    console.log('📤 Submitting topic...');
    await page.keyboard.press('Enter');
    
    console.log('⏳ Waiting for clarifying questions (60s)...');
    await page.waitForTimeout(60000);
    
    // Screenshot after clarifying questions
    await page.screenshot({ path: 'step1-clarification.png', fullPage: true });
    console.log('📸 Saved: step1-clarification.png');
    
    // Answer the clarifying questions
    console.log('✍️ Answering clarification questions...');
    const textarea2 = await page.waitForSelector('textarea', { timeout: 5000 });
    await textarea2.click();
    await textarea2.fill('Target: complete beginners. Region: USA. Focus: both residential and commercial. Duration: 3-6 months program.');
    await page.waitForTimeout(1500);
    
    console.log('📤 Submitting answers - Starting Phase 1 Research...');
    await page.keyboard.press('Enter');
    
    console.log('⏳ Watching Phase 1 Competitive Research (4 minutes)...');
    console.log('   You should see courses, pricing, lessons appearing...');
    await page.waitForTimeout(240000); // 4 minutes for research
    
    // Screenshot after Phase 1
    await page.screenshot({ path: 'step2-phase1-result.png', fullPage: true });
    console.log('📸 Saved: step2-phase1-result.png');
    
    console.log('✅ Test complete! Browser stays open for 60 more seconds...');
    await page.waitForTimeout(60000);
    
    await browser.close();
})();
