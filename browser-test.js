const { chromium } = require('playwright');

async function testCurriculumBuilder() {
    console.log('🚀 Starting Browser UI Test...\n');
    
    const browser = await chromium.launch({ 
        headless: true,
        args: ['--no-sandbox']
    });
    const context = await browser.newContext({
        viewport: { width: 1400, height: 900 }
    });
    const page = await context.newPage();
    
    // Enable console logging from the page
    page.on('console', msg => console.log('    [Browser]', msg.text()));
    
    try {
        // Step 1: Navigate to the app
        console.log('📍 Step 1: Opening http://localhost:3000...');
        await page.goto('http://localhost:3000', { timeout: 30000, waitUntil: 'networkidle' });
        await page.waitForTimeout(3000);
        await page.screenshot({ path: '/home/ubuntu/Dev/ai-curriculum-gen/screenshot-1-home.png', fullPage: true });
        console.log('   ✅ Home page loaded\n');
        
        // Step 2: Find the textarea and type
        console.log('📍 Step 2: Typing topic "HVAC service technician"...');
        
        // Wait for textarea to be visible and ready
        const textarea = await page.waitForSelector('textarea', { timeout: 10000 });
        await textarea.click();
        await page.waitForTimeout(500);
        
        // Type the message
        await textarea.fill('HVAC service technician');
        await page.waitForTimeout(500);
        await page.screenshot({ path: '/home/ubuntu/Dev/ai-curriculum-gen/screenshot-2-typed.png', fullPage: true });
        console.log('   ✅ Topic typed\n');
        
        // Step 3: Submit by pressing Enter
        console.log('📍 Step 3: Submitting message (pressing Enter)...');
        await textarea.press('Enter');
        console.log('   ⏳ Message submitted, waiting for response...');
        
        // Wait for thinking indicator or message to appear
        await page.waitForTimeout(3000);
        await page.screenshot({ path: '/home/ubuntu/Dev/ai-curriculum-gen/screenshot-3-submitted.png', fullPage: true });
        console.log('   ✅ Screenshot after submit\n');
        
        // Step 4: Wait for Claude's clarification questions
        console.log('📍 Step 4: Waiting for Claude\'s response (20 seconds)...');
        await page.waitForTimeout(20000);
        await page.screenshot({ path: '/home/ubuntu/Dev/ai-curriculum-gen/screenshot-4-response.png', fullPage: true });
        console.log('   ✅ Response screenshot captured\n');
        
        // Step 5: Check if there are messages now
        const messageCount = await page.evaluate(() => {
            const messages = document.querySelectorAll('[class*="message"], [class*="Message"]');
            return messages.length;
        });
        console.log(`   📊 Found ${messageCount} message elements in DOM\n`);
        
        // Step 6: Answer clarification
        console.log('📍 Step 5: Answering clarification questions...');
        const textarea2 = await page.$('textarea');
        if (textarea2) {
            await textarea2.click();
            await textarea2.fill('Complete beginners, US market, residential HVAC, comprehensive course');
            await page.screenshot({ path: '/home/ubuntu/Dev/ai-curriculum-gen/screenshot-5-answer-typed.png', fullPage: true });
            
            await textarea2.press('Enter');
            console.log('   ✅ Answer submitted\n');
            
            // Wait for Phase 1
            console.log('📍 Step 6: Waiting for Phase 1 research (30 seconds)...');
            await page.waitForTimeout(30000);
            await page.screenshot({ path: '/home/ubuntu/Dev/ai-curriculum-gen/screenshot-6-phase1.png', fullPage: true });
            console.log('   ✅ Phase 1 screenshot captured\n');
        }
        
        // Final screenshot
        console.log('📍 Step 7: Final state...');
        await page.waitForTimeout(10000);
        await page.screenshot({ path: '/home/ubuntu/Dev/ai-curriculum-gen/screenshot-7-final.png', fullPage: true });
        
        // Debug: Print page content
        const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 1000));
        console.log('   📄 Page content preview:', bodyText.substring(0, 500));
        
        console.log('\n🎉 Browser test complete!');
        console.log('   Screenshots saved to: /home/ubuntu/Dev/ai-curriculum-gen/screenshot-*.png');
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        await page.screenshot({ path: '/home/ubuntu/Dev/ai-curriculum-gen/screenshot-error.png', fullPage: true });
    } finally {
        await browser.close();
    }
}

testCurriculumBuilder();
