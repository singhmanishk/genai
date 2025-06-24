# Problem Statement: Create a new route for the E-commerce Tool

In this exercise, you will be creating a new route for the E-commerce Tool. This new route will be called `small-talk` and will be uses to handle colloquial conversations with the user.

### **Tasks**:
1. Create a new route called `small-talk` in the `router.py` file with the following utterances:
    - "How are you?"
    - "What is your name?"
    - "Are you a robot?"
    - "What are you?"
    - "What do you do?"

2. Create a new module called `smalltalk.py` that will contain the `talk` function that uses Groq to answer user's question.

3. Update the `ask` function in `main.py` to handle the new route `small-talk`.