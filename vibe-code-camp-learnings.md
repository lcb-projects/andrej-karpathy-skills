# Vibe Code Camp Learnings

Extracted from the [Every Inc. Vibe Code Camp](https://github.com/EveryInc/vibe-code-camp) 8-hour livestream transcript featuring top vibe coders demonstrating how they build software with AI.

---

## Planning & Prompting

- **Plan before you code.** Everyone forgot to plan when AI coding started. "We just one-shot everything. And we complain." Bring back the planning discipline. (Kieran Klaassen)
- **A senior-quality plan elicits senior-quality code.** If your plan reads like a senior engineer wrote it, the model responds at that level. Mediocre plans produce mediocre code. (Kevin Rose / Kieran)
- **Write detailed PRDs with atomic user stories and clear acceptance criteria.** Acceptance criteria must be things an agent can verify autonomously (e.g., browser testing), not things requiring manual human checks. (Ryan Carson)
- **Use voice-to-text for prompting.** Speaking produces better, more detailed prompts than typing. "When I'm typing, there's some inherent laziness. But if I'm just rambling, I'm way more specific." (CJ Hess)
- **Front-load massive context.** Dictate for 10-20 minutes, distill it, and send it. More upfront tokens = higher first-attempt success rate. (Kevin Rose)
- **Have the AI interview you back on your plan.** After brain-dumping, ask it to interview you on things it doesn't understand. This fills gaps before implementation. (Brandon Gell)
- **Add "in the chat" to prevent premature coding.** Claude is eager to write code. Append "in the chat" to have a side conversation without it touching files. (CJ Hess)

## Workflow Architecture

- **Compound Engineering loop: Plan -> Work -> Review -> Compound -> Repeat.** The "compound" step extracts learnings from mistakes into searchable docs. Most people skip this. (Kieran Klaassen)
- **Three levels of agent memory:** Long-term (model training), medium-term (`agents.md` / skills files), short-term (`progress.txt` for current task gotchas). Promote short-term learnings to medium-term when broadly relevant. (Ryan Carson)
- **Use progress.txt and plan files.** The plan says what needs to happen; progress tracks what's been done. Every agent instance reads both so it knows current state. (Ben Tossell)
- **Set up a cron job that analyzes your product data nightly.** Pull from your database, send to an LLM, get a markdown report identifying the #1 thing to fix. Think of it as a VP of product for 15 cents/day. (Ryan Carson)
- **Build recursive self-reviewing PR workflows.** Claude reviews its own PR, categorizes fixes into "fix now" vs. "create follow-up issue," implements immediate fixes, and on PR merge evaluates follow-ups automatically. (Nat Eliason)
- **Use a Kanban board to manage agent tasks.** Instead of juggling terminal tabs, maintain a board with To Do / Planning / Building / Done columns. Cards turn red when the agent needs human input. (Geoffrey Litt)
- **Prototype in V0, then build properly in Claude Code.** Use V0 for rapid visual prototyping. When it "feels right," hand it to compound engineering to build for real. (Kieran Klaassen)

## Multi-Model Strategy

- **Use different models for different phases.** Opus for creative/complex work and orchestration. Codex for debugging, large codebase edits, and focused implementation. Sonnet/Haiku for lightweight tasks like pattern review or search. (Multiple speakers)
- **Opus as engineering manager, Codex as the coder.** Trust Opus to orchestrate and plan. Offload implementation to Codex. This also preserves Claude credits. (Nat Eliason)
- **Two-pane review: one model builds, another reviews.** Run Opus to implement, then have GPT-5 or Codex review. Pass review feedback back with "Don't just agree -- tell me why you'd change these things." (Kevin Rose)
- **Cross-model debugging works.** "I actually really like when Opus uses Codex to debug something." (Ashe Magalhaes)
- **Retry techniques with each new model.** What didn't work with Sonnet 4.5 may work brilliantly with Opus 4.5. Re-evaluate your scaffolding constantly. (Thariq Shihipar)

## Debugging & Getting Unstuck

- **When stuck in a "fix it" loop: STOP.** Invest time explaining all the things that aren't working in detail. Build shared understanding with the agent. Then say "go do it" and it one-shots it. (Dan Shipper)
- **Bug diagnosis strategy:** (1) List all possible bugs. (2) Go through them one by one. (3) Ask the agent which is most likely. (4) Validate with tests and agent browser. (5) Keep looping. (Ben Tossell)
- **Write tests even if you don't understand them.** "I don't know anything about tests but I say make sure you write tests." (Ben Tossell)
- **Use agent browser for validation.** Direct the agent to use browser tools to navigate your site, log what's happening, and identify issues autonomously. "If you're not using Agent Browser, what are you doing?" (Ryan Carson)
- **When a build fails, point Claude back to the plan.** "Give it the error, tell it when it happened, and say: reference the original plans. Did we follow them correctly?" (CJ Hess)
- **Ask the agent to update agents.md after recurring problems.** "Why did that come up again? Do we need to add something to agents.md so we don't repeat this?" (Ben Tossell)

## Skills, Setup & Agent Configuration

- **Skills = markdown files encoding tribal knowledge.** Write down everything you'd tell a new hire in their first week. Create new skills from questions that new team members ask. (Paula Dozsa)
- **Ask Claude to help write your Claude setup.** "It is actually really good at that. You don't have to handwrite it yourself." (Paula Dozsa)
- **Use hooks as automated guardrails.** Scripts that run before/after Claude uses tools to prevent known bad patterns. When Claude does something wrong repeatedly, add a hook. (Paula Dozsa)
- **Compounding: extract learnings into searchable docs.** Instead of bloating `CLAUDE.md` with rules, save learnings as individual markdown files with frontmatter and keywords. A Haiku-powered search agent finds relevant ones on demand. (Kieran Klaassen)
- **Skills and CLIs often beat MCPs.** "Skills and CLIs are often just as capable and give you way less context bloat." (CJ Hess)
- **Use Context7 MCP server** to keep agent tool libraries up to date with best-in-class frameworks. "Tokens don't lie." (Tina He)

## Agent-Native App Design

- **Parity principle:** Anything the user can do in the app, the agent can also do. This unlocks emergent capabilities you never explicitly coded. (Dan Shipper / Geoffrey Litt)
- **Granularity principle:** Make tools smaller than features so the agent can combine them in new ways you didn't predict. "Like Lego bricks into new and different forms." (Dan Shipper)
- **Features as skills.** Each feature is a "skill" the agent can perform, consisting of prompts and tools that run in a loop until done. (Dan Shipper)
- **CLIs thrived temporarily because they naturally have parity.** They're both a mediocre GUI and a mediocre API -- and that duality is the superpower. (Geoffrey Litt)

## Autonomous & Always-On Agents

- **Buy a Mac Mini ($500) to run agents 24/7.** Message it at 10 PM, wake up to completed features. Use Apple Scripts for iMessage notifications when tasks complete. (Nat Eliason / Kieran Klaassen)
- **Connect Sentry errors to Slack, tag your agent.** It investigates, spins up a sub-agent to code a fix, and opens a PR. If the bug is ambiguous, it asks a question and waits for guidance. (Nat Eliason)
- **Nightly conversation analysis.** At 2 AM, have your agent pull all user conversations, identify frustrations and failures, write a report, and auto-fix bugs it finds. (Nat Eliason)
- **Overnight browser testing.** Agent opens staging, creates an account, goes through the onboarding flow, looks for issues, writes a report, and auto-fixes bugs. (Nat Eliason)
- **Bash scripts are underrated for orchestration.** They avoid context limits, can invoke agents non-interactively, and you can spawn thousands of instances. (Ryan Carson)

## Non-Technical & Creative Builders

- **Non-engineers can ship production code.** Designers with no coding experience at Portola open iOS and backend PRs via Claude. Engineers review before merge, but the PRs are "basically ready to go." (Paula Dozsa)
- **Pain tolerance is your ceiling.** The extent of what you can build is directly proportional to your willingness to push through frustration. "It's always a me problem." (Ben Tossell)
- **Good writers make good vibe coders.** If you can describe something precisely in language, you can prompt effectively. (Tina He)
- **The allocation economy:** You don't need the skills yourself; you need to know what to ask for and which resources to invoke. (Dan Shipper)
- **Claude Desktop app is a massive unlock for non-technical users.** The pull-down menu for folder navigation eliminates the need to memorize terminal commands. (Katie Parrott)
- **Ask Claude to "explain like I'm five."** When technical output is confusing, explicitly ask for simpler explanations. Levels up your understanding over time. (Katie Parrott)

## Reverse Engineering & Learning

- **Reverse engineer macOS apps to learn from billion-dollar teams.** Any macOS app is just a bundle of files. Feed it to Claude Code to get a complete teardown -- frameworks, APIs, third-party services, what they built vs. bought. (Yash Poojary)
- **Saved teardowns become a reusable reference library.** When building a new feature, tell Claude to reference the relevant teardown and "plug and play." (Yash Poojary)
- **Use DeepWiki to evaluate new tools.** Paste any GitHub link; it builds a full deep document. Then generate a NotebookLM podcast from it and listen at 2x. "In seven minutes, I'm like, oh yeah, I got to give this a try." (Kevin Rose)
- **Read every line of AI-generated code.** The "TikTokification of code" (just accepting output) leads to not understanding your own codebase. Being responsible for every line means you can fix issues in two minutes when something breaks. (Yash Poojary)
- **Have Claude write explanatory documents for every code change, starting zoomed out.** Never start with a code diff. Start with "here's what lunar landers are, here's how the physics works." Then narrow to the specific change. (Geoffrey Litt)
- **Quiz yourself on AI-generated PRs before sending them.** "I refuse to send a PR unless I can pass a quiz of understanding what's in the PR." (Geoffrey Litt)

## AI-to-Human Communication

- **Make agent status reports feel like presidential briefing books.** "I want it to feel like a staff spent a day preparing this briefing book for me -- an optimal learning experience." (Geoffrey Litt)
- **Voice is high-bandwidth human-to-AI; visualization is high-bandwidth AI-to-human.** Have Claude make presentations with interactive simulations showing what it did. (Geoffrey Litt)
- **For vibe-coded projects, a Loom walkthrough beats a code diff.** Ask the agent to create a feature walkthrough -- it clicks through things and shows you. (Logan Kilpatrick)
- **Invest in a good place to read plans.** "You should not be reading mono-spaced markdown. Quality of life improvement everyone should invest in." (Geoffrey Litt)

## Data, Research & Non-Coding Uses

- **Drop a CSV into AI Studio and ask for an interactive visualization.** One prompt, full dashboard. Then layer AI features on top. (Logan Kilpatrick)
- **Build interactive research dashboards, not static documents.** One command to create a full earnings preview dashboard with financial data from MCPs, local files, and APIs simultaneously. 5 hours of manual analyst work becomes one automated command. (Brooker Belcourt)
- **Store complex prompts in GitHub for version control.** When prompts exceed chat limits, put them in a repo as Claude plugins. Version control, collaboration, and more robust prompt engineering. (Brooker Belcourt)
- **Inject your domain philosophy via skills.** Encode your analytical framework (investing philosophy, editorial style, design principles) so Claude applies your thinking, not generic consensus. (Brooker Belcourt)

## Meta-Insights

- **Tool calling is the most important model capability for coding agents.** Every user request involves many micro-decisions that are all tool calls. Making tool calling better over long-running tasks is the holy grail. (Logan Kilpatrick)
- **The "delete code" cycle is the hardest part of AI engineering.** A new model comes out that natively handles what your scaffolding did. You must delete that code. Most people get stuck here. (Thariq Shihipar)
- **Slop = in-distribution for the model.** The goal is pushing the edges of what the model can barely do. The slop line is a moving target. (Logan Kilpatrick)
- **Jevons paradox applies to software.** If Claude writes 10x as much code, you can also delete 10x as much. The moat is your direction, not any single feature. (Thariq Shihipar)
- **Building is like making a movie:** research phase, scripting phase, shooting phase, editing phase. Don't worry about perfecting corners during shooting. Polish comes in the edit. (Yash Poojary)
- **Focus on the experience, not feature implementation.** With AI writing code so easily, the real work is user experience. Code generation is the easy part now. (Yash Poojary)

## Key Tools Mentioned

| Tool | Purpose |
|------|---------|
| Claude Code / Opus 4.5 | Primary AI coding agent |
| Codex (OpenAI) | Complementary agent for large codebases, debugging |
| Compound Engineering Plugin | Plan/work/review/compound loop for Claude Code |
| Monologue | Voice-to-text Mac/iOS app |
| Agent Browser (Vercel) | Automated browser testing for agents |
| V0 (Vercel) | Visual prototyping |
| Context7 MCP | Up-to-date library documentation |
| Conductor Build | GUI wrapper around Claude Code with Git worktrees |
| Flowey | JSON-based diagramming tool (flowcharts + UI mockups) |
| AI Studio (Google) | Vibe coding with built-in Gemini API |
| DeepWiki (Devin) | Auto-documentation from any GitHub repo |
| Agent Watch | Menu bar app showing status of running agents |
| Remotion | Programmatic video creation |
| Streamlit | Interactive dashboards from Python |
