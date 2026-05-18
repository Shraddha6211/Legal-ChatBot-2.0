# backend/core/chains.py

import sys
import os
sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.dirname(__file__))))

import json
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from backend.core.retriever import retrieve
from backend.memory.session import get_history, save_message
from backend.memory.cache import search_cache, save_to_cache
from config import settings

client = OpenAI(api_key=settings.openai_api_key)
embeddings_model = OpenAIEmbeddings(
    model=settings.embedding_model,
    openai_api_key=settings.openai_api_key
)

# ── Tool Definitions ──────────────────────────
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_constitution",
            "description": "Search Constitution of Nepal for relevant articles. Use when user asks about constitutional rights, duties, government structure, elections, or any legal topic that needs knowledge base lookup.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Search conversation history. Use when user says 'tell me more', 'elaborate', 'what did I ask', refers to previous messages, or asks follow-up questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for in history"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_article",
            "description": "Get specific article by number. Use when user mentions specific article number like 'Article 18' or 'Article 42'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "article_number": {
                        "type": "integer",
                        "description": "Article number to fetch"
                    }
                },
                "required": ["article_number"]
            }
        }
    }
]


# ── Main Chat Function ────────────────────────
def chat(
    question: str,
    session_id: str
) -> dict:
    """
    Main entry point for chat.
    Returns: {answer, sources, cache_hit, session_id}
    """
    print(f"\n=== CHAT: '{question}' ===")
    sources = []

    # ── Step 1: Check Semantic Cache ──────────
    # embed question
    question_embedding = embeddings_model.embed_query(question)
    # search cache
    cached_answer = search_cache(question, question_embedding)
    # if hit → return immediately!
    if cached_answer:
        return {
            "answer": cached_answer,
            "sources": [],
            "cache_hit": True,
            "session_id": session_id
        }

    # ── Step 2: Load Session Memory ───────────
    history = get_history(session_id)
    print(f"History loaded: {len(history)} messages")

    # ── Step 3: Define Inner Tool Functions ───
    # (closure pattern - access history + sources!)
    
    def search_constitution(query: str) -> str:
        # call retrieve(query)
        docs = retrieve(query)
        # build sources list
        if not docs: 
            return "No relevant constitutional aricles found"
        # return context string
        context_parts = []

        for doc in docs:
            article_number = doc.get("article_number", "Unknown")
            title = doc.get("title", "")
            content = doc.get("content", "")

            sources.append({
                "article": article_number,
                "title": title,
                "similarity": doc.get("similarity", 0)
            })

            context_parts.append(
                f"Article {article_number}: {title}\n{content}"
            )

        return "\n\n".join(context_parts)


    def search_memory(query: str) -> str:
        # search history for query
        # return relevant messages as string
        if not history:
            return "No conversation history found."

        relevant = []

        query_lower = query.lower()

        for msg in history:
            if any(word in msg["content"].lower()
                   for word in query_lower.split()):
                relevant.append(
                    f"{msg['role'].upper()}: {msg['content']}"
                )

        if not relevant:
            # return last 4 messages as context
            recent = history[-4:]
            relevant = [
                f"{m['role'].upper()}: {m['content']}"
                for m in recent
            ]

        return "\n".join(relevant)

    def get_article(article_number: int) -> str:
        # search for specific article
        # return article content
        docs = retrieve(f"Article {article_number} Nepal Constitution")

        if not docs:
            return f"Article {article_number} not found."

        for doc in docs:
            if doc.get("article_number") == article_number:
                sources.append({
                    "article": article_number,
                    "title": doc.get("title", ""),
                    "similarity": doc.get("similarity", 0)
                })
                return (
                    f"Article {article_number}: "
                    f"{doc.get('title', '')}\n"
                    f"{doc.get('content', '')}"
                )

        # return best match if exact not found
        doc = docs[0]
        sources.append({
            "article": doc.get("article_number"),
            "title": doc.get("title", ""),
            "similarity": doc.get("similarity", 0)
        })
        return (
            f"Article {doc.get('article_number')}: "
            f"{doc.get('title', '')}\n"
            f"{doc.get('content', '')}"
        )

    def run_tool(tool_name: str, tool_args: dict) -> str:
        # dispatch to correct function
        if tool_name == "search_constitution":
            return search_constitution(
                tool_args["query"]
            )

        elif tool_name == "search_memory":
            return search_memory(
                tool_args["query"]
            )

        elif tool_name == "get_article":
            return get_article(
                tool_args["article_number"]
            )

        return "Invalid tool."

    # ── Step 4: Tool Calling Loop ─────────────
    messages = [
        {
            "role": "system",
            "content": """You are a legal assistant for 
            the Constitution of Nepal.
            Use tools to find information.
            Never answer from your own knowledge.
            Always cite article numbers.
            Be concise (3-5 sentences) unless asked for detail."""
        }
    ]

    # add history to messages
    for msg in history[-settings.max_history_messages:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # add current question
    messages.append({
        "role": "user",
        "content": question
    })

    # tool calling loop
    while True:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message
        assistant_message = {
            "role": message.role,
            "content": message.content
        }

        # from chatgpt
        if message.tool_calls:
            assistant_message["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]

        messages.append(assistant_message)

        if response.choices[0].finish_reason == "tool_calls":
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(
                    tool_call.function.arguments
                )
                print(f"GPT calling: {tool_name}({tool_args})")
                tool_result = run_tool(tool_name, tool_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
        else:
            answer = message.content
            print(f"Final answer: {answer[:100]}...")
            break

    # ── Step 5: Save to Memory + Cache ────────
    # save user message to session
    # save assistant answer to session
    # save to semantic cache
     # save user message to session
    save_message(
        session_id=session_id,
        role="user",
        content=question
    )

    # save assistant answer to session
    save_message(
        session_id=session_id,
        role="assistant",
        content=answer
    )

    # save to semantic cache
    save_to_cache(
        question=question,
        answer=answer,
        question_embedding=question_embedding
    )

    return {
        "answer": answer,
        "sources": sources,
        "cache_hit": False,
        "session_id": session_id
    }