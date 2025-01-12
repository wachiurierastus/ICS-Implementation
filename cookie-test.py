import streamlit as st
from datetime import datetime
import os

from mmse_app import next_page


def cookie_test():
    st.subheader("Cookie Test")
    st.write("This test evaluates verbal fluency and description abilities.")

    # Create recordings directory if it doesn't exist
    if not os.path.exists("recordings"):
        os.makedirs("recordings")

    # Display the cookie image
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("img/cookie.jpeg", caption="Cookie Image", use_column_width=True)
        st.write("Please describe everything you see in this image in as much detail as possible.")

    # Recording section
    st.subheader("Record Your Description")

    # Audio input for recording
    audio_file = st.audio_input("Press the button below to record your description")

    if audio_file:
        # Save audio file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        patient_id = st.session_state.get('patient_name', 'unknown').replace(" ", "_")
        audio_filename = f"recordings/cookie_test_{patient_id}_{timestamp}.wav"

        with open(audio_filename, 'wb') as f:
            f.write(audio_file.read())

        st.success(f"Audio recorded successfully and saved as {audio_filename}")

        # Playback section
        st.subheader("Review Recording")
        st.audio(audio_filename)

        # Volume control (manual playback volume control is typically done through the audio player UI)

        # Download button
        with open(audio_filename, "rb") as file:
            st.download_button(
                label="Download Recording",
                data=file,
                file_name=os.path.basename(audio_filename),
                mime="audio/wav"
            )

    # Error handling and instructions
    with st.expander("Troubleshooting"):
        st.write("""
        If you're having issues with the recording:
        1. Make sure your microphone is connected and working
        2. Allow microphone access in your browser
        3. Try refreshing the page if the recording doesn't start
        4. Check your system's audio input settings
        """)

    # Add notes section for examiner
    notes = st.text_area(
        "Examiner Notes (Optional)",
        help="Record any observations about the patient's description, fluency, or behavior during the test"
    )
    if notes:
        if 'responses' not in st.session_state:
            st.session_state.responses = {}
        st.session_state.responses['cookie_test_notes'] = notes

    # Navigation
    if st.button("Complete Test"):
        if 'completed_sections' not in st.session_state:
            st.session_state.completed_sections = set()
        st.session_state.completed_sections.add('cookie_test')
        next_page()  # Assuming this is defined elsewhere
