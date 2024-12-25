import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the API key
api_key = os.getenv("API_KEY")
if not api_key:
    st.error("API_KEY is not set. Please add it to your environment or .env file.")
    st.stop()

genai.configure(api_key=api_key)

# Function to upload a file to Gemini
def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    file = genai.upload_file(path, mime_type=mime_type)
    return file

# Streamlit UI
st.title("Gemini AI Blog Post Generator")
st.write("Generate an engaging blog post using AI by uploading an image. Optionally, provide a prompt to further guide the AI.")

# File upload section (optional for images)
uploaded_file = st.file_uploader("Upload an image (optional, e.g., JPEG, PNG)", type=["jpeg", "png"])

# Text area input for the prompt
if 'user_prompt' not in st.session_state:
    st.session_state.user_prompt = ""

# Default empty prompt to allow both options
if not st.session_state.user_prompt:
    st.session_state.user_prompt = st.text_area("Enter your prompt (optional)", placeholder="Describe what you want the AI to generate.")

# Ensure the user has uploaded an image or entered a prompt before generating
if st.button("Generate"):
    if not uploaded_file and not st.session_state.user_prompt.strip():
        st.error("Please upload an image or provide a prompt.")
    else:
        try:
            # If an image is uploaded, process it
            if uploaded_file is not None:
                # Save uploaded file locally
                temp_file_path = f"temp_{uploaded_file.name}"
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Upload the file to Gemini
                uploaded_gemini_file = upload_to_gemini(temp_file_path, mime_type="image/jpeg")
                st.success(f"File uploaded successfully: {uploaded_gemini_file.uri}")
            else:
                uploaded_gemini_file = None  # No image provided

            # Create the model for content generation
            generation_config = {
                "temperature": 0.9,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }

            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
            )

            # Start the chat session using the prompt (and image if provided)
            chat_history = []

            if st.session_state.user_prompt.strip():
                chat_history.append({
                    "role": "user",
                    "parts": [st.session_state.user_prompt],
                })

            if uploaded_gemini_file:
                chat_history.append({
                    "role": "user",
                    "parts": [uploaded_gemini_file],
                })

            # If no user prompt is given, generate the content based on the image alone
            if not chat_history:
                chat_history.append({
                    "role": "user",
                    "parts": ["Generate a blog post based on the uploaded image."],
                })

            chat_session = model.start_chat(history=chat_history)

            # Generate response
            response = chat_session.send_message("Generate content")
            response_text = response.text

            st.subheader("Generated Blog Post")
            st.write(response_text)

        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            # Clean up the temporary file
            if uploaded_file is not None and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
