import streamlit as st
from ChatAgent import init_agent

st.set_page_config(page_title="Study With Nova")

# Initialize state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "title_shown" not in st.session_state:
    st.session_state.title_shown = True
if "agent" not in st.session_state:
    st.session_state.agent = init_agent()
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# Styling for hover icons
st.markdown("""
    <style>
    .chat-container {
        position: relative;
        margin-bottom: 10px;
        padding: 8px;
        border-radius: 8px;
        background: #f0f2f6;
        max-width: 80%;
    }
    .chat-buttons {
        position: absolute;
        bottom: 4px;
        right: 4px; /* changed to right side */
        display: none;
        gap: 4px;
    }
    .chat-container:hover .chat-buttons {
        display: flex;
    }
    .chat-button {
        background: transparent;
        border: none;
        cursor: pointer;
        padding: 0;
    }
    </style>
""", unsafe_allow_html=True)

# Display chat history
def display_chat():
    for i, msg in enumerate(st.session_state.chat_history):
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                if st.session_state.edit_index == i:
                    edited_text = st.text_input("Edit your message:", value=msg["content"], key=f"edit_{i}")
                    if st.button("Send Edited", key=f"send_{i}"):
                        st.session_state.chat_history[i]["content"] = edited_text
                        st.session_state.chat_history = st.session_state.chat_history[:i+1]
                        st.session_state.edit_index = None
                        st.session_state.new_input = edited_text
                        st.session_state.title_shown = False
                        st.rerun()
                    if st.button("Cancel Edit", key=f"cancel_{i}"):
                        st.session_state.edit_index = None
                else:
                    st.markdown(f"""
                        <div class="chat-container">
                            <div>{msg["content"]}</div>
                            <div class="chat-buttons">
                                <button class="chat-button" onclick="window.parent.postMessage({{'type': 'edit', 'index': {i}}}, '*')">
                                    ✏️
                                </button>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="chat-container">
                        <div>{msg["content"]}</div>
                        <div class="chat-buttons">
                            <button class="chat-button" onclick="navigator.clipboard.writeText(`{msg['content']}`)">
                                📋
                            </button>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

display_chat()

# Edit button logic (using JS postMessage)
st.markdown("""
    <script>
    window.addEventListener("message", (event) => {
        if (event.data.type === "edit") {
            const index = event.data.index;
            const pyCode = `
            st.session_state.edit_index = ${index}
        st.rerun()
        `;
            const pyRunner = parent.document.querySelector("iframe").contentWindow.streamlit;
            pyRunner.runScript(pyCode);
        }
    });
    </script>
""", unsafe_allow_html=True)

# Chat input at bottom
if st.session_state.edit_index is None:
    user_input = st.chat_input("Type your message here...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.text(user_input)

        with st.spinner("Thinking..."):
            config = {"configurable": {"thread_id": "1"}}
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.chat_history]

            response_placeholder = st.empty()
            bot_message = ""
            for event in st.session_state.agent.graph.stream({"messages": messages}, config=config):
                for value in event.values():
                    new_text = value["messages"][-1].content
                    if new_text != bot_message:
                        bot_message = new_text
                        response_placeholder.text(bot_message)

            st.session_state.chat_history.append({"role": "assistant", "content": bot_message})

        st.session_state.title_shown = False
        st.rerun()
