
from ddgs import DDGS


def web_search(topic, max_results=8):
    """Search the web using multiple query variations."""

    # Simplify long user prompts into shorter search queries.
    clean_topic = topic.strip()

    for word in ["Research the ", "Research ", "research the ", "research "]:
        if clean_topic.startswith(word):
            clean_topic = clean_topic[len(word):]
            break

    clean_topic = clean_topic.split(",")[0].strip()

    queries = [
        clean_topic,
        "latest news " + clean_topic,
        "2026 " + clean_topic
    ]

    all_results = []
    seen_urls = set()
    errors = []

    for query in queries:
        try:
            print(f"Searching DuckDuckGo for: {query}", flush=True)

            with DDGS() as ddgs:
                results = ddgs.text(
                    query,
                    max_results=max_results,
                    backend="auto"
                )

                for item in results or []:
                    url = item.get("href") or item.get("url") or ""

                    if url and url not in seen_urls:
                        seen_urls.add(url)

                        all_results.append({
                            "title": item.get("title") or "Untitled",
                            "url": url,
                            "snippet": (
                                item.get("body")
                                or item.get("snippet")
                                or ""
                            )
                        })

            if all_results:
                break

        except Exception as error:
            errors.append(f"{query}: {error}")
            print(f"Search attempt failed: {error}", flush=True)

    if not all_results:
        print("All DuckDuckGo search attempts failed.", flush=True)
        if errors:
            raise RuntimeError("; ".join(errors))
        return []

    print(f"Successfully collected {len(all_results)} search results.", flush=True)

    return all_results[:max_results]
