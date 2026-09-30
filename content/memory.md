# Memory in AI Agents
 
## Overview
 
Memory allows AI agents to retain information across interactions and use past knowledge to make better decisions.
 
Unlike a traditional chatbot that only reacts to the current prompt, an agent with memory can:
 
- Remember user preferences
- Recall previous tasks
- Personalize recommendations
- Maintain long-running workflows

## Learning Objectives
 
After completing this lesson, you should be able to:
 
- Explain why memory is important in AI agents
- Distinguish between short-term and long-term memory
- Implement memory in a simple agent
- Identify risks associated with agent memory
- Design memory-aware agent workflows

 
## Why Do Agents Need Memory?
 
Imagine a travel assistant.
 
User:
 
> I prefer window seats.
 
Later:
 
> Find me a flight to Paris.
 
Without memory:
 
```text
Agent asks again:
What seat do you prefer?
```
With memory:
 
```text
Agent remembers:
Window seat preference.
```
 
Memory creates personalization and continuity.
 
---
 
## Types of Memory
 
### Short-Term Memory
 
Stores information from the current conversation.
 
Example:
 
```text
Destination: Stockholm
Budget: 5000 SEK
Trip length: 3 days
```
 
Duration:
 
- Current session only
 
---
 
### Long-Term Memory
 
Stores information across multiple sessions.
 
Example:
 
```text
Preferred airline: SAS
Seat preference: Window
Dietary preference: Vegetarian
```
 
Duration:
 
- Days
- Months
- Years
 
---
 
### Semantic Memory
 
Stores facts and knowledge.
 
Example:
 
```text
User is based in Sweden.
User often travels for conferences.
```
 
---
 
### Episodic Memory
 
Stores past experiences.
 
Example:
 
```text
Trip to Paris in 2025.
Stayed near the city centre.
Preferred walking tours.
```
 
---
 
## Memory Architecture
 
```text
User
|
v
Agent
|
+------ Working Memory
|
+------ Long-Term Memory
|
+------ Knowledge Base
```
 
The agent retrieves relevant information before making decisions.
 
---
 
## Example: Travel Planner Agent
 
### First Interaction
 
User:
 
> I do not like museums.
 
Memory Store:
 
```json
{
"likes_museums": false
}
```
 
### Future Interaction
 
User:
 
> Plan a trip to Stockholm.
 
Agent retrieves memory and avoids:
 
- Vasa Museum
- ABBA Museum
 
Instead recommends:
 
- Archipelago Tour
- Gamla Stan Walking Tour
- Skansen
 
---
 
## Hands-On Exercise
 
### Step 1: Create a Memory Dictionary
 
```python
memory = {}
```
 
### Step 2: Store Preferences
 
```python
memory["seat_preference"] = "window"
memory["diet"] = "vegetarian"
```
 
### Step 3: Use Memory
 
```python
print(
f"Preferred seat: {memory['seat_preference']}"
)
```
 
### Expected Output
 
```text
Preferred seat: window
```
 
---
 
## Advanced Memory
 
Production agents often use:
 
- Vector Databases
- Embeddings
- Retrieval
- Memory Ranking
 
Examples:
 
- ChromaDB
- FAISS
- Qdrant
 
These systems allow agents to retrieve semantically relevant memories.
 
---
 
## Risks and Challenges
 
### Privacy
 
Memory can contain:
 
- Personal information
- Travel history
- User preferences
 
Protect stored data appropriately.
 
### Hallucinated Memories
 
The agent may incorrectly infer user preferences.
 
### Outdated Memories
 
Preferences change.
 
Example:
 
```text
Previously preferred window seat.
Now prefers aisle seat.
```
 
Memory must be updated.
 
---
 
## Responsible AI Considerations
 
When designing memory systems:
 
- Be transparent about stored information
- Allow users to update preferences
- Allow users to delete memories
- Minimize sensitive data collection
- Apply access controls
 
---
 
## Key Takeaways
 
- Memory enables personalization.
- Short-term memory supports current tasks.
- Long-term memory supports future tasks.
- Memory improves agent performance.
- Memory requires privacy and governance considerations.
