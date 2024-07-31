import streamlit as st

from utils import human_stt, ai_response, ai_tts

st.title("Automatic Broccoli the Voice Chatbot")
st.text("Llama 3.1 with LangChain")


def chat_bot():
    st.markdown("Transcription started...")
    while True:
        stt_output = human_stt()
        st.markdown(f"You: {stt_output}")

        if stt_output == "bye":
            st.markdown("Chat Ended")
            break

        response = ai_response(stt_output)
        # ai_tts(response)  # TODO TTS not working
        st.markdown(f"AI Assistant: {response['response']}")


if 'button' not in st.session_state:
    st.session_state.button = False


def click_button():
    st.session_state.button = not st.session_state.button


st.button('CHAT', on_click=click_button)  # TODO Add Speaking Animation when mic is one, otherwise mic icon.

if st.session_state.button:
    # The message and nested widget will remain on the page
    st.write("Listening On.")
    st.write("Say 'BYE' to end chat or click button.")
    chat_bot()
else:
    st.write('Listening Off.')
