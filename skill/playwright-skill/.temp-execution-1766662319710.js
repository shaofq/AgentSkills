const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const page = await browser.newPage();

  try {
    // 打开百度
    console.log('正在打开百度...');
    await page.goto('https://www.baidu.com', { waitUntil: 'domcontentloaded' });
    console.log('✅ 百度首页加载成功');

    // 等待页面加载完成
    await page.waitForTimeout(2000);
    
    // 尝试多种方式定位搜索框
    console.log('正在输入搜索关键词：烟台岸基网络科技');
    
    // 使用 JavaScript 直接操作
    await page.evaluate(() => {
      const searchBox = document.getElementById('kw') || document.querySelector('input[name="wd"]');
      if (searchBox) {
        searchBox.value = '烟台岸基网络科技';
        searchBox.focus();
      }
    });
    
    // 等待一下
    await page.waitForTimeout(500);
    
    // 点击搜索按钮
    console.log('点击搜索按钮...');
    await page.evaluate(() => {
      const searchBtn = document.getElementById('su') || document.querySelector('input[type="submit"]');
      if (searchBtn) {
        searchBtn.click();
      }
    });
    
    // 等待搜索结果加载
    await page.waitForTimeout(3000);
    console.log('✅ 搜索完成');
    
    // 截图保存搜索结果
    await page.screenshot({ path: '/tmp/baidu-search-result.png', fullPage: true });
    console.log('📸 搜索结果截图已保存到 /tmp/baidu-search-result.png');
    
    // 等待一段时间以便查看结果
    console.log('浏览器将保持打开状态 30 秒，以便查看搜索结果...');
    await page.waitForTimeout(30000);
    
  } catch (error) {
    console.error('❌ 发生错误:', error.message);
    // 即使出错也截图
    try {
      await page.screenshot({ path: '/tmp/baidu-error.png', fullPage: true });
      console.log('📸 错误截图已保存到 /tmp/baidu-error.png');
    } catch (e) {}
  } finally {
    await browser.close();
    console.log('浏览器已关闭');
  }
})();
