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


