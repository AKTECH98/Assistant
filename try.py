import streamlit as st
from ChatAgent import init_agent

st.set_page_config(page_title="Chat with NOVA", page_icon="💬")

# Custom CSS for full-screen chat layout
st.markdown("""
<style>
html, body, .stApp {
    height: 100%;
    # background-color: #F9F9F9;
    margin: 0;
}

.chat-container {
    display: flex;
    flex-direction: column;
    padding: 20px;
    margin-bottom: 80px; /* Leave space for the input box */
}

.chat-bubble {
    max-width: 70%;
    padding: 10px 15px;
    border-radius: 18px;
    font-size: 16px;
    line-height: 1.4;
    margin: 6px 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    word-wrap: break-word;
}

.user-bubble {
    background-color: #D1F0FF;
    color: #333;
    align-self: flex-end;
}

.assistant-bubble {
    background-color: #ECEFF1;
    color: #333;
    align-self: flex-start;
}

.stChatInputContainer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: #fff;
    padding: 10px 20px;
    box-shadow: 0 -2px 4px rgba(0,0,0,0.1);
}

.stChatInputContainer .stTextInput>div>div>input {
    background-color: #fff;
    border-radius: 20px;
    padding: 10px 15px;
    border: 1px solid #ccc;
    box-shadow: none;
}
</style>
""", unsafe_allow_html=True)

st.title("💬 N.O.V.A")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
st.markdown("```python\nprint('Hello World')\n```")
if "agent" not in st.session_state:
    st.session_state.agent = init_agent()

# Chat container
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in st.session_state.chat_history:
    role = msg["role"]
    bubble_class = "user-bubble" if role == "user" else "assistant-bubble"
    st.markdown(
        f"""
        <div class="chat-bubble {bubble_class}">{msg["content"]}</div>
        """,
        unsafe_allow_html=True
    )
# Input box (overlayed)
user_input = st.chat_input("Type your message...")
st.markdown('</div>', unsafe_allow_html=True)

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    # Display user's message
    st.markdown(
        f"""
        <div class="chat-container">
            <div class="chat-bubble user-bubble">{user_input}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.spinner("Thinking..."):
        config = {"configurable": {"thread_id": "1"}}
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.chat_history]

        bot_message = ""
        for event in st.session_state.agent.graph.stream({"messages": messages}, config=config):
            for value in event.values():
                bot_message = value["messages"][-1].content

        st.session_state.chat_history.append({"role": "assistant", "content": bot_message})
        st.markdown(
            f"""
            <div class="chat-container">
                <div class="chat-bubble assistant-bubble">{bot_message}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
