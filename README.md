# 激活虚拟环境
conda activate aicodeskill

# 运行
python main.py

#执行push
git push origin main

# 多智能体运行
## 默认测试模式
python multi_agent_main.py
## 交互模式
python multi_agent_main.py -i
## 串行协作示例
python multi_agent_main.py -seq
## 并行协作示例
python multi_agent_main.py -par

# api server
python api_server.py

# 前端编排界面
cd frontend && npm run dev

# 运行导出的工作流配置
## 单次执行
python run_workflow.py workflow.json "你的输入内容"
## 交互模式
python run_workflow.py workflow.json -i

# Skill_Seekers使用并生成skills
---git clone https://github.com/yusufkaraaslan/Skill_Seekers.git
cd /Users/shaoqiang/work/workspace/lowcodeUI/Skill_Seekers
pip install -r requirements.txt
# 方法一：使用通配符处理所有PDF
skill-seekers pdf --pdf dosc/bc.pdf --name agknowdoc 

# 方法二：处理单个PDF
python3 cli/pdf_scraper.py --pdf "~/docs/your_document.pdf" --name 项目文档 --output_dir "./skills"