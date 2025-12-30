const { chromium } = require('playwright');

(async () => {
    console.log('');
    console.log('🚀 Testing ALL fixes - Watch your screen!');
    console.log('   - Reasoning container now expands');
    console.log('   - Smooth streaming (50 char updates)');
    console.log('   - Certifications on separate lines');
    console.log('   - Lessons inline with numbers');
    console.log('');
    
    const browser = await chromium.launch({ headless: false, slowMo: 100 });
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    await page.goto('http://localhost:3000');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForTimeout(2000);
    
    console.log('1. Typing topic...');
    const textarea = await page.waitForSelector('textarea');
    await textarea.fill('HVAC technician training');
    await page.keyboard.press('Enter');
    
    console.log('2. Waiting for clarification (45s)...');
    await page.waitForTimeout(45000);
    
    await page.screenshot({ path: 'fixes-step1.png' });
    console.log('📸 Step 1: Clarification saved');
    
    // Try to click on reasoning to expand
    try {
        const reasoningBtn = await page.$('button:has-text("reasoning")');
        if (reasoningBtn) {
            await reasoningBtn.click();
            await page.waitForTimeout(1000);
            await page.screenshot({ path: 'fixes-reasoning.png' });
            console.log('📸 Reasoning expanded saved');
        }
    } catch (e) {}
    
    console.log('3. Answering...');
    const textarea2 = await page.waitForSelector('textarea');
    await textarea2.fill('Complete beginners, USA, residential');
    await page.keyboard.press('Enter');
    
    console.log('4. Watching research (4min)...');
    await page.waitForTimeout(240000);
    
    await page.screenshot({ path: 'fixes-step2.png', fullPage: true });
    console.log('📸 Step 2: Research saved');
    
    console.log('✅ Done! Browser stays open 60s...');
    await page.waitForTimeout(60000);
    
    await browser.close();
})();
