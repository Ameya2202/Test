# AI Agent Memory Systems: Working, Procedural, Semantic & Episodic Memory

## Metadata

| Field | Value |
|---|---|
| Source | https://youtu.be/mY3bR9qjZr4 |
| Approx. Duration | ~12 min |
| Language | English |
| Speakers | 1 / Shawn (Sean’s AI Stories) |
| Input Tokens used | ~48,117 (estimated) |
| Output Tokens used | ~3,196 (estimated) |
| Execution Time | 06:47 |

## Overview

This talk walks through the system design of a modern AI agent memory stack: working memory (context/RAM), procedural memory (skills and behavior), semantic memory (durable facts via RAG and vector stores), and episodic memory (dated events and chat history). Shawn explains how ChatGPT- and Claude-style products consolidate episodic activity into compact semantic facts behind a consolidation gate, and why that pattern improves token efficiency and retrieval quality.

## Table of Contents

- [Why Agent Memory Matters](#why-agent-memory-matters)
- [User Prompts and the Basic Q&A Flow](#user-prompts-and-the-basic-qa-flow)
- [Working Memory (Context RAM)](#working-memory-context-ram)
- [Chat History and System Prompts](#chat-history-and-system-prompts)
- [Ephemeral AI Agent Sessions](#ephemeral-ai-agent-sessions)
- [Three Pillars Beyond Working Memory](#three-pillars-beyond-working-memory)
- [Procedural Memory and Skills](#procedural-memory-and-skills)
- [Semantic Memory, Durable Facts, and RAG](#semantic-memory-durable-facts-and-rag)
- [Vector Stores and Top-K Search](#vector-stores-and-top-k-search)
- [Episodic Memory](#episodic-memory)
- [Consolidation Gate and Summarizer Agent](#consolidation-gate-and-summarizer-agent)
- [Putting the Full Memory System Together](#putting-the-full-memory-system-together)
- [Key Takeaways](#key-takeaways)

## Why Agent Memory Matters

Hey everyone, this is Shawn. Today I want to explain what an AI agent memory system looks like, and why it is important to understand how memory works these days.

If you have been using tools like ChatGPT or Claude, or code tools, you are probably already using a memory system without realizing it. For example, when you ask your AI tool about who you are and about questions you asked over the past week, they know what is going on. If you are an AI builder or startup founder, sometimes they even remember what your company is without you needing to explain it.

In this video I want to explain the essential parts of how this works. I am going to walk you through the system design on the screen step by step, so you understand what matters in this kind of design, and what helps with efficient token usage in a memory system for AI agents. Let’s get started.

## User Prompts and the Basic Q&A Flow

When we talk to ChatGPT or Claude or anything similar, the first thing you do is ask a question. In our language that is called a user prompt. A prompt is basically something you send to a chatbot — for example, “Hey, what’s the weather like today? How do I build an app? How do I understand Einstein’s theory?”

We might think we are asking the question directly to that pink bubble, which is an LLM — a Q&A agent that lets you ask questions and get answers, and then you get a reply. Between the question and the reply, more steps are happening.

## Working Memory (Context RAM)

The question first flows into something called working memory, or context RAM. That means that instead of asking a simple question such as “What does my company do?” — in which case the large language model might not remember or might not even know — it needs working memory that includes information from the internet, from the current context itself, or from databases where you previously stored that information.

## Chat History and System Prompts

Working memory also needs to be fed with the current chat history and a system prompt.

Chat history is basically everything you have talked about in a conversation with AI. That is easy to understand.

A system prompt is basically a role-play. For example, if you want AI to respond like Elon Musk, you put in the system prompt: “Hey, you’re Elon Musk. You must talk to me like Elon Musk.”

The user question (the user prompt), the current chat history, and the system prompt are the basic components fed into working memory — the current context — so your Q&A agent can understand: “Okay, here’s the entire context. I’m going to process this information before I send this user a reply.”

## Ephemeral AI Agent Sessions

But what if we need more than just the current chat history? What if we need something else?

Let’s say you are setting up an agent so customers can talk to you and ask questions about your products or about a deal you are discussing. A customer might ask about product quality, about previous conversations, or ask a follow-up question. The current chat history is all the history that happened in that e-commerce app. The system prompt is probably something like: “Oh, you are a bot that will take care of all of my customers on this e-commerce site.”

The conversation happening here is called an AI agent session. This session is ephemeral, which means nothing here will get saved unless you manually save it in a database — because there is no database here yet. We are literally just making an LLM call.

You could argue that the current chat history has a bit of memory, but that only exists in the current conversation. This current session does not know anything about your product stocks, previous purchase history, your customers’ taste, anything you have argued about, or any complaints in the past.

That is why we need to build on top of working memory, give it richer information, and make it efficient as well.

## Three Pillars Beyond Working Memory

There are three main pillars that make working memory more complete:

1. Procedural memory
2. Semantic memory
3. Episodic memory

I will explain them one by one.

## Procedural Memory and Skills

Procedural memory is basically how the agent should behave. It is usually related to how the agent should act. If you are familiar with the idea, you can write skills to teach an agent to do repeated tasks.

For example, it could be something like: if you realize the customer is really angry, you should answer them politely and always apologize. That is a skill your agent should learn. There is not really “memory” about that thing in the episodic sense — you can think of it as a habit you want to teach an employee or your kids: this is how you react when such a situation happens. It is just a procedure.

These are usually saved in files or text. For skills, you can save them as a markdown file. I am going to connect this to the working memory, and this is usually inputted as a `skill.md` markdown file.

## Semantic Memory, Durable Facts, and RAG

Semantic memory and episodic memory are slightly different. They are not saved in files; we would call the stores vector stores. These vector stores feed information into memory that gets plugged into working memory.

For semantic memory, it is basically saving things like durable facts or a user profile.

Let’s say I start a new store online today, and if I just ask ChatGPT what my products are, ChatGPT will have no idea who you are. Well, if they do have some idea of who you are — say if you’re Walmart — then that means you’re already famous. Their models have already trained on you, or they can search the internet to find out about you.

But in your case, because the foundational large language model does not know who you are, you need to save some durable facts — or the profile of your company or about yourself — in a database so that when one of your customers asks a question about a certain product, your agent will be able to understand where to fetch that information.

This is a process we call RAG, which is retrieval augmented generation. Normally it uses a top-K search method. I have a dedicated video about retrieval augmented generation on my channel — feel free to watch it.

Basically, RAG allows the AI agent to have access to information and also to select and fetch the most relevant information related to your questions.

Why is selectively fetching so important? If you run a company for 10 years, your database could be really huge. You could have a gigantic amount of images or text or documentation about a company. You do not want to feed the whole thing into the LLM, because firstly that would be very expensive, and secondly that is probably not feasible.

These days, I think the context window for most LLMs is roughly 1 million tokens. If you go beyond that, good luck — but you do not want to overload your LLMs, because that also makes things much slower and less accurate. So you want something to smartly fetch information for you, and that method is called RAG. You can watch my previous video to understand RAG a bit better.

Here, RAG is basically helping you fetch the static and durable facts about your company: what products you’re selling, who you are, what kind of branding you have, what kind of ways you put yourself out there in front of customers. These things do not normally change.

Or the facts could be about who this customer is — if they message you very often, you want to remember who they are. Otherwise it sounds like you do not really care about your customers. I will explain how we make semantic memory also remember the customer side in a bit.

## Vector Stores and Top-K Search

Episodic memory is also stored in a vector store. Again, a vector store is an embedded list of arrays or numbers that represent all the text. Remember: computers cannot process text or documents; they can only process numbers. How AI understands our world is by turning every single word into a list of numbers, and then doing similarity search — which is basically RAG.

RAG, again, is doing top-K search. If K is five, then it is looking for the top five most relevant pieces of information from the vector store to feed into answering the user’s question.

## Episodic Memory

The main difference between episodic memory and semantic memory is that episodic memory records the dated events or activities that happened. It is like a timeline where everything that happened has a time on it — or it is just past chat history.

Remember: in this box, the AI agent session, everything is going to be gone after the conversation is gone. So we are going to save this conversation — the current chat history — into the episodic memory later, so it has the entire record of previous conversations related to this agent’s activities with their users.

For selling items online, examples could be storing who is purchasing what items on what day, when the item was delivered, and when the last time somebody filed a complaint for your service.

We need to add an arrow here to link the reply to this database. This is basically saving the messages — or actually activities as well — so that episodic memory is constantly being updated. It is basically a log of all previous history.

## Consolidation Gate and Summarizer Agent

Here is the fun part. If you have been using ChatGPT or Claude and you use their memories, you will realize that sometimes you can edit the memories yourself. You realize the memories are not very long, but they are constantly being updated. For example, it remembers that I am building a company working on a certain type of problem. I do not need to explain anything — but sometimes we do a small pivot and talk about it in our conversations, and then the memory just remembered that.

For an efficient agent memory system to work, you do not want the AI agent to always search this kind of information from episodic memory, because that is just a huge database about everything that happened in the past. You want some kind of durable summarized facts that you think are very important for AI to know.

That is why ChatGPT and Claude and all these AI agents are doing something similar: summarizing, at a certain frequency — not too frequent — all of these activities that happened into the semantic memory, so that the facts about you, about your company, about everything are condensed and saved properly for future retrievals.

This is actually very smart, because it not only saves a lot of token usage every single time, it also makes your tools much faster.

But let’s pause here for one second. If we summarize every single bit of new activity into the semantic memory, that sounds like we are just saving the information twice. What’s the point of having durable facts anyway?

That brings us to the concept of a gate: we only consolidate after a certain number of chats. It could be 20 conversations, it could be 100 activities — it could be anything.

In order for these systems to work together, we need a system that does consolidation after a certain number of messages, and then we feed that into the summarizer agent. The summarizer agent then summarizes the information into the semantic memory, and we call this the [unclear] into facts.

## Putting the Full Memory System Together

Congratulations — this is pretty much it. You have built up an entire memory system that is, in my opinion, quite modern in today’s context, and it should be embedded in any AI applications we are building these days, because it is so easy for users to engage with an AI agent, and so easy to build software.

But what happens is that the database just explodes if you are recording all these activities. So we need to figure out a way to very efficiently not only record the data, but also summarize the data, and then turn it into some core memory — which is semantic — and some episodic memory, which is just a timeline list of things.

At the same time, you can define the best practices for how the agent should behave in a certain task — which is what skills are about. I also made a video about agent skills and agent teams in the past — feel free to check them out.

Overall, I believe this is a very complete way to understand what an AI agent system should be performing with a memory that is added as a context layer on top of the entire interaction.

I hope you enjoy this. Let me know if you have any questions, and I’ll see you next time. Thanks.

## Key Takeaways

- Working memory (context/RAM) combines the user prompt, chat history, and system prompt so the LLM can answer with full current-session context.
- Procedural memory encodes behavior and skills (often as files like `skill.md`) — how the agent should act in recurring situations.
- Semantic memory stores durable facts and profiles in a vector store and is retrieved with RAG / top-K search so you do not dump an entire company knowledge base into the context window.
- Episodic memory is a dated timeline/log of past chats and activities; sessions are ephemeral unless you persist them there.
- Efficient systems gate consolidation: after N conversations/activities, a summarizer promotes important episodic material into compact semantic facts, cutting token cost and speeding retrieval.
