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