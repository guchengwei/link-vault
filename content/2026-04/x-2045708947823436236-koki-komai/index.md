# あと10万インプくらい伸びたら消したほうがいい。

- Source: https://x.com/koki_komai/status/2045708947823436236
- Author: @koki_komai
- Created: 2026-04-19T03:39:55Z

あと10万インプくらい伸びたら消したほうがいい。

## Quoted article
### Claudeで使える超便利ツール20選
- Source: https://x.com/hata_AI_master/status/2045332262250795256
- Author: @hata_AI_master
- Created: 2026-04-18T02:43:06Z

Claudeで使える超便利ツール20選

この記事では、あらゆるAIモデルに追加して生産性を向上させることができる、20の強力なエージェントスキルを厳選してまとめました。
各スキルは .md

![](assets/image-01.jpg)

この記事では、あらゆるAIモデルに追加して生産性を向上させることができる、20の強力なエージェントスキルを厳選してまとめました。

各スキルは .md 形式で書かれており、これはClaudeの標準フォーマットです。ChatGPTやGeminiでスキルを使いたい場合も、ドキュメントをコピーして貼り付けるだけで利用できます。

スキルは5つのカテゴリに分類しており、これらのスキルをClaudeエージェントに簡単に追加する方法を示す動画ガイドも添付しています。

ライティング＆コンテンツ スキル

SCQAライティングフレームワーク

SCQAは、コミュニケーション、特にライティングやプレゼンテーションの構造化に使われるフレームワークです。以下の頭文字を取っています：

S = 状況（Situation） → 文脈を設定する。現在の状態や背景を説明し、読者が出発点を理解できるようにする。

C = 問題（Complication） → 状況を揺るがす問題、緊張、または課題を導入する。これがストーリーや議論を興味深くする要素。

Q = 問い（Question） → 問題から自然に生じる核心的な質問を提示する。読者は何を知りたいのか？

A = 回答（Answer） → 解決策、インサイト、または推奨事項を提供する。これが論理的に問いを解決する。

論理を伴うストーリーテリングと考えてください。コンサルティング、ビジネスライティング、コンテンツ制作で広く使われているのは、複雑なアイデアをわかりやすくするからです。

```
---
name: scqa-writing-framework
description: Structures content using the Situation, Complication, Question, Answer framework for clear, logical, and engaging narratives suitable for threads, articles, and reports.
（SCQAフレームワークを使用してコンテンツを構造化し、スレッド、記事、レポートに適した明確で論理的かつ魅力的なナラティブを作成する）
license: Complete terms in LICENSE.txt
---

# SCQA Writing Framework（SCQAライティングフレームワーク）

## Overview（概要）

Transforms unstructured ideas into structured, high-engagement content. It's perfect for educational material, storytelling, and technical explanations.
（未整理のアイデアを構造化された高エンゲージメントコンテンツに変換する。教育コンテンツ、ストーリーテリング、技術的な説明に最適）

**Keywords**: writing, storytelling, SCQA, structured content, clarity, narrative, article, thread

## Core Framework（コアフレームワーク）

### Situation（状況）
- Establish context, current state（文脈、現在の状態を確立する）
- Concise, clear, relevant（簡潔、明確、関連性がある）

### Complication（問題）
- Introduce problem or tension（問題や緊張を導入する）
- Create curiosity（好奇心を生み出す）

### Question（問い）
- Frame audience's key question（読者の核心的な質問をフレーミングする）
- Essential and natural（本質的かつ自然）

### Answer（回答）
- Deliver insight or solution（インサイトまたは解決策を提供する）
- Clear, actionable（明確、実行可能）

## Features（特徴）

- Logical progression（論理的な展開）
- Readability optimized（読みやすさを最適化）
- Curiosity-driven engagement（好奇心を刺激するエンゲージメント）

## Output Format（出力形式）

- SCQA blocks, short paragraphs, bullet highlights（SCQAブロック、短い段落、箇条書きのハイライト）

## Instructions（指示）

- Break input into SCQA sections（入力をSCQAセクションに分割する）
- Keep sentences concise（文を簡潔に保つ）
- Avoid unnecessary jargon（不要な専門用語を避ける）
- Maintain smooth flow（スムーズな流れを維持する）

## Constraints（制約条件）

- No skipped sections（セクションを飛ばさない）
- No repetition（繰り返しを避ける）
- Conciseness prioritized（簡潔さを優先する）
```

コンテンツ転用エンジン

```
---
name: content-repurposing-engine
description: Converts long-form content into multiple formats like social media threads, short video scripts, or summaries while preserving the core message.
（コアメッセージを保持しながら、長文コンテンツをSNSスレッド、短尺動画スクリプト、要約などの複数フォーマットに変換する）
license: Complete terms in LICENSE.txt
---

# Content Repurposing Engine（コンテンツ転用エンジン）

## Overview（概要）

Transforms blogs, notes, and articles into varied formats for different channels.
（ブログ、メモ、記事をさまざまなチャネル向けの多様な形式に変換する）

**Keywords**: content, repurposing, social media, threads, scripts, short-form, long-form

## Features（特徴）

- Extracts key ideas（重要なアイデアを抽出）
- Adapts for platforms（プラットフォームに合わせて適応）
- Maintains tone and clarity（トーンと明瞭さを維持）

## Output Format（出力形式）

- Platform-specific content（プラットフォーム別のコンテンツ）
- Structured sections（構造化されたセクション）
- Engaging headlines/hooks（魅力的な見出し／フック）

## Instructions（指示）

- Analyze original content（元のコンテンツを分析する）
- Identify key points（重要ポイントを特定する）
- Rewrite in target format（ターゲット形式で書き直す）
- Keep consistent tone and readability（一貫したトーンと読みやすさを保つ）

## Constraints（制約条件）

- Preserve meaning（意味を保持する）
- Avoid verbosity（冗長さを避ける）
- Format must match channel style（チャネルのスタイルに合わせる）
```

トーン＆スタイル統一ツール

```
---
name: tone-style-enforcer
description: Ensures all outputs match a consistent brand or personal tone, maintaining clarity, style, and audience alignment across multiple outputs.
（すべての出力が一貫したブランドまたは個人のトーンに合致するようにし、複数の出力にわたって明瞭さ、スタイル、オーディエンスとの整合性を維持する）
license: Complete terms in LICENSE.txt
---

# Tone & Style Enforcer（トーン＆スタイル統一ツール）

## Overview（概要）

Keeps all generated content in line with defined style guidelines or brand voice.
（すべての生成コンテンツを、定義されたスタイルガイドラインまたはブランドボイスに沿って統一する）

**Keywords**: style, tone, brand voice, consistency, clarity, writing

## Features（特徴）

- Tone preservation（トーンの保持）
- Consistency across outputs（出力間の一貫性）
- Formatting enforcement（フォーマットの統一）

## Output Format（出力形式）

- Text aligned with style guide（スタイルガイドに沿ったテキスト）
- Optional bullet structure（任意の箇条書き構造）
- Clean, professional（クリーンでプロフェッショナル）

## Instructions（指示）

- Apply defined tone to all input（定義されたトーンをすべての入力に適用する）
- Check for style inconsistencies（スタイルの不一致をチェックする）
- Adjust language, structure, and formatting（言語、構成、フォーマットを調整する）

## Constraints（制約条件）

- No deviation from selected tone（選択したトーンからの逸脱禁止）
- Maintain clarity（明瞭さを維持する）
```

長文→要約コンプレッサー

```
---
name: long-form-summary-compressor
description: Condenses long text into concise summaries, keeping essential ideas intact for quick consumption and understanding.
（長いテキストを、本質的なアイデアを損なわずに簡潔な要約に凝縮し、素早い理解を可能にする）
license: Complete terms in LICENSE.txt
---

# Long-Form to Summary Compressor（長文→要約コンプレッサー）

## Overview（概要）

Reduces complex content into digestible summaries for easy reading.
（複雑なコンテンツを読みやすい要約に圧縮する）

**Keywords**: summarization, long-form, clarity, conciseness, insights

## Features（特徴）

- Key point extraction（要点の抽出）
- Bullet or paragraph output（箇条書きまたは段落形式の出力）
- Simplifies dense material（密度の高い素材を簡略化）

## Output Format（出力形式）

- Concise paragraph（簡潔な段落）
- Optional bullet points（任意の箇条書き）

## Instructions（指示）

- Identify main points（主要ポイントを特定する）
- Remove redundancy（冗長な部分を除去する）
- Produce readable, actionable summary（読みやすく実行可能な要約を作成する）

## Constraints（制約条件）

- No missing critical info（重要な情報を欠落させない）
- No filler（不要な文言を入れない）
```

構造化コピーライティングスキル

```
---
name: structured-copywriting-skill
description: Generates high-impact copy with clear hooks, structured flow, and concise messaging for marketing, articles, and social media content.
（マーケティング、記事、SNSコンテンツ向けに、明確なフック、構造化されたフロー、簡潔なメッセージングで高インパクトなコピーを生成する）
license: Complete terms in LICENSE.txt
---

# Structured Copywriting Skill（構造化コピーライティングスキル）

## Overview（概要）

Produces persuasive, well-structured copy with strong hooks and calls to action.
（強力なフックとCTAを備えた、説得力があり構造化されたコピーを作成する）

**Keywords**: copywriting, marketing, social media, structured content, hooks, engagement

## Features（特徴）

- Strong hooks（強力なフック）
- Sectioned flow（セクション分けされたフロー）
- CTA inclusion（CTAの挿入）
- Concise and readable（簡潔で読みやすい）

## Output Format（出力形式）

- Sections, bullet points, hooks, conclusion（セクション、箇条書き、フック、結論）

## Instructions（指示）

- Craft attention-grabbing opening（注目を引く冒頭を作成する）
- Organize main points clearly（要点を明確に整理する）
- Include actionable CTA（実行可能なCTAを含める）
- Avoid unnecessary filler（不要な埋め草を避ける）

## Constraints（制約条件）

- Maintain readability（読みやすさを維持する）
- Do not overcomplicate（複雑にしすぎない）
```

ビジュアル＆インフォグラフィック スキル

Excalidraw図解ジェネレーター

```
---
name: excalidraw-diagram-generator
description: Converts textual concepts or workflows into clear diagram instructions suitable for Excalidraw or other visual tools.
（テキストの概念やワークフローを、Excalidrawやその他の視覚ツールに適した明確な図解指示に変換する）
license: Complete terms in LICENSE.txt
---

# Excalidraw Diagram Generator（Excalidraw図解ジェネレーター）

## Overview（概要）

Transforms ideas into diagram structures for visualization, learning, and planning.
（アイデアを視覚化、学習、計画のための図解構造に変換する）

**Keywords**: diagrams, visualization, excalidraw, workflows, mapping

## Features（特徴）

- Node and connector generation（ノードとコネクタの生成）
- Logical hierarchy（論理的な階層構造）
- Clear labels（明確なラベル）

## Output Format（出力形式）

- Diagram title（図のタイトル）
- Nodes and connections（ノードと接続関係）
- Layout suggestion（レイアウトの提案）

## Instructions（指示）

- Identify main elements（主要な要素を特定する）
- Create nodes（ノードを作成する）
- Connect logically（論理的に接続する）
- Suggest layout（レイアウトを提案する）

## Constraints（制約条件）

- Avoid clutter（ごちゃごちゃさせない）
- Maintain clarity（明瞭さを維持する）
```

インフォグラフィックビルダー

```
---
name: infographic-builder
description: Turns textual content into structured infographic formats suitable for reports, presentations, and educational materials.
（テキストコンテンツを、レポート、プレゼンテーション、教育資料に適した構造化されたインフォグラフィック形式に変換する）
license: Complete terms in LICENSE.txt
---

# Infographic Builder（インフォグラフィックビルダー）

## Overview（概要）

Generates visual-friendly summaries from text, highlighting steps, processes, or data points.
（テキストからステップ、プロセス、データポイントを強調した視覚的な要約を生成する）

**Keywords**: infographic, visual, summary, chart, design

## Features（特徴）

- Sectioned breakdown（セクション分けされた分解）
- Bullet or step representation（箇条書きまたはステップ表現）
- Readable visual format（読みやすい視覚フォーマット）

## Output Format（出力形式）

- Steps, headings, visual cues（ステップ、見出し、視覚的手がかり）
- Optional icons or markers（任意のアイコンやマーカー）

## Instructions（指示）

- Extract key points（要点を抽出する）
- Organize visually（視覚的に整理する）
- Apply concise formatting（簡潔なフォーマットを適用する）

## Constraints（制約条件）

- Avoid excessive text（テキストの入れすぎを避ける）
- Maintain clarity（明瞭さを維持する）
```

フローチャート意思決定ビルダー

```
---
name: flowchart-decision-builder
description: Generates decision trees and flowcharts from textual input to simplify complex decision-making processes.
（テキスト入力から意思決定ツリーとフローチャートを生成し、複雑な意思決定プロセスを簡素化する）
license: Complete terms in LICENSE.txt
---

# Flowchart Decision Builder（フローチャート意思決定ビルダー）

## Overview（概要）

Converts processes into stepwise flowcharts for clear decision-making.
（プロセスをステップ形式のフローチャートに変換し、明確な意思決定を支援する）

**Keywords**: flowchart, decision tree, process, visualization, clarity

## Features（特徴）

- Node-based structure（ノードベースの構造）
- Conditional branching（条件分岐）
- Clear labeling（明確なラベリング）

## Output Format（出力形式）

- Nodes（ノード）
- Connections（接続関係）
- Layout guidance（レイアウトガイダンス）

## Instructions（指示）

- Identify steps and decisions（ステップと判断ポイントを特定する）
- Map conditional paths（条件分岐のパスをマッピングする）
- Maintain logical flow（論理的な流れを維持する）

## Constraints（制約条件）

- Keep diagrams simple（図をシンプルに保つ）
- Avoid unnecessary nodes（不要なノードを避ける）
```

UI/UXレイアウトアドバイザー

```
---
name: ui-ux-layout-advisor
description: Advises on interface layouts to optimize clarity, spacing, hierarchy, and usability.
（インターフェースレイアウトの明瞭さ、余白、階層構造、ユーザビリティを最適化するアドバイスを提供する）
license: Complete terms in LICENSE.txt
---

# UI/UX Layout Advisor（UI/UXレイアウトアドバイザー）

## Overview（概要）

Provides structured suggestions for designing clean and usable interfaces.
（クリーンで使いやすいインターフェース設計のための構造的な提案を行う）

**Keywords**: ui, ux, layout, design, hierarchy, clarity

## Features（特徴）

- Spacing and alignment suggestions（余白と配置の提案）
- Hierarchy optimization（階層構造の最適化）
- Accessibility considerations（アクセシビリティへの配慮）

## Output Format（出力形式）

- Layout instructions（レイアウトの指示）
- Element positioning（要素の配置）
- Optional visual hints（任意の視覚的ヒント）

## Instructions（指示）

- Analyze input design（入力されたデザインを分析する）
- Suggest optimal layout（最適なレイアウトを提案する）
- Maintain readability and hierarchy（読みやすさと階層構造を維持する）

## Constraints（制約条件）

- Do not overcrowd layout（レイアウトを詰め込みすぎない）
- Prioritize clarity（明瞭さを優先する）
```

リサーチ＆分析 スキル

ディープリサーチシンセサイザー

```
---
name: deep-research-synthesizer
description: Synthesizes insights from large datasets, filters irrelevant data, identifies patterns, and produces actionable summaries.
（大規模データセットからインサイトを統合し、無関係なデータをフィルタリングし、パターンを特定し、実行可能な要約を作成する）
license: Complete terms in LICENSE.txt
---

# Deep Research Synthesizer（ディープリサーチシンセサイザー）

## Overview（概要）

Converts large amounts of text into structured insights and actionable takeaways.
（大量のテキストを構造化されたインサイトと実行可能な要点に変換する）

**Keywords**: research, synthesis, insights, analysis, knowledge

## Features（特徴）

- Filters low-value info（価値の低い情報をフィルタリング）
- Highlights patterns（パターンを強調表示）
- Creates structured output（構造化された出力を作成）

## Output Format（出力形式）

- Key insights（主要なインサイト）
- Supporting details（裏付けとなる詳細）
- Summary paragraph（要約の段落）

## Instructions（指示）

- Identify key points（要点を特定する）
- Remove irrelevant content（無関係なコンテンツを除去する）
- Organize logically（論理的に整理する）

## Constraints（制約条件）

- Avoid generic summaries（一般的すぎる要約を避ける）
- Focus on utility（実用性に焦点を当てる）
```

オンチェーン取引アナライザー

```
---
name: onchain-transaction-analyzer
description: Analyzes blockchain transactions by tracing wallets, contracts, and token movements and providing simple, understandable explanations.
（ウォレット、コントラクト、トークンの動きを追跡し、シンプルでわかりやすい説明を提供することで、ブロックチェーン取引を分析する）
license: Complete terms in LICENSE.txt
---

# Onchain Transaction Analyzer（オンチェーン取引アナライザー）

## Overview（概要）

Decodes onchain data into human-readable explanations.
（オンチェーンデータを人間が読める説明に変換する）

**Keywords**: blockchain, crypto, analysis, transactions, wallets

## Features（特徴）

- Wallet tracking（ウォレットの追跡）
- Contract mapping（コントラクトのマッピング）
- Token flow visualization（トークンフローの可視化）
- Simple language（平易な言葉遣い）

## Output Format（出力形式）

- Step-by-step explanation（ステップごとの説明）
- Key actors and actions（主要なアクターとアクション）
- Summary insights（まとめのインサイト）

## Instructions（指示）

- Trace wallet and token flows（ウォレットとトークンの流れを追跡する）
- Identify key interactions（主要なインタラクションを特定する）
- Summarize in plain language（平易な言葉で要約する）

## Constraints（制約条件）

- Avoid jargon（専門用語を避ける）
- Focus on clarity（明瞭さに焦点を当てる）
```

ソース検証スキル

```
---
name: source-validation-skill
description: Validates the credibility of information sources, highlighting reliability, relevance, and potential biases.
（情報源の信頼性を検証し、信頼度、関連性、潜在的なバイアスを強調する）
license: Complete terms in LICENSE.txt
---

# Source Validation Skill（ソース検証スキル）

## Overview（概要）

Filters information for trustworthiness and relevance.
（情報の信頼性と関連性をフィルタリングする）

**Keywords**: credibility, validation, sources, research, bias

## Features（特徴）

- Reliability scoring（信頼性スコアリング）
- Bias detection（バイアスの検出）
- Relevance filtering（関連性のフィルタリング）

## Output Format（出力形式）

- Verified sources（検証済みソース）
- Key insights（主要なインサイト）
- Notes on reliability（信頼性に関する注記）

## Instructions（指示）

- Check references（参考文献をチェックする）
- Evaluate author and date（著者と日付を評価する）
- Highlight trustworthy content（信頼できるコンテンツを強調する）

## Constraints（制約条件）

- Avoid unverified info（未検証の情報を避ける）
- Prioritize high-quality sources（質の高いソースを優先する）
```

競合インテリジェンススキル

```
---
name: competitive-intelligence-skill
description: Compares products, protocols, or tools to provide structured analysis of strengths, weaknesses, and opportunities.
（製品、プロトコル、またはツールを比較し、強み、弱み、機会の構造化された分析を提供する）
license: Complete terms in LICENSE.txt
---

# Competitive Intelligence Skill（競合インテリジェンススキル）

## Overview（概要）

Delivers comparative insights for business, tech, or market research.
（ビジネス、テクノロジー、市場調査のための比較分析インサイトを提供する）

**Keywords**: analysis, competitive, research, comparison, strategy

## Features（特徴）

- Feature comparison（機能比較）
- SWOT-style analysis（SWOT形式の分析）
- Recommendations（推奨事項）

## Output Format（出力形式）

- Bullet comparison（箇条書きの比較）
- Strengths/weaknesses（強み／弱み）
- Key takeaways（重要なポイント）

## Instructions（指示）

- Identify competitors/tools（競合やツールを特定する）
- Compare features（機能を比較する）
- Highlight differences and risks（違いとリスクを強調する）

## Constraints（制約条件）

- Avoid bias（バイアスを避ける）
- Focus on actionable insights（実行可能なインサイトに焦点を当てる）
```

ナレッジ構造化スキル

```
---
name: knowledge-structuring-skill
description: Organizes unstructured information into clear frameworks, bullet points, or structured notes for easier understanding and application.
（未整理の情報を、より容易な理解と活用のために、明確なフレームワーク、箇条書き、または構造化ノートに整理する）
license: Complete terms in LICENSE.txt
---

# Knowledge Structuring Skill（ナレッジ構造化スキル）

## Overview（概要）

Transforms messy input into structured, usable knowledge.
（散らかった入力を構造化された使える知識に変換する）

**Keywords**: knowledge, structuring, frameworks, organization, notes

## Features（特徴）

- Categorizes ideas（アイデアをカテゴリ分け）
- Creates logical hierarchy（論理的な階層構造を作成）
- Bullet formatting（箇条書きフォーマット）

## Output Format（出力形式）

- Structured framework（構造化されたフレームワーク）
- Key points（要点）
- Optional notes（任意の注記）

## Instructions（指示）

- Identify major topics（主要トピックを特定する）
- Group related ideas（関連するアイデアをグループ化する）
- Present clearly and concisely（明確かつ簡潔に提示する）

## Constraints（制約条件）

- Avoid ambiguity（曖昧さを避ける）
- Maintain readability（読みやすさを維持する）
```

動画制作 スキル

動画スクリプトジェネレーター

```
---
name: video-script-generator
description: Generates video scripts with hooks, structured sections, pacing, and call-to-actions optimized for engagement and retention.
（エンゲージメントとリテンションに最適化されたフック、構造化セクション、ペーシング、CTAを含む動画スクリプトを生成する）
license: Complete terms in LICENSE.txt
---

# Video Script Generator（動画スクリプトジェネレーター）

## Overview（概要）

Produces structured scripts for short and long-form video content.
（短尺・長尺動画コンテンツ向けの構造化されたスクリプトを作成する）

**Keywords**: video, scripts, hooks, engagement, pacing, content

## Features（特徴）

- Strong opening hooks（強力なオープニングフック）
- Sectioned content（セクション分けされた内容）
- Clear calls-to-action（明確なCTA）

## Output Format（出力形式）

- Hook（フック）
- Content sections（コンテンツセクション）
- Closing summary（締めの要約）

## Instructions（指示）

- Start with hook（フックから始める）
- Organize main points（要点を整理する）
- Maintain pacing（ペーシングを維持する）
- Include CTA（CTAを含める）

## Constraints（制約条件）

- Avoid filler（不要な埋め草を避ける）
- Maintain audience attention（視聴者の注意を維持する）
```

動画編集プランナー

```
---
name: video-editing-planner
description: Suggests editing structure, scene cuts, transitions, and pacing for improved video content quality and engagement.
（動画コンテンツの品質とエンゲージメントを向上させるための編集構造、シーンカット、トランジション、ペーシングを提案する）
license: Complete terms in LICENSE.txt
---

# Video Editing Planner（動画編集プランナー）

## Overview（概要）

Assists in planning efficient, engaging edits.
（効率的で魅力的な編集の計画を支援する）

**Keywords**: video, editing, pacing, transitions, scenes

## Features（特徴）

- Scene breakdown（シーンの分解）
- Transition suggestions（トランジションの提案）
- Pacing optimization（ペーシングの最適化）

## Output Format（出力形式）

- Editing steps（編集ステップ）
- Scene notes（シーンのメモ）
- Transition plan（トランジション計画）

## Instructions（指示）

- Identify key scenes（主要シーンを特定する）
- Suggest cuts/transitions（カット／トランジションを提案する）
- Optimize for engagement（エンゲージメント向上のために最適化する）

## Constraints（制約条件）

- Avoid excessive edits（過剰な編集を避ける）
- Preserve story clarity（ストーリーの明瞭さを保つ）
```

フックジェネレーター

```
---
name: hook-generator
description: Produces attention-grabbing hooks for videos, social posts, and content intros to maximize engagement.
（エンゲージメントを最大化するために、動画、SNS投稿、コンテンツのイントロ向けの注目を集めるフックを生成する）
license: Complete terms in LICENSE.txt
---

# Hook Generator（フックジェネレーター）

## Overview（概要）

Creates compelling openings to capture attention immediately.
（即座に注目を集める魅力的な冒頭を作成する）

**Keywords**: hook, attention, engagement, intro, viral

## Features（特徴）

- Short, impactful（短くインパクトがある）
- Curiosity-driven（好奇心を刺激する）
- Adaptable to content type（コンテンツタイプに適応可能）

## Output Format（出力形式）

- Hook sentence（フック文）
- Optional follow-up intro（任意のフォローアップイントロ）

## Instructions（指示）

- Focus on curiosity or bold statements（好奇心や大胆な主張に焦点を当てる）
- Keep concise（簡潔に保つ）
- Match audience interest（オーディエンスの関心に合わせる）

## Constraints（制約条件）

- Avoid generic hooks（汎用的すぎるフックを避ける）
- Maintain relevance（関連性を維持する）
```

字幕＆キャプションフォーマッター

```
---
name: caption-subtitle-formatter
description: Formats captions and subtitles for readability, timing, and accessibility across videos.
（動画全般にわたって、字幕とキャプションの読みやすさ、タイミング、アクセシビリティを最適にフォーマットする）
license: Complete terms in LICENSE.txt
---

# Caption & Subtitle Formatter（字幕＆キャプションフォーマッター）

## Overview（概要）

Ensures captions are readable, timed correctly, and maintain visual clarity.
（字幕が読みやすく、正確なタイミングで、視覚的に明瞭であることを保証する）

**Keywords**: caption, subtitle, accessibility, readability, video

## Features（特徴）

- Line breaks for clarity（明瞭さのための改行）
- Timing alignment（タイミングの調整）
- Readability optimization（読みやすさの最適化）

## Output Format（出力形式）

- Caption text blocks（キャプションテキストブロック）
- Timing cues（タイミングの手がかり）

## Instructions（指示）

- Format each line for clarity（各行を明瞭に整形する）
- Match timing to speech（発話に合わせてタイミングを調整する）
- Maintain readability standards（読みやすさの基準を維持する）

## Constraints（制約条件）

- Avoid long lines（長すぎる行を避ける）
- Keep clear and concise（明確かつ簡潔に保つ）
```

コーディング＆自動化 スキル

コードレビュースキル

```
---
name: code-review-skill
description: Reviews code for bugs, inefficiencies, and adherence to best practices, providing actionable improvement suggestions.
（コードのバグ、非効率性、ベストプラクティスへの準拠をレビューし、実行可能な改善提案を提供する）
license: Complete terms in LICENSE.txt
---

# Code Review Skill（コードレビュースキル）

## Overview（概要）

Analyzes code to ensure quality, efficiency, and maintainability.
（コードの品質、効率、保守性を分析する）

**Keywords**: code, review, bugs, optimization, best practices

## Features（特徴）

- Error detection（エラーの検出）
- Optimization recommendations（最適化の推奨）
- Style enforcement（スタイルの統一）

## Output Format（出力形式）

- Issues found（発見された問題）
- Suggested fixes（修正の提案）
- Optional summary（任意の要約）

## Instructions（指示）

- Analyze code line by line（コードを1行ずつ分析する）
- Highlight errors or inefficiencies（エラーや非効率な箇所を強調する）
- Suggest improvements（改善を提案する）

## Constraints（制約条件）

- Maintain accuracy（正確さを維持する）
- Avoid false positives（誤検出を避ける）
```

ワークフロー自動化エージェント

```
---
name: workflow-automation-agent
description: Breaks complex tasks into step-by-step workflows, mapping actions to tools, optimizing execution, and improving efficiency.
（複雑なタスクをステップバイステップのワークフローに分解し、アクションをツールにマッピングし、実行を最適化し、効率を改善する）
license: Complete terms in LICENSE.txt
---

# Workflow Automation Agent（ワークフロー自動化エージェント）

## Overview（概要）

Converts goals into actionable workflows for AI-assisted or human execution.
（目標をAI支援または人間が実行可能なワークフローに変換する）

**Keywords**: automation, workflow, productivity, steps, execution

## Features（特徴）

- Task decomposition（タスクの分解）
- Tool mapping（ツールへのマッピング）
- Optimization（最適化）

## Output Format（出力形式）

- Goal（目標）
- Stepwise actions（ステップごとのアクション）
- Tools & instructions（ツールと指示）

## Instructions（指示）

- Identify goal（目標を特定する）
- Break into steps（ステップに分解する）
- Assign tools（ツールを割り当てる）
- Optimize for efficiency（効率を最適化する）

## Constraints（制約条件）

- Avoid vague instructions（曖昧な指示を避ける）
- Maintain logical flow（論理的な流れを維持する）
```

スキルクリエイター（メタスキル）

```
---
name: skill-creator-meta-skill
description: Generates new AI skills in `.md` format, providing structured name, description, and instruction for future use.
（将来の使用に向けて、構造化されたname、description、instructionを備えた新しいAIスキルを `.md` 形式で生成する）
license: Complete terms in LICENSE.txt
---

# Skill Creator / Meta Skill（スキルクリエイター／メタスキル）

## Overview（概要）

Automates creation of AI skills by generating fully structured `.md` files.
（完全に構造化された `.md` ファイルを生成してAIスキルの作成を自動化する）

**Keywords**: skill creation, automation, AI, md, modular

## Features（特徴）

- Generates skill metadata（スキルのメタデータを生成）
- Includes detailed instructions（詳細な指示を含む）
- Ready-to-use format（すぐに使えるフォーマット）

## Output Format（出力形式）

- Skill name（スキル名）
- Description（説明）
- Instruction steps（指示ステップ）

## Instructions（指示）

- Accept input goal（入力された目標を受け取る）
- Define role, task, process（役割、タスク、プロセスを定義する）
- Output structured `.md` skill（構造化された `.md` スキルを出力する）

## Constraints（制約条件）

- Maintain clarity（明瞭さを維持する）
- Ensure usability（使いやすさを確保する）
```

DevOpsアシスタント

```
---
name: devops-assistant
description: Assists in version control, deployment, and automation tasks, ensuring smooth DevOps operations and workflow efficiency.
（バージョン管理、デプロイメント、自動化タスクを支援し、スムーズなDevOps運用とワークフローの効率を確保する）
license: Complete terms in LICENSE.txt
---

# DevOps Assistant（DevOpsアシスタント）

## Overview（概要）

Supports development workflows by managing versioning, deployment, and automation tasks.
（バージョニング、デプロイメント、自動化タスクを管理して開発ワークフローを支援する）

**Keywords**: devops, automation, deployment, git, workflow

## Features（特徴）

- Commit and version guidance（コミットとバージョン管理のガイダンス）
- Deployment suggestions（デプロイメントの提案）
- Workflow optimization（ワークフローの最適化）

## Output Format（出力形式）

- Task instructions（タスクの指示）
- Stepwise guide（ステップごとのガイド）
- Automation recommendations（自動化の推奨）

## Instructions（指示）

- Analyze project requirements（プロジェクト要件を分析する）
- Suggest DevOps actions（DevOpsアクションを提案する）
- Optimize workflow efficiency（ワークフローの効率を最適化する）

## Constraints（制約条件）

- Ensure accuracy（正確さを確保する）
- Avoid redundant steps（冗長なステップを避ける）
```

最後に

株式会社Levelaでは、一緒に働く仲間を募集しています。

Levelaは「with AI」を掲げ、全スタッフがAIありきでタスクを進行し、当たり前に開発を行える会社にしてます。

2026年、AIを使いこなせるかどうかで今後のキャリアプランが変わることは間違いありません。

「AIを当たり前に使いこなせる人材になりたい！」という方は是非、下記のLINEからお問い合わせください。

https://liff.line.me/2007583006-A5YJgw0X/landing?follow=%40319mlqoq&lp=jflzEw&liff_id=2007583006-A5YJgw0X
