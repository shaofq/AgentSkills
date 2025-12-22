const { chromium } = require('playwright');

(async () => {
  // 目标URL
  const TARGET_URL = 'https://ejj.jjshipping.cn/';
  
  console.log('正在启动浏览器...');
  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const page = await browser.newPage();
  
  try {
    // 访问网站
    console.log(`正在访问 ${TARGET_URL}`);
    await page.goto(TARGET_URL, { waitUntil: 'networkidle', timeout: 30000 });
    
    // 等待页面加载完成
    await page.waitForTimeout(2000);
    
    // 尝试查找并点击"在线订舱"相关的链接或按钮
    console.log('正在查找在线订舱功能...');
    
    // 可能的选择器 - 尝试多种方式找到在线订舱入口
    const bookingSelectors = [
      'text=在线订舱',
      'text=订舱',
      '[href*="booking"]',
      '[href*="order"]',
      '.booking',
      '#booking',
      'a[href*="booking"]',
      'button:has-text("订舱")'
    ];
    
    let foundBooking = false;
    for (const selector of bookingSelectors) {
      try {
        const elements = await page.$$(selector);
        if (elements.length > 0) {
          console.log(`找到在线订舱入口: ${selector}`);
          await elements[0].click();
          foundBooking = true;
          break;
        }
      } catch (e) {
        // 忽略选择器错误，继续尝试下一个
      }
    }
    
    if (!foundBooking) {
      // 如果没有找到特定的订舱按钮，尝试查找导航菜单中的相关项
      console.log('未找到明确的订舱按钮，尝试其他方式...');
      
      // 获取页面所有文本内容，查找包含"订舱"的元素
      const allTextElements = await page.$$('*');
      for (const element of allTextElements) {
        try {
          const text = await element.textContent();
          if (text && (text.includes('订舱') || text.includes('booking'))) {
            const tagName = await element.evaluate(el => el.tagName);
            if (tagName === 'A' || tagName === 'BUTTON') {
              console.log('通过文本内容找到订舱入口');
              await element.click();
              foundBooking = true;
              break;
            }
          }
        } catch (e) {
          // 忽略单个元素的错误
        }
      }
    }
    
    // 等待页面跳转或加载
    await page.waitForTimeout(3000);
    
    // 现在尝试获取表格数据的第一行
    console.log('正在获取数据表格的第一行...');
    
    // 尝试多种表格选择器
    const tableSelectors = [
      'table',
      '.table',
      '[class*="table"]',
      'tbody',
      '.data-table',
      '.result-table'
    ];
    
    let firstRowData = null;
    for (const tableSelector of tableSelectors) {
      try {
        const tables = await page.$$(tableSelector);
        if (tables.length > 0) {
          console.log(`找到表格: ${tableSelector}`);
          
          // 获取第一行数据（跳过表头）
          const rows = await tables[0].$$('tr');
          if (rows.length > 1) {
            // 第一行可能是表头，所以取第二行作为第一行数据
            const firstDataRow = rows[1];
            const cells = await firstDataRow.$$('td, th');
            
            const rowData = [];
            for (const cell of cells) {
              const text = await cell.textContent();
              rowData.push(text.trim());
            }
            
            firstRowData = rowData;
            console.log('成功获取第一行数据:', rowData);
            break;
          } else if (rows.length === 1) {
            // 如果只有一行，可能是数据行
            const cells = await rows[0].$$('td, th');
            const rowData = [];
            for (const cell of cells) {
              const text = await cell.textContent();
              rowData.push(text.trim());
            }
            firstRowData = rowData;
            console.log('成功获取第一行数据:', rowData);
            break;
          }
        }
      } catch (e) {
        // 忽略表格选择器错误
      }
    }
    
    if (!firstRowData) {
      // 如果没有找到表格，尝试获取页面上的其他数据结构
      console.log('未找到标准表格，尝试获取其他数据格式...');
      
      // 获取页面上所有可能包含数据的元素
      const dataContainers = await page.$$('[class*="data"], [class*="result"], .item, .row');
      if (dataContainers.length > 0) {
        // 获取第一个数据容器的内容
        const firstContainer = dataContainers[0];
        const containerText = await firstContainer.textContent();
        firstRowData = [containerText.trim()];
        console.log('从数据容器获取内容:', containerText.trim());
      }
    }
    
    if (!firstRowData) {
      // 最后的手段：获取整个页面的主要内容
      console.log('尝试获取页面主要内容...');
      const bodyText = await page.textContent('body');
      // 提取前几行有意义的内容
      const lines = bodyText.split('\n').filter(line => line.trim().length > 0);
      if (lines.length > 0) {
        firstRowData = [lines[0]];
        console.log('从页面主体获取第一行内容:', lines[0]);
      }
    }
    
    if (firstRowData) {
      console.log('\n=== 第一行数据结果 ===');
      console.log(JSON.stringify(firstRowData, null, 2));
      console.log('=====================');
    } else {
      console.log('❌ 未能找到任何数据');
    }
    
    // 截图保存以便调试
    await page.screenshot({ path: '/tmp/booking-screenshot.png', fullPage: true });
    console.log('📸 截图已保存到 /tmp/booking-screenshot.png');
    
  } catch (error) {
    console.error('❌ 执行过程中出现错误:', error.message);
    // 保存错误截图
    try {
      await page.screenshot({ path: '/tmp/booking-error.png', fullPage: true });
      console.log('📸 错误截图已保存到 /tmp/booking-error.png');
    } catch (e) {
      console.log('无法保存错误截图');
    }
  } finally {
    await browser.close();
    console.log('浏览器已关闭');
  }
})();
