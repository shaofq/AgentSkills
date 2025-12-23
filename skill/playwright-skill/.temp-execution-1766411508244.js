const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: false, 
    slowMo: 200,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  
  try {
    console.log('🚀 开始访问登录页面...');
    await page.goto('http://1.95.222.229:9001/', { 
      waitUntil: 'domcontentloaded',
      timeout: 30000 
    });
    
    // 等待页面完全加载
    await page.waitForTimeout(2000);
    
    console.log('📝 填写登录信息...');
    
    // 等待并填写用户名
    await page.waitForSelector('input[type="text"]', { timeout: 10000 });
    await page.fill('input[type="text"]', 'admin');
    console.log('✅ 用户名已填写');
    
    // 等待并填写密码
    await page.waitForSelector('input[type="password"]', { timeout: 10000 });
    await page.fill('input[type="password"]', '654321');
    console.log('✅ 密码已填写');
    
    // 查找并点击登录按钮
    await page.click('button:has-text("登录")', { timeout: 10000 });
    console.log('✅ 登录按钮已点击');
    
    // 等待登录完成
    console.log('⏳ 等待登录完成...');
    await page.waitForTimeout(5000);
    
    // 检查是否需要等待跳转
    const currentUrl = page.url();
    console.log(`📍 当前URL: ${currentUrl}`);
    
    // 尝试导航到船舶记录页面
    console.log('🚢 导航到船舶记录页面...');
    try {
      await page.goto('http://1.95.222.229:9001/?#/amis/shipRecord', {
        waitUntil: 'domcontentloaded',
        timeout: 30000
      });
      console.log('✅ 成功导航到船舶记录页面');
    } catch (navError) {
      console.log('⚠️ 直接导航失败，尝试修改URL...');
      // 尝试通过修改当前URL的方式
      await page.evaluate(() => {
        window.location.hash = '#/amis/shipRecord';
      });
      await page.waitForTimeout(3000);
    }
    
    // 等待页面加载
    await page.waitForTimeout(3000);
    
    console.log('🔍 查找船名输入框...');
    
    // 等待页面中的输入框加载
    await page.waitForSelector('input[type="text"]', { timeout: 10000 });
    
    // 查找船名输入框并填写
    const inputs = await page.$$('input[type="text"]');
    console.log(`📋 找到 ${inputs.length} 个文本输入框`);
    
    let shipNameFilled = false;
    for (let i = 0; i < inputs.length; i++) {
      const placeholder = await inputs[i].getAttribute('placeholder');
      console.log(`输入框 ${i + 1} placeholder: ${placeholder}`);
      
      if (placeholder && (placeholder.includes('船') || placeholder.includes('船舶') || placeholder.includes('Ship'))) {
        await inputs[i].fill('华浩21');
        console.log(`✅ 船名已填写: 华浩21 (输入框 ${i + 1})`);
        shipNameFilled = true;
        break;
      }
    }
    
    // 如果没有找到专门的船名输入框，使用第一个
    if (!shipNameFilled && inputs.length > 0) {
      await inputs[0].fill('华浩21');
      console.log('✅ 船名已填写: 华浩21 (使用第一个输入框)');
      shipNameFilled = true;
    }
    
    // 查找并点击查询按钮
    console.log('🔍 查找查询按钮...');
    
    // 查找所有按钮
    const buttons = await page.$$('button');
    console.log(`📋 找到 ${buttons.length} 个按钮`);
    
    for (let i = 0; i < buttons.length; i++) {
      const buttonText = await buttons[i].textContent();
      console.log(`按钮 ${i + 1} 文本: ${buttonText}`);
      
      if (buttonText && (buttonText.includes('查询') || buttonText.includes('搜索') || buttonText.includes('Search'))) {
        await buttons[i].click();
        console.log(`✅ 查询按钮已点击 (按钮 ${i + 1}: ${buttonText})`);
        break;
      }
    }
    
    // 等待查询结果
    console.log('⏳ 等待查询结果加载...');
    await page.waitForTimeout(5000);
    
    // 获取表格数据
    console.log('📊 获取表格数据...');
    
    // 尝试多种方式获取表格数据
    let tableData = [];
    
    // 方法1: 查找标准表格
    try {
      const tableRows = await page.$$('table tbody tr, .table tbody tr, .grid tbody tr');
      if (tableRows.length > 0) {
        const firstRow = tableRows[0];
        const cells = await firstRow.$$('td, th');
        for (const cell of cells) {
          const text = await cell.textContent();
          if (text && text.trim()) {
            tableData.push(text.trim());
          }
        }
        console.log(`✅ 通过标准表格获取到 ${tableData.length} 个数据`);
      }
    } catch (e) {
      console.log('标准表格方法失败');
    }
    
    // 方法2: 查找其他可能的表格结构
    if (tableData.length === 0) {
      try {
        const rows = await page.$$('[role="row"], .table-row, .grid-row');
        if (rows.length > 0) {
          const firstRow = rows[0];
          const cells = await firstRow.$$('[role="gridcell"], .cell, td');
          for (const cell of cells) {
            const text = await cell.textContent();
            if (text && text.trim()) {
              tableData.push(text.trim());
            }
          }
          console.log(`✅ 通过其他表格结构获取到 ${tableData.length} 个数据`);
        }
      } catch (e) {
        console.log('其他表格结构方法失败');
      }
    }
    
    // 方法3: 如果都失败了，尝试获取页面中包含"华浩"的文本
    if (tableData.length === 0) {
      console.log('🔍 尝试从页面文本中查找相关数据...');
      const pageText = await page.textContent('body');
      const lines = pageText.split('\n').map(line => line.trim()).filter(line => line);
      
      for (const line of lines) {
        if (line.includes('华浩21') || line.includes('华浩')) {
          console.log(`📋 找到相关行: ${line}`);
          tableData.push(line);
          break;
        }
      }
    }
    
    // 输出结果
    console.log('\n🎉 查询结果:');
    console.log('==========================================');
    
    if (tableData.length > 0) {
      // 尝试识别船名和船号
      let shipName = '';
      let shipNumber = '';
      
      // 从数据中查找船名和船号
      for (const data of tableData) {
        if (data.includes('华浩21') || data.includes('华浩')) {
          shipName = data;
          // 尝试提取船号
          const numberMatch = data.match(/(\d+)$/);
          if (numberMatch) {
            shipNumber = numberMatch[1];
          }
          break;
        }
      }
      
      console.log(`🚢 船名: ${shipName || tableData[0]}`);
      console.log(`🔢 船号: ${shipNumber || '未找到'}`);
      console.log('==========================================');
      console.log(`📊 完整数据: ${tableData.join(' | ')}`);
    } else {
      console.log('❌ 未找到表格数据');
      
      // 打印页面的部分内容用于调试
      const pageTitle = await page.title();
      console.log(`📄 页面标题: ${pageTitle}`);
      console.log(`📍 当前URL: ${page.url()}`);
    }
    
    // 截图保存
    await page.screenshot({ path: '/tmp/ship-record-result-v2.png', fullPage: true });
    console.log('📸 截图已保存到: /tmp/ship-record-result-v2.png');
    
  } catch (error) {
    console.error('❌ 执行过程中出现错误:', error.message);
    
    // 保存错误截图
    try {
      await page.screenshot({ path: '/tmp/ship-record-error-v2.png', fullPage: true });
      console.log('📸 错误截图已保存到: /tmp/ship-record-error-v2.png');
    } catch (e) {
      console.log('无法保存错误截图');
    }
  } finally {
    await browser.close();
    console.log('🏁 浏览器已关闭');
  }
})();
