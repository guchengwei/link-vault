# 8 Claude Code Hooks That Automate What You Keep Forgetting

- Source: https://x.com/zodchiii/status/2040000216456143002
- Author: @zodchiii
- Created: 2026-04-03T09:35:27Z

8 Claude Code Hooks That Automate What You Keep Forgetting

Have you ever told Claude Code to do something and it just didn't?
You said format the code - It didn't. You said don't touch that file - It did. 
You said run tests before finishing - It forgot.

Have you ever told Claude Code to do something and it just didn't?

You said format the code - It didn't. You said don't touch that file - It did.

You said run tests before finishing - It forgot.

That's because CLAUDE.md is a suggestion.

Claude reads it and follows it about 80% of the time. Hooks are different. They're automatic actions that fire every time Claude edits a file, runs a command, or finishes a task.

Below I will share 8 personal hooks you can copy straight into your settings.json and never think about again 👇

Before we dive in, I share daily notes on AI & vibe coding in my Telegram channel: https://t.me/zodchixquant🧠

![](assets/image-01.jpg)

How hooks work (30-second version) What are hooks?

Hooks are automatic actions that run every time Claude Code does something, like editing a file or running a command.

You set them up once and they work in the background without you thinking about it.

The two you'll use most:

PreToolUse runs before Claude does something. You can inspect the action and block it by returning exit code 2. Think of it as a bouncer.

PostToolUse runs after Claude does something. You can run cleanup, formatting, tests, or logging. Think of it as quality control on the assembly line.

```markdown
Where hooks live:

.claude/settings.json         project-level (shared via git)
~/.claude/settings.json       user-level (all your projects)
.claude/settings.local.json   local only (not committed)
```

You configure them in .claude/settings.json in your project root. That file gets committed to git, so your whole team gets the same hooks automatically.

Full documentation: https://code.claude.com/docs/en/hooks

![](assets/image-02.jpg)

1. Auto-format every file Claude touches

The problem: Claude writes correct code that breaks your formatting rules. You add "always run Prettier" to CLAUDE.md and it works most of the time, but not always.

The hook: Prettier runs automatically after every file write or edit.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write 2>/dev/null; exit 0"
          }
        ]
      }
    ]
  }
}

```

Swap npx prettier --write for whatever formatter you use: black for Python, gofmt for Go, rustfmt for Rust. The pattern is the same.

This was the first hook I set up and honestly it should be the default for every project. No more "Claude forgot to format" commits.

2. Block dangerous commands

The problem: Claude is powerful enough to run rm -rf, git reset --hard, DROP TABLE, or curl to random URLs. It probably won't, but "probably" isn't good enough when it's your production database.

The hook: Block destructive commands before they execute.

Create .claude/hooks/block-dangerous.sh:

```bash
Create .claude/hooks/block-dangerous.sh:
#!/usr/bin/env bash
set -euo pipefail
cmd=$(jq -r '.tool_input.command // ""')

dangerous_patterns=(
  "rm -rf"
  "git reset --hard"
  "git push.*--force"
  "DROP TABLE"
  "DROP DATABASE"
  "curl.*|.*sh"
  "wget.*|.*bash"
)

for pattern in "${dangerous_patterns[@]}"; do
  if echo "$cmd" | grep -qiE "$pattern"; then
    echo "Blocked: '$cmd' matches dangerous pattern '$pattern'. Propose a safer alternative." >&2
    exit 2
  fi
done
exit 0
Then add to your settings.json:
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/block-dangerous.sh"
          }
        ]
      }
    ]
  }
}
```

Then add to your settings.json:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/block-dangerous.sh"
          }
        ]
      }
    ]
  }
}

```

Exit code 2 is the key. It blocks the action and sends your error message back to Claude so it can try a safer approach. Exit code 0 means "go ahead." Anything else logs a warning but doesn't block.

3. Protect sensitive files from edits

The problem: Claude can read and edit any file in your project. That includes .env, package-lock.json, config files, and anything else you'd rather it didn't touch.

The hook: Block edits to files that should be off-limits.

Create .claude/hooks/protect-files.sh:

```bash
#!/usr/bin/env bash
set -euo pipefail
file=$(jq -r '.tool_input.file_path // .tool_input.path // ""')

protected=(
  ".env*"
  ".git/*"
  "package-lock.json"
  "yarn.lock"
  "*.pem"
  "*.key"
  "secrets/*"
)

for pattern in "${protected[@]}"; do
  if echo "$file" | grep -qiE "^${pattern//\*/.*}$"; then
    echo "Blocked: '$file' is protected. Explain why this edit is necessary." >&2
    exit 2
  fi
done
exit 0
```

```bash
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/protect-files.sh"
          }
        ]
      }
    ]
  }
}
```

4. Run tests after every edit

The problem: Claude makes a change, says "done," and you discover the tests are broken 20 minutes later when you try to commit.

The hook: Run your test suite automatically after every code change. If tests fail, Claude sees the failure and can fix it immediately.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npm run test --silent 2>&1 | tail -5; exit 0"
          }
        ]
      }
    ]
  }
}
```

The tail -5 keeps the output short so it doesn't flood Claude's context. You want Claude to see "3 tests failed" not the full 200-line test output.

Boris Cherny, the creator of Claude Code, says giving Claude a feedback loop like this improves output quality by 2-3x. Instead of writing code and hoping it works, Claude writes code, sees the test results, and fixes failures on its own.

5. Require passing tests before creating a PR

The problem: Claude finishes a feature and immediately creates a PR. Tests are failing. Your reviewer sees red CI and sends it back.

The hook: Block PR creation unless all tests pass.

Create .claude/hooks/require-tests-for-pr.sh:

```
#!/usr/bin/env bash
set -euo pipefail

if npm run test --silent; then
  exit 0
else
  echo "Tests are failing. Fix all test failures before creating a PR." >&2
  exit 2
fi

```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__github__create_pull_request",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/require-tests-for-pr.sh"
          }
        ]
      }
    ]
  }
}
```

This is a hard gate. No green tests, no PR. Claude will fix the failures first because exit code 2 tells it the action was blocked and why.

6. Auto-lint and report errors

The problem: Claude writes code that works but violates your ESLint rules, style guide, or type checks. You catch it during review and send it back.

The hook: Lint after every edit. If lint fails, Claude sees the errors and fixes them before you ever look at the code.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npx eslint --fix $(jq -r '.tool_input.file_path') 2>&1 | tail -10; exit 0"
          }
        ]
      }
    ]
  }
}
```

You can chain this with the auto-format hook from #1. Prettier runs first, then ESLint. By the time you see the code, it's formatted and lint-clean.

7. Log every command Claude runs

The problem: Claude runs a lot of shell commands during a session. If something goes wrong, you want to know exactly what it did and when.

The hook: Append every Bash command to a log file with timestamps.

Create .claude/hooks/log-commands.sh:

```bash
#!/usr/bin/env bash
set -euo pipefail
cmd=$(jq -r '.tool_input.command // ""')
printf '%s %s\n' "$(date -Is)" "$cmd" >> .claude/command-log.txt
exit 0
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/log-commands.sh"
          }
        ]
      }
    ]
  }
}
```

Now you have a timestamped audit trail of every command Claude ran. Add .claude/command-log.txt to your .gitignore so it doesn't pollute your repo.

This is especially useful for debugging: if Claude broke something three sessions ago, you can look at the log and find exactly when and what it ran.

8. Auto-commit after each completed task

The problem: Claude finishes a task and you forget to commit. Then it starts another task and now you have two unrelated changes mixed together in one commit.

The hook: Automatically commit all changes when Claude stops working on a task.

Create .claude/hooks/auto-commit.sh:

```bash
#!/usr/bin/env bash
set -euo pipefail
git add -A
if ! git diff --cached --quiet; then
  git commit -m "chore(ai): apply Claude edit"
fi
exit 0
```

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/auto-commit.sh"
          }
        ]
      }
    ]
  }
}
```

Every time Claude finishes a response, changes get committed automatically. Your git history stays clean with atomic commits per task instead of one massive "Claude changes" blob at the end of the day.

Combine this with claude -w feature-branch (worktrees) and you get isolated, auto-committed feature branches for every task.

The complete settings.json

Here's everything combined into one file you can copy-paste:

Screenshot-friendly:

![](assets/image-03.jpg)

Copy this file into .claude/settings.json, create the hook scripts in .claude/hooks/, make them executable with chmod +x .claude/hooks/*.sh, and commit everything to git. Your whole team gets the same safety nets automatically.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": ".claude/hooks/block-dangerous.sh" },
          { "type": "command", "command": ".claude/hooks/log-commands.sh" }
        ]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": ".claude/hooks/protect-files.sh" }
        ]
      },
      {
        "matcher": "mcp__github__create_pull_request",
        "hooks": [
          { "type": "command", "command": ".claude/hooks/require-tests-for-pr.sh" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write 2>/dev/null; exit 0" },
          { "type": "command", "command": "npx eslint --fix $(jq -r '.tool_input.file_path') 2>&1 | tail -10; exit 0" }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": ".claude/hooks/auto-commit.sh" }
        ]
      }
    ]
  }
}

```

The difference between a good Claude Code setup and a great one isn't the model or the prompts. It's the hooks.

They're the part that runs when you're not paying attention, catching the mistakes you'd otherwise find during code review or worse, in production.

Set up hook #1 (auto-format) and #2 (block dangerous commands) today. That alone will save you from the most common Claude Code mistakes. Add the rest as you need them.

I share daily notes on AI, finance, and vibe coding in my Telegram channel: https://t.me/zodchixquant

Thanks for reading 🙏🏼

![](assets/image-04.jpg)
