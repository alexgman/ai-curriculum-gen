const { chromium } = require('playwright');

(async () => {
    console.log('');
    console.log('╔══════════════════════════════════════════════════════════════╗');
    console.log('║  FULL VISIBLE TEST - WATCH YOUR SCREEN!                      ║');
    console.log('║  Chrome browser will open in 3 seconds...                    ║');
    console.log('╚══════════════════════════════════════════════════════════════╝');
    console.log('');
    
    await new Promise(r => setTimeout(r, 3000));
    
    const browser = await chromium.launch({
        headless: false,
        slowMo: 200,
    });
    
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1400, height: 900 });
    
    // Step 1: Open app
    console.log('📍 Step 1: Opening http://localhost:3000...');
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(3000);
    
    // Step 2: Type topic
    console.log('✍️ Step 2: Typing "HVAC technician training course"...');
    const textarea = await page.waitForSelector('textarea', { timeout: 10000 });
    await textarea.click();
    await textarea.fill('HVAC technician training course');
    await page.waitForTimeout(2000);
    
    // Step 3: Submit
    console.log('📤 Step 3: Submitting topic...');
    await page.keyboard.press('Enter');
    
    // Step 4: Wait for clarifying questions
    console.log('⏳ Step 4: Waiting for Claude to ask clarifying questions (up to 60 seconds)...');
    await page.waitForTimeout(60000);
    
    // Step 5: Answer clarifying questions
    console.log('✍️ Step 5: Answering clarification questions...');
    const textareaAfter = await page.waitForSelector('textarea', { timeout: 5000 });
    await textareaAfter.click();
    await textareaAfter.fill('Target audience: complete beginners. Focus: both residential and commercial. Region: United States. Include all major certifications like EPA 608 and NATE.');
    await page.waitForTimeout(2000);
    
    // Step 6: Submit answers
    console.log('📤 Step 6: Submitting answers...');
    await page.keyboard.press('Enter');
    
    // Step 7: Wait for Phase 1 research
    console.log('⏳ Step 7: Watching Phase 1 Competitive Research (3 minutes)...');
    console.log('   You should see:');
    console.log('   - Search progress');
    console.log('   - Thinking process');
    console.log('   - Course listings with pricing, duration, certifications');
    console.log('   - Lesson lists');
    console.log('');
    await page.waitForTimeout(180000); // 3 minutes
    
    // Step 8: Continue to Phase 2
    console.log('✍️ Step 8: Saying "continue" to Phase 2...');
    const textareaPhase2 = await page.waitForSelector('textarea', { timeout: 5000 });
    await textareaPhase2.click();
    await textareaPhase2.fill('continue');
    await page.keyboard.press('Enter');
    
    // Step 9: Watch Phase 2
    console.log('⏳ Step 9: Watching Phase 2 Industry Expertise (3 minutes)...');
    await page.waitForTimeout(180000); // 3 minutes
    
    // Step 10: Continue to Phase 3
    console.log('✍️ Step 10: Saying "continue" to Phase 3...');
    const textareaPhase3 = await page.waitForSelector('textarea', { timeout: 5000 });
    await textareaPhase3.click();
    await textareaPhase3.fill('continue');
    await page.keyboard.press('Enter');
    
    // Step 11: Watch Phase 3
    console.log('⏳ Step 11: Watching Phase 3 Consumer Sentiment (3 minutes)...');
    await page.waitForTimeout(180000); // 3 minutes
    
    // Step 12: Generate final synthesis
    console.log('✍️ Step 12: Saying "continue" for Final Synthesis...');
    const textareaFinal = await page.waitForSelector('textarea', { timeout: 5000 });
    await textareaFinal.click();
    await textareaFinal.fill('continue');
    await page.keyboard.press('Enter');
    
    // Step 13: Watch final synthesis
    console.log('⏳ Step 13: Watching Final Synthesis (3 minutes)...');
    await page.waitForTimeout(180000);
    
    console.log('');
    console.log('✅ Full test complete! Browser will stay open for 30 more seconds.');
    await page.waitForTimeout(30000);
    
    await browser.close();
    console.log('🏁 Done!');
})();
