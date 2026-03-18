---
url: "https://www.bilibili.com/video/BV1fkPazmE3p/?spm_id_from=333.1007.tianma.1-3-3.click&vd_source=c9e7a539968fe2c068de834c08aab366"
source_type: bilibili
title: "独家访谈 | 虚拟细胞挑战赛困境何在"
author: "BioTender观测日志"
fetched_at: "2026-03-15T14:05:02.897632Z"
duration: 300.816
view_count: 387
like_count: 14
upload_date: "20260307"
has_transcript: true
transcript_method: "whisper"
platform: "BiliBili"
---

# 独家访谈 | 虚拟细胞挑战赛困境何在

**Author:** BioTender观测日志

本期邀请到了来自Mila的yuanxinyu师姐来分享一下她对虚拟细胞挑战赛的经历与认识


--- Transcript ---
Hello 大家好 我是Max
本期节目我们邀请到了来自米娜的原星域世界
来分享一下她对于虚拟细胞挑战赛的经历与认识
对 我觉得他们的那个尝试是一个很好的尝试吧
因为总得有人往前花一些钱
然后走一些路 然后去探路嘛 我觉得
但他们 比如说他们中间
11月吧 他们的指标有问题
就他们指标的实现其实有问题
然后被很多 而且包括他们去评测的这个方式也有问题
就讲得具体一点 就其实这个也很简单
就讲这些大概就是说 你的
你在做evaluation的时候 你这个
出销跟你的这个预测的这个销
你需要把这两个举证拿去做对比
买凡去计算一些metrics
然后这单个 比如说你的出销
你们有两类 一类是control销
一类是perturbs销
那他们的evaluation pipeline
就是没有对你提交的这两个举证
有一些细致的限制
这就导致了很多人他们发现
你可以通过一些
就是一些操作
就是比如你把
比如说你把那个
一些销的那个数值保证
保持为整数
就是那个很大的一个整数
然后你把另外一些数值保持
比如log完了之后的一个数
然后反那样去交
这是其中一个例子
然后他们他们就是那讨论挺机械
还有一些其他的就是这种
去hack的这种技术
有这种技术挺多的
然后导致当时很多提交 performance
大家其实觉得都很不靠谱
然后他们那个evaluation pipeline
应该也是
一开始他们一直不respond
然后直到快快结束的时候
可能过了大概
先四个周三个周百
他们可能才respond的一个
他们都现在这个evaluation没问题
然后然后就要这样这样结束
然后大家都很无语吧
我觉得了
然后为啥我要
我觉得我浪费的时间是因为
他们的那个data
我觉得他们用的那个data
有点太difficult了
就是或者怎么说呢
就他们他们用的是一个
genetic perturbation data
我觉得大概就不到
不到一个million的总量吧
然后是
pervation数量特别多
大概是几千还是几万
反正反正就说
你在同一个pervation上
你的有效的样本量
大概只有几百
这个东西非常难学
然后我们当时就是用一些
可能翻悉一点的model
就是比如像difusion这种
就是我们这个模型去试了一下
然后发现
他那个样本量不够
然后我们其实就学不好
然后我们后面就就let go了
但后来就是看那个结果出来之后
发现可能还是一些
就是更正统的偏
生性的方法
会更管用一些
然后也没办法说完
那确实人家生性
研究的比较深入
不是我们这种
搞AI的
就是跳进去能做的
对
就是如果不是功力的
去说这个事的话
其实谁也不知道
你这个所谓的
pervation到底应该怎么样做更好
但是如果说
就只举现在其中的一点点match上
然后不去把这个benchmarking给扩大
甚至我觉得他们现在这些
已有的这12个match
其实都是不够的
就如果不把这个benchmark做强的话
其实很难吸引到
其他领域
比如像做mash learning的人
去这个领域
去做一些technical上的一些尝试
比如之前protein为啥能发展那么快
一方面肯定是因为molecule和graph
之前已经火了
然后后面做molecule那些人
没东西做了
做protein
这是一波人
但还有一个比较重要的原因是
就是protein的benchmark做得很solid
就是你
你那个structure该啥样
你做应该啥样
然后你保证这个东西
unseen
那它这个structure就是unseen
那你这个东西是有保证的
那我是learning的人
一看你这个东西
你evaluation确定了
那我进来我就只需要刷个方法
那这东西我假都能跳进来水一水对吧
但如果
如果需要这一块benchmark没有搞定的话
其实我感觉很难吸引到
除了生性之外的人
包括像
像我们这种就做交叉的嘛
就除了我们这种就很难有人进来做