from query import VectorSearch

# Initialize the search engine
searcher = VectorSearch()

# Example 1: Basic search
print("=" * 80)
print("Example 1: Basic Search")
print("=" * 80)
query = "I want to exercise more"
results = searcher.search(query, limit=3)

print(f"Query: {query}\n")
for i, (participant, coach, category, goal, similarity) in enumerate(results, 1):
    print(f"Result {i} (similarity: {similarity:.3f})")
    print(f"Category: {category}")
    print(f"Participant: {participant}")
    print(f"Coach: {coach}\n")

# Example 2: Get only coach responses
print("\n" + "=" * 80)
print("Example 2: Coach Responses Only")
print("=" * 80)
query = "I'm feeling stressed"
coach_responses = searcher.get_coach_responses(query, limit=3)

print(f"Query: {query}\n")
for i, response in enumerate(coach_responses, 1):
    print(f"{i}. {response}")

# Example 3: Search with dictionary results
print("\n" + "=" * 80)
print("Example 3: Dictionary Format")
print("=" * 80)
query = "help with my goals"
results = searcher.search_with_details(query, limit=2, min_similarity=0.3)

print(f"Query: {query}\n")
for i, result in enumerate(results, 1):
    print(f"Result {i}:")
    print(f"  Similarity: {result['similarity']:.3f}")
    print(f"  Category: {result['category']}")
    print(f"  Coach said: {result['coach_response']}\n")
