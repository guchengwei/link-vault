# 看多了前端已死，程序员要被淘汰了，这次终于轮到 marketing 了？

- Source: https://x.com/chuhaiqu/status/2045061966428041272
- Author: @chuhaiqu
- Created: 2026-04-17T08:49:02Z

看多了前端已死，程序员要被淘汰了，这次终于轮到 marketing 了？

Anthropic 有个非技术背景的人，一个人扛了 10 个月的 growth marketing。

他做的事其实已经不太像 marketing 了：

历史广告数据喂给 Claude Code，先分析哪些文案差，再直接生成新版本
headline 和 description 拆给不同 sub-agent，再接 Figma plugin 批量出图
然后喂给 Meta Ads 的 MCP server，直接问 Claude 哪些广告在浪费预算
最后加一个 memory system，让每轮实验结果进入下一轮。

这套东西看下来，会感觉未来很多公司缺的可能是一个会搭 agent、接数据、做闭环的人。

作者这类人起个新名字，Distribution Engineer（未来真的都是AI 加持下的复合型人才了）！

## Quoted article
### Marketing is dead. Long live The Distribution Engineer.
- Source: https://x.com/GRITCULT/status/2044378810489913809
- Author: @GRITCULT
- Created: 2026-04-15T11:34:25Z

Marketing is dead. Long live The Distribution Engineer.

Your entire marketing department is about to be replaced by one person with an AI agent swarm. This is how it happens, who survives, and why the most important job title in tech doesnt exist yet.

![](assets/image-01.jpg)

For decades the engineer was God.

The person who could build the thing held all the power. Everyone else, the marketers, the operators, sales, bd, the "growth people", sat around waiting for the engineer to finish so they could do their jobs.

The entire hierarchy of tech was built on one bottleneck: who can ship code.

That era is over. Not ending. Over.

Claude, GPT, Codex, whatever model drops next month, they are collapsing the engineering moat in real time. A non-technical founder can ship a product in a weekend now. A solo operator can build an entire SaaS in a week. I have seen this happen multiple times this year alone.

The ability to "build the thing" is no longer rare. Its rapidly approaching commodity.

What is scarce now?

The Word Itself Is Wrong

“Marketing” is dead. The very name is the problem. it itself focused on an act. You market - you do something. In the age of AI you can delegate doing to an always on AI Agent. It doesnt make sense to think about this in the 19th century sense where you have to do something manually.

Not "marketing" in the way your corporate LinkedIn friends mean it. Not brand guidelines and quarterly content calendars and "aligning with stakeholders" in a room full of people who dont make anything.

The actual, technical, unglamorous work of making a human being on the internet see your thing, care about your thing, and tell another human being about your thing.

So how to think about the future? Why is a16z focusing so much on creating its own content and channels? Why is every company turning into a media company?

Distribution.

The person who can do this, and build the systems to do it at scale, is the most valuable person in any room in 2026. They just dont have a title yet.

So lets give them one.

The new paradigm

The Distribution Engineer.

Or for the more senior: Chief Distribution Officer.

What this actually looks like technically?

A Distribution Engineer is not a marketer. They are not a growth hacker. They are not a "GTM strategist" with a Notion board full of OKRs and a Loom library nobody watches.

A builder who treats distribution like an engineering problem. Infrastructure, not campaigns.

They dont run campaigns. They build the agents that run them.

They dont write copy by hand. They build systems that generate, test, and iterate on hundreds of variations while they sleep.

They dont sit in the Meta Ads dashboard refreshing metrics at 2am. They build an MCP server that connects their AI directly to live campaign data so they can ask "where am i wasting spend" and get a real answer in seconds without ever opening the dashboard.

This is not theoretical.

The Most Insane Example Ive Seen This Year.

Anthropic. $380 billion company. The company that builds Claude.

Their entire growth marketing operation was run by ONE person for 10 months. A single non-technical human doing paid search, paid social, app store optimization, email marketing, and SEO. For one of the most valuable AI companies on the planet.

How?

He exports all his existing ads and performance data into a CSV. CTRs, CPMs, conversions, spend, everything. Feeds the entire file into Claude Code. Claude analyses the data, flags whats underperforming, and generates new copy variations on the spot.

He splits the work into two specialised sub-agents. One that only writes headlines, capped at 30 characters. One that only writes descriptions, capped at 90 characters. Each agent is tuned to its specific constraint so the output quality is way higher than cramming both into a single prompt. This is agent architecture applied to ad copy. This is systems thinking and systems engioneering. This is a whole different solution to this problem of getting it infront of people, and making them care and making them buy. And it fundamentally requires a different level of thinking. This is also why many people that were brought up into the old legacy system are struggling to adapt.

Then he built a Figma plugin that takes all those new headlines and descriptions, finds the ad templates in his Figma files, and automatically swaps the copy into each one. Up to 100 ready-to-publish ad variations generated at half a second per batch. What used to take hours of duplicating frames and copy-pasting text by hand, gone.

For performance tracking he built an MCP server connected to the Meta Ads API. Ask Claude which ads performed best this week. Get real answers from live data. No dashboard. No manual reporting.

And the part that closes the entire loop: a memory system that logs every hypothesis and every experiment result across iterations. So when he generates the next batch, Claude automatically pulls in what worked and what didnt from every previous round.

A self evolving system - not available in any saas, custom made for his unique flows and products.

Ad creation went from 2 hours to 15 minutes. 10x more creative output. More variations tested across more channels than most full marketing teams.

Again this cant be framed as "marketing". Marketing is dead.

That is not marketing. That is engineering applied to distribution. One person outperforming an entire department because he built the system instead of doing the work manually.

Thats the Distribution Engineer.

The Four Levels. Most People Are At The Bottom.

The Anthropic growth team mapped this out and it is the clearest framework Ive seen.

Level 1: Automate what you already do. Reporting, copy, data pulls. You replaced a few hours of grunt work. You are not ahead. You are slightly less behind. This is table stakes. Everyone will be here within 6 months.

Level 2: Use AI as a thinking partner where its better than you. Build a marketing knowledge base with your in-house data, competitor research, previous campaigns. Hook up multiple models running in parallel, Claude, GPT, Gemini. Throw a rough idea in and get back ten execution paths, each grounded in what your company already tried and what your competitors are doing.

It requires you to actually build something. And most marketers dont build. They operate. They “market”

Level 3: Do work that was below the ROI threshold before. Mining negative keywords across every ad group. Monitoring every competitor move in real time. Turning every webinar into a brand-voice article, refreshed weekly. This work always existed in theory. Nobody had the hours for it.

The Distribution Engineer has the hours because they built agents that dont sleep.

Level 4: Build custom tools only you would ever build. Your business has specific data, specific workflows, specific edge cases that no generic tool covers. The people building around their own specific problems are the ones pulling away from everyone else. This is where the ROI compounds. This is where one person starts outperforming entire departments.

The Distribution Engineer lives at 3 and 4.

The Most Dangerous Person In Tech Right Now.

Building. Plus psychology. Plus audience. In one body.

The overlap of all these skills. Thats the most dangerous person in tech right now. You want people who have their audience, their own channels, and you wanna hire them to rent those channels.

The most valuable people to hire right now are people with large followings, who are technical, who can understand both worlds. Building and crowd psychology.

This is why so many people are tryying to replicate what cluely have done. No one knows what their product does, but they know they have distribution.

Heres the thing that nobody in traditional marketing wants to hear and nobody in engineering wants to admit.

The most valuable skill to have right now is the ability to learn.

If you can learn, you can adapt.You can be taught.AI can do the teaching.

That is a completely different muscle than writing code or architecting systems. Marketing is fuzzy. Emotional. Irrational. Most engineers have never trained this muscle because theyve spent their entire careers in the land of clearly defined problems with clearly defined solutions.

Flip side. The best thing any marketer can do right now is learn how to build. Claude Code is free. Cursor exists. The barrier to becoming technical has never been lower in human history and it will never be this low again because next month it will be even lower and someone else will have already started.

Computer science school in 2026 should basically be half technical knowledge, half distribution knowledge.

The people who figure this out early, who realise that building the thing and getting the thing into peoples hands are now the same skill set, those are the people who eat everything.

The One Person Army Is Not A Meme.

A single Distribution Engineer with the right stack can do what took a team of ten.

Research real prospects. Score accounts against your ICP. Write personalised outreach sequences. Build repeatable pipelines. Generate entire content calendars. Create pitch decks. Monitor competitor moves in real time. Automate all reporting. Build custom workflows that replace three tools youre currently paying for.

One person. Not a department. Not a team. Not an agency retainer.

The Anthropic growth team proved it.

This is why the language around these roles is shifting. People are calling it "GTM Engineering" and "Marketing Engineering" and "Growth Systems" because the old titles dont capture whats actually happening. The work has become technical. The people doing it are builders. The playbook is agents, MCP servers, and infrastructure, not campaigns, calendars, and committee meetings.

Some people are framing this as marketing getting "rebranded" to sound more serious. More technical. More masculine. And maybe theres some truth in that, guys have always loved marketing, they just hated corporate marketing culture so they started YouTubing or podcasting or running ads instead. But the deeper reality is simpler.

The work itself changed.

Distribution in 2026 is a systems engineering problem. The title should reflect what the job actually requires.

The prescription

If you are a founder, your first hire should not be a "head of marketing" who builds decks and "aligns stakeholders" and goes to conferences. Your first hire should be a Distribution Engineer who builds the agents, automations, and systems that create an entirely new kind of go-to-market. Part builder, part strategist. The person who builds the machine, not the person who operates it.

The tools are already here.

One person with the right stack is worth more than a team of ten operating the old way.

Thats not a prediction. That's already happening. The Anthropic growth team proved it. And they wont be the last.

If youre building distribution systems with AI or working on GTM infrastructure, dm me. Would love to see what people are building.

-GRITCULT
