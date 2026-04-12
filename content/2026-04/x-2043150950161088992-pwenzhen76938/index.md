# 前两天我发Gemma 4的时候，在评论区留了一句：

- Source: https://x.com/PWenzhen76938/status/2043150950161088992
- Author: @PWenzhen76938
- Created: 2026-04-12T02:15:21Z

前两天我发Gemma 4的时候，在评论区留了一句：

> “我现在在测试一个想法：用 Gemma 4 做一个完全离线的个人知识库 Agent，所有数据在本地，所有推理在本地，没有 API 费用，没有隐私问题。如果测试顺利，我会分享具体的部署方案和我踩过的坑。”

现在测试结束了

我把整个过程、踩过的所有坑、最终方案一次性抛出来

完全真实操作记录，没有云端API，没有任何营销，纯个人复盘

---

我以前用ChatGPT/Claude做笔记，搜个人文档，总是心里不踏实：

- 输入客户资料、Space灵感稿、投资笔记时，总担心被用来训练
- 想让AI 24h随时分析我的推文 + 阅读记录，它动不动就断线、要钱
- 最重要的是：我想拥有一个真正属于自己的AI助手，不是租来的

Gemma 4 31B（量化后 17.4GB）+ 4090正好能跑

Apache 2.0协议又随便改，256K上下文能容一整本书去了

native function calling 又稳

这不就是离线个人知识库的完美底座吗？

于是我花了整整一个周末加上后续一周迭代，把它做成了现在这个完全离线的个人知识库Agent

---

我的最终硬件 & 环境（真实配置）

硬件

→ GPU：RTX 4090 24GB（31B Q4_K_M 量化后实测占用约 19-21GB VRAM，留 3GB 给 embedding 和系统）
→ CPU:AMD 7950X
→ 内存：64GB DDR5
→ 存储：2TB NVMe（知识库目前塞了约 1800 份 PDF+MD+Notion 导出）

 软件栈

→ Ollama（主力推荐，Mac/Linux/Windows 都能跑）
→ LlamaIndex（RAG框架，最稳）
→ nomic-embed-tex（本地embedding，中文支持好）
→ Chroma（向量库，本地持久化）
→ AnythingLLM（前端界面，可选，但我最后还是直接用LlamaIndex + Streamlit 更灵活）

---

完整部署方案（一步步手把手，可直接复制，因为不支持Markdown代码块渲染，所以我文字输出，复制时候对比下）

 1. 安装Ollama +拉模型（最简单一步）

```bash
# Mac/Linux/Windows 都一样
ollama pull gemma4:31b
# 官方直接用 gemma4:31b-it（instruct 版）
# 或者直接用量化好的 GGUF（HuggingFace 搜 google/gemma-4-31B-it-GGUF）
# 我最终用的是 Q4_K_M，速度和质量平衡最好
```

---

2. 准备embedding模型

```bash
ollama pull nomic-embed-text
```

---

3. 搭建RAG核心（LlamaIndex关键代码）

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

# 配置

Settings.llm = Ollama(model="gemma4:31b", request_timeout=300.0)
Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")
Settings.chunk_size = 1024  # 按需调整，1024 效果最好
Settings.chunk_overlap = 200

# 加载你的知识库文件夹（支持 PDF、MD、TXT、DOCX）
documents =
SimpleDirectoryReader("./my_knowledge_base").load_data()
index = VectorStoreIndex.from_documents(documents, show_progress=True)

# 持久化
http://index.storage_context.persist(persist_dir="./storage")
```

---

4. 把Agent 跑起来

我用LlamaIndex的ReAct Agent +自定义工具：

➤ 工具1：`query_knowledge_base`（检索我的所有笔记）
➤ 工具2：`save_to_note`（把新洞见自动保存回知识库）

核心 Prompt 我改成了：

> “你是我的私人AI研究员，只基于本地知识库回答，永远不要编造。如果不确定就说‘知识库中暂无相关记录’。”

---

 5. 前端界面（我用 Streamlit 5分钟搞好）

现在手机/电脑随时能用：

> “把我上周Space里聊的美股机制总结一下”，它秒出，还带来源引用

整个部署从0到能用，大概花了4小时（不包括后面调优）

---

完整踩坑记录（这些坑我全踩过，血泪教训）

坑1：OOM+ 上下文爆炸（最致命）

第一次直接扔256K 上下文 + 大文档，直接显存炸了

解决：

· 强制设置 `--ctx-size 8192` + KV cache用q4_0
· `chunk_size` 从2048降到1024
· 现在长文档也能稳稳处理

---

坑2：中文检索效果差

用默认bge-large-en，搜我的中文Space记录经常miss

解决：
· 换 `nomic-embed-text` + 手动加了中文stopwords过滤 +Hybrid Search（BM25+Vector）
· 命中率从60% 提到92%

---

坑3：Agent 幻觉+死循环

刚开始Agent老是“自信地”编造我没写过的东西，或者卡在循环里

解决：

➢ 强制加system prompt + 设置 `max_iterations=8` + 加入self-reflection step

---

坑 4：文档解析炸裂（尤其是PDF）

很多PDF是扫描稿或表格，直接拉稀

解决：

➢ 先用 LlamaParse 本地版或者 [http://unstructured.io](http://unstructured.io) 预处理，现在表格也能正常读了

---
坑 5：速度慢到想砸电脑

刚开始生成速度只有8-12 t/s

解决：
➢ 用Q4_K_M + 开启GPU offload（`n-gpu-layers=-1`）
➢ 现在实测稳定28-35 t/s，完全能接受

---

坑6：知识库更新麻烦

每次加新文件都要重新 build index

解决：

➢ 用了Incremental Index + 定时脚本，每天凌晨自动增量更新

---

现在这个Agent到底能干啥？（真实使用2周感受）

1. 问任何我去过的长文、Space记录、阅读笔记，它都能精准引出处

> 我：“上周我在DeFi项目笔记里提到过30天所有项目笔记做个对比表格”

> Agent:30 秒出完整Markdown表格

2. 让我把最近30天周读总结，发到Notion

自动帮我生成周读总结，发到 Notion

3. 最爽的是：完全离线，飞机上、地铁上、甚至断网也能用，隐私100%可控

这感觉真的不一样

它不再是云端租来的AI，而是长在我电脑里的私人研究员

---

 最后一点思考

Gemma 4 31B 把本地AI 的门槛真正拉到了一张高端显卡就能干大事的水平

我现在越来越相信：2026年的Web3+AI真正落地，可能不是链上训练，而是主权模型+主权数据+本地Agent

你呢？

➤已经在跑本地知识库Agent的，欢迎评论区分享你的方案**（尤其是踩过的坑）
➤还在犹豫要不要上Gemma 4 的，说说你最担心哪一步

我把完整代码、Modelfile、Streamlit前端全放GitHub了（评论“代码”我发链接）

纯个人复盘，所有数据和体验来自真实操作，不做任何推广
