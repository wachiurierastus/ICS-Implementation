import os
from venv import logger
import sklearn
import streamlit as st
import datetime
import requests
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz


def init_session_state():
    if 'page' not in st.session_state:
        st.session_state.page = 0
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'responses' not in st.session_state:
        st.session_state.responses = {}
    if 'exam_type' not in st.session_state:
        st.session_state.exam_type = None


def cookie_test():
    st.subheader("Cookie Test")
    st.write("This test evaluates verbal fluency and description abilities.")

    # Create recordings directory if it doesn't exist
    if not os.path.exists("recordings"):
        os.makedirs("recordings")

    # Display the cookie image
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("img/cookie.jpeg", caption="Cookie Image", use_container_width=True)
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

        # Send to Flask backend for analysis
        if st.button("Analyze Recording",key="Analyze Recording"):
            try:
                # Get MMSE score from session state
                mmse_score = st.session_state.score
                print("mmse", mmse_score)

                # Prepare the files and data for the request
                files = {'audio': open(audio_filename, 'rb')}
                data = {'mmse': str(mmse_score)}

                # Make request to Flask backend
                response = requests.post('http://localhost:5000/analyze',
                                         files=files,
                                         data=data)

                if response.status_code == 200:
                    result = response.json()

                    # Store results in session state
                    st.session_state.diagnosis = result['diagnosis']
                    st.session_state.stage = result['stage']

                    # Display initial results
                    st.success("Analysis completed successfully!")
                    display_prognosis()

                    # Enable the Complete Test button
                    st.session_state.analysis_complete = True
                else:
                    st.error(f"Analysis failed: {response.json().get('error', 'Unknown error')}")

            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
                logger.error(f"Analysis error: {str(e)}")

        # Download button
        with open(audio_filename, "rb") as file:
            st.download_button(
                label="Download Recording",
                data=file,
                file_name=os.path.basename(audio_filename),
                mime="audio/wav",
                key = "download_recording"
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

    # Navigation
    if st.button("Complete Test", key ="complete_test_1") and st.session_state.get('analysis_complete', False):
        if 'completed_sections' not in st.session_state:
            st.session_state.completed_sections = set()
        st.session_state.completed_sections.add('cookie_test')
        next_page()
    elif st.button("Complete Test",key ="complete_test_2") :
        st.warning("Please analyze the recording before proceeding.")


def display_prognosis():
    st.title("Prognosis Report")

    if 'diagnosis' not in st.session_state or 'stage' not in st.session_state:
        st.error("No diagnosis available. Please complete the cookie test first.")
        return

    # Display diagnosis information
    st.header("Diagnosis Results")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Diagnosis", st.session_state.diagnosis)
    with col2:
        st.metric("Stage", st.session_state.stage)

    # Provide detailed information based on diagnosis and stage
    st.subheader("Detailed Assessment")

    if st.session_state.diagnosis == "No Dementia":
        st.write("""
        Based on the analysis of your cookie test and MMSE score, no significant cognitive impairment 
        was detected. However, regular cognitive check-ups are recommended for early detection of any 
        future changes.
        """)
    else:
        stage_info = {
            "Stage 1 (Mild)": """
            - Early stage of cognitive decline
            - Minor memory problems and cognitive changes
            - Fully independent in daily activities
            - Excellent candidate for early intervention
            - Regular monitoring and cognitive exercises recommended
            """,
            "Stage 2 (Mild to Moderate)": """
            - Increasing memory difficulties
            - Some challenges with complex tasks
            - Generally independent but may need occasional assistance
            - Important to start planning for future care needs
            - Benefit from structured daily routines
            """,
            "Stage 3 (Moderate)": """
            - More pronounced memory and communication challenges
            - Increased difficulty with daily tasks
            - Requires regular assistance and supervision
            - Important to establish comprehensive support systems
            - Safety measures should be implemented
            """,
            "Stage 4 (Severe)": """
            - Significant cognitive impairment
            - Requires extensive support for daily activities
            - Close medical supervision needed
            - Focus on quality of life and comfort
            - Full-time care typically required
            """
        }

        st.markdown(stage_info.get(st.session_state.stage, "Stage information not available"))

    # Recommendations section
    st.subheader("Recommendations")
    st.write("""
    1. Schedule a follow-up with a healthcare provider to discuss these results
    2. Consider lifestyle modifications that may help maintain cognitive function
    3. Explore available support groups and resources
    4. Plan regular cognitive assessments to monitor any changes
    """)

def next_page():
    st.session_state.page += 1


def render_examiner_section():
    # Constants for the examiner section
    TOTAL_PAGES = 13
    MAX_SCORE = 30

    # Section names for progress tracking
    SECTIONS = {
        1: "Patient Information",
        2: "Orientation to Time",
        3: "Orientation to Place",
        4: "Registration",
        5: "Attention and Calculation",
        6: "Recall",
        7: "Naming",
        8: "Repetition",
        9: "3-Stage Command",
        10: "Reading and Writing",
        11: "Copying",
        12: "Cookie test"
    }

    # Initialize section completion status if not exists
    if 'completed_sections' not in st.session_state:
        st.session_state.completed_sections = set()

    # Progress indicator
    st.progress(len(st.session_state.completed_sections) / TOTAL_PAGES)

    # Display progress and score
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.write(f"Current Score: {st.session_state.score}/{MAX_SCORE}")
    with col3:
        st.write(f"Section: {SECTIONS[st.session_state.page]}")

    # Navigation buttons
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.session_state.page > 1:
            if st.button("← Previous Section"):
                st.session_state.page -= 1
                st.rerun()

    # Section completion status
    st.write("Completed sections:")
    for section_num, section_name in SECTIONS.items():
        if section_num in st.session_state.completed_sections:
            st.success(f"✓ {section_name}")
        else:
            st.info(f"○ {section_name}")

    st.divider()

    if st.session_state.page == 1:
        st.write("Patient Information")
        patient_name = st.text_input("Patient Name")
        examiner_name = st.text_input("Examiner Name")
        date = st.date_input("Date of Examination")

        # Validation message
        if not all([patient_name, examiner_name, date]):
            st.warning("Please complete all fields before proceeding")

        if all([patient_name, examiner_name, date]):
            st.session_state.responses.update({
                'patient_name': patient_name,
                'examiner_name': examiner_name,
                'exam_date': date
            })
            if st.button("Begin Assessment", key ="Begin Assessment"):
                st.session_state.completed_sections.add(1)
                next_page()

    elif st.session_state.page == 2:
        st.subheader("Orientation to Time (5 points)")
        st.write("Ask: 'What is the...'")

        questions = [
            ("Year?", "year_response"),
            ("Season?", "season_response"),
            ("Month of the year?", "month_response"),
            ("Day of the week?", "day_response"),
            ("Date?", "date_response")
        ]

        all_answered = True
        score = 0

        for question, key in questions:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(question)
            with col2:
                response = st.radio(
                    f"Response for {question}",
                    ["Awaiting Response", "Patient Answered Correctly", "Patient Answered Incorrectly"],
                    key=key,
                    help="Select the appropriate response based on patient's answer"
                )
                if response == "Awaiting Response":
                    all_answered = False
                elif response == "Patient Answered Correctly":
                    score += 1

        if not all_answered:
            st.warning("Please evaluate all responses before proceeding")

        if st.button("Next", disabled=not all_answered, key="Page2"):
            st.session_state.score += score
            st.session_state.completed_sections.add(2)
            next_page()

    # Similar pattern continues for other sections...
    # I'll show the pattern for one more section, then can continue with the rest if desired

    elif st.session_state.page == 3:
        st.subheader("Orientation to Place (5 points)")
        st.write("Ask: 'Where are we...'")

        questions = [
            ("State?", "state_response"),
            ("County?", "county_response"),
            ("Town/City?", "city_response"),
            ("Hospital/Facility?", "facility_response"),
            ("Floor?", "floor_response")
        ]

        all_answered = True
        score = 0

        for question, key in questions:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(question)
                # Add helper text
                st.caption("Record patient's response to location question")
            with col2:
                response = st.radio(
                    f"Evaluation for {question}",
                    ["Awaiting Response", "Patient Answered Correctly", "Patient Answered Incorrectly"],
                    key=key,
                    help="Select whether the patient correctly identified this location"
                )
                if response == "Awaiting Response":
                    all_answered = False
                elif response == "Patient Answered Correctly":
                    score += 1

        if not all_answered:
            st.warning("⚠️ Please complete all evaluations before proceeding")

        if st.button("Next", disabled=not all_answered, key="Page3"):
            st.session_state.score += score
            st.session_state.completed_sections.add(3)
            next_page()

        elif st.session_state.page == 4:
            st.subheader("Registration (3 points)")
        st.write("""Instructions: Name three objects (Apple, Penny, Table). 
                 Take one second to say each. Ask the patient to repeat all three.""")

        st.write("Score one point for each correct answer on the first trial.")

        objects = [
            ("Apple", "apple_response"),
            ("Penny", "penny_response"),
            ("Table", "table_response")
        ]

        all_answered = True
        score = 0

        for obj, key in objects:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"Said '{obj}'")
                st.caption("Evaluate patient's immediate recall of this word")
            with col2:
                response = st.radio(
                    f"Patient's recall of '{obj}'",
                    ["Awaiting Response", "Patient Answered Correctly", "Patient Answered Incorrectly"],
                    key=key,
                    help="Select whether the patient correctly repeated this word"
                )
                if response == "Awaiting Response":
                    all_answered = False
                elif response == "Patient Answered Correctly":
                    score += 1

        trials = st.number_input("Number of trials needed:", min_value=1, value=1)
        st.session_state.responses['registration_trials'] = trials

        if not all_answered:
            st.warning("⚠️ Please evaluate all responses before proceeding")

        if st.button("Next", disabled=not all_answered, key ="Page4"):
            st.session_state.score += score
            st.session_state.completed_sections.add(4)
            next_page()

    elif st.session_state.page == 5:
        st.subheader("Attention and Calculation (5 points)")
        st.write("""Instructions: Ask the patient to begin with 100 and count 
                 backwards by 7. Stop after 5 subtractions.""")
        st.caption("Each subtraction is scored independently. Any error makes that step incorrect.")

        calculations = [
            ("100 - 7 = 93", "calc1_response"),
            ("93 - 7 = 86", "calc2_response"),
            ("86 - 7 = 79", "calc3_response"),
            ("79 - 7 = 72", "calc4_response"),
            ("72 - 7 = 65", "calc5_response")
        ]

        all_answered = True
        score = 0

        for calc, key in calculations:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(calc)
                st.caption("Evaluate this specific calculation step")
            with col2:
                response = st.radio(
                    f"Evaluation for {calc}",
                    ["Awaiting Response", "Patient Answered Correctly", "Patient Answered Incorrectly"],
                    key=key,
                    help="Select whether the patient calculated this step correctly"
                )
                if response == "Awaiting Response":
                    all_answered = False
                elif response == "Patient Answered Correctly":
                    score += 1

        if not all_answered:
            st.warning("⚠️ Please evaluate all calculations before proceeding")

        if st.button("Next", disabled=not all_answered,key="Page5"):
            st.session_state.score += score
            st.session_state.completed_sections.add(5)
            next_page()

    elif st.session_state.page == 6:
        st.subheader("Recall (3 points)")
        st.write("Ask: 'What were the three objects I asked you to remember?'")
        st.caption("Test delayed recall of the three objects from the Registration section")

        objects = [
            ("Apple", "recall_apple"),
            ("Penny", "recall_penny"),
            ("Table", "recall_table")
        ]

        all_answered = True
        score = 0

        for obj, key in objects:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"Recalled '{obj}'?")
                st.caption("Evaluate patient's delayed recall of this word")
            with col2:
                response = st.radio(
                    f"Patient's recall of '{obj}'",
                    ["Awaiting Response", "Patient Answered Correctly", "Patient Answered Incorrectly"],
                    key=key,
                    help="Select whether the patient correctly remembered this word"
                )
                if response == "Awaiting Response":
                    all_answered = False
                elif response == "Patient Answered Correctly":
                    score += 1

        if not all_answered:
            st.warning("⚠️ Please evaluate all recall responses before proceeding")

        if st.button("Next", disabled=not all_answered,key="Page6"):
            st.session_state.score += score
            st.session_state.completed_sections.add(6)
            next_page()

    elif st.session_state.page == 7:
        st.subheader("Naming (2 points)")
        st.write("Show the patient these objects and ask them to name them:")
        st.caption("Score one point for each object correctly named")

        objects = [
            ("Watch", "name_watch"),
            ("Pencil", "name_pencil")
        ]

        all_answered = True
        score = 0

        for obj, key in objects:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"Naming '{obj}'")
                st.caption(f"Patient should identify this object without assistance")
            with col2:
                response = st.radio(
                    f"Patient's naming of '{obj}'",
                    ["Awaiting Response", "Patient Answered Correctly", "Patient Answered Incorrectly"],
                    key=key,
                    help="Select whether the patient correctly named this object"
                )
                if response == "Awaiting Response":
                    all_answered = False
                elif response == "Patient Answered Correctly":
                    score += 1

        if not all_answered:
            st.warning("⚠️ Please evaluate all naming responses before proceeding")

        if st.button("Next", disabled=not all_answered,key="Page7"):
            st.session_state.score += score
            st.session_state.completed_sections.add(7)
            next_page()

    elif st.session_state.page == 8:
        st.subheader("Repetition (1 point)")
        st.write("""Instructions: Ask the patient to repeat:
                 'No ifs, ands, or buts'""")
        st.caption("Patient must repeat the phrase exactly as stated")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Patient's phrase repetition")
            st.caption("Evaluate accuracy of the entire phrase")
        with col2:
            response = st.radio(
                "Phrase repetition evaluation",
                ["Awaiting Response", "Patient Repeated Correctly", "Patient Repeated Incorrectly"],
                key="phrase_repetition",
                help="Select whether the patient repeated the entire phrase correctly"
            )

        if response == "Awaiting Response":
            st.warning("⚠️ Please evaluate the phrase repetition before proceeding")

        if st.button("Next", disabled=response == "Awaiting Response",key="Page8"):
            if response == "Patient Repeated Correctly":
                st.session_state.score += 1
            st.session_state.completed_sections.add(8)
            next_page()

    elif st.session_state.page == 9:
        st.subheader("3-Stage Command (3 points)")
        st.write("""Instructions: Give the patient a plain piece of paper 
                 and say: 'Take the paper in your right hand, 
                 fold it in half, and put it on the floor.'""")
        st.caption("Score one point for each part correctly executed")

        commands = [
            ("Took paper in right hand", "command_hand"),
            ("Folded paper in half", "command_fold"),
            ("Put paper on floor", "command_floor")
        ]

        all_answered = True
        score = 0

        for command, key in commands:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(command)
                st.caption("Evaluate this specific action")
            with col2:
                response = st.radio(
                    f"Evaluation of '{command}'",
                    ["Awaiting Response", "Patient Performed Correctly", "Patient Performed Incorrectly"],
                    key=key,
                    help="Select whether the patient performed this action correctly"
                )
                if response == "Awaiting Response":
                    all_answered = False
                elif response == "Patient Performed Correctly":
                    score += 1

        if not all_answered:
            st.warning("⚠️ Please evaluate all commands before proceeding")

        if st.button("Next", disabled=not all_answered,key="Page9"):
            st.session_state.score += score
            st.session_state.completed_sections.add(9)
            next_page()

    elif st.session_state.page == 10:
        st.subheader("Reading and Writing (2 points)")
        st.caption("Two separate tasks: reading comprehension and sentence writing")

        # Reading task
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("""1. Show the patient the words: 'CLOSE YOUR EYES'
                    Ask them to read and do what it says.""")
            st.caption("Patient should read and perform the action")
        with col2:
            reading_response = st.radio(
                "Reading comprehension evaluation",
                ["Awaiting Response", "Patient Performed Correctly", "Patient Performed Incorrectly"],
                key="reading_response",
                help="Select whether the patient both read and performed the action"
            )

        # Writing task
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("""2. Ask the patient to write a complete sentence.""")
            st.caption("Sentence must contain a subject and verb and make sense")
        with col2:
            writing_response = st.radio(
                "Writing evaluation",
                ["Awaiting Response", "Patient Wrote Correctly", "Patient Wrote Incorrectly"],
                key="writing_response",
                help="Select whether the patient wrote a complete, sensible sentence"
            )

        patient_sentence = st.text_area("Record patient's sentence here:", "")
        if patient_sentence:
            st.session_state.responses['written_sentence'] = patient_sentence

        all_answered = reading_response != "Awaiting Response" and writing_response != "Awaiting Response"

        if not all_answered:
            st.warning("⚠️ Please evaluate both reading and writing tasks before proceeding")

        if st.button("Next", disabled=not all_answered, key="Page10"):
            if reading_response == "Patient Performed Correctly":
                st.session_state.score += 1
            if writing_response == "Patient Wrote Correctly":
                st.session_state.score += 1
            st.session_state.completed_sections.add(10)
            next_page()

    elif st.session_state.page == 11:
        st.subheader("Copying (1 point)")
        st.write("""Instructions: Ask the patient to copy the design shown.
                 Allow multiple tries. Wait until the person is finished and 
                 take it away.""")
        st.caption("All 10 angles must be present and two must intersect")

        st.image("path_to_pentagon_image.jpg", caption="Intersecting Pentagons")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Patient's design copy")
            st.caption("Evaluate accuracy of the copied design")
        with col2:
            design_response = st.radio(
                "Design copy evaluation",
                ["Awaiting Response", "Patient Copied Correctly", "Patient Copied Incorrectly"],
                key="design_response",
                help="Select whether the patient copied the design accurately"
            )

        uploaded_file = st.file_uploader("Upload patient's drawing (optional)",
                                         type=['png', 'jpg', 'jpeg'])
        if uploaded_file:
            st.image(uploaded_file, caption="Patient's drawing")
            st.session_state.responses['drawing'] = uploaded_file

        if design_response == "Awaiting Response":
            st.warning("⚠️ Please evaluate the design copy before completing the assessment")

        if st.button("Complete Assessment", disabled=design_response == "Awaiting Response",key="Page11"):
            if design_response == "Patient Copied Correctly":
                st.session_state.score += 1
            st.session_state.completed_sections.add(11)
            next_page()
    elif st.session_state.page == 12:
        if 'cookie_test' not in st.session_state.completed_sections:
            cookie_test()

    elif st.session_state.page == 13:
        st.subheader("Assessment Complete")
        st.write(f"Patient Name: {st.session_state.responses['patient_name']}")
        st.write(f"Examiner: {st.session_state.responses['examiner_name']}")
        st.write(f"Date: {st.session_state.responses['exam_date']}")
        st.write(f"Final Score: {st.session_state.score}/30")

        # Score interpretation
        if st.session_state.score <= 23:
            st.warning("Score indicates possible cognitive impairment.")
            st.caption("Consider referral for detailed cognitive assessment")
        else:
            st.success("Score is within normal range.")
            st.caption("Continue routine monitoring as appropriate")

        # Level of consciousness assessment
        consciousness = st.select_slider(
            "Level of Consciousness:",
            options=['Alert', 'Drowsy', 'Stupor', 'Coma'],
            help="Select the patient's level of consciousness during the assessment"
        )
        st.session_state.responses['consciousness'] = consciousness

        # Optional notes
        examiner_notes = st.text_area(
            "Additional Notes:",
            "",
            help="Record any additional observations, behaviors, or concerns"
        )
        if examiner_notes:
            st.session_state.responses['examiner_notes'] = examiner_notes

        # Review sections button
        if st.button("Review Previous Sections",key="Review Previous Sections"):
            st.session_state.page = 1
            st.rerun()


def get_location_from_ip():
    # Try multiple geolocation services
    services = [
        'https://ipapi.co/json/',
        'https://ip-api.com/json/',
        'https://freegeoip.app/json/'
    ]

    for service in services:
        try:
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                data = response.json()

                # Handle different API response formats
                if 'city' in data:
                    return {
                        'city': data.get('city', ''),
                        'country': data.get('country_name', data.get('country', '')),
                        'state': data.get('region', data.get('region_name', '')),
                        'latitude': data.get('latitude', data.get('lat', 0)),
                        'longitude': data.get('longitude', data.get('lon', 0))
                    }
        except Exception as e:
            continue

    # Fallback to default location if all services fail
    return {
        'city': 'Unknown',
        'country': 'Unknown',
        'state': 'Unknown',
        'latitude': 0,
        'longitude': 0
    }


def get_local_time(lat, lon):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=lat, lng=lon)
    if timezone_str:
        timezone = pytz.timezone(timezone_str)
        return datetime.now(timezone)
    return datetime.now()


def normalize_score(current_score, max_possible_score, target_score=30):
    return round((current_score / max_possible_score) * target_score)

def render_self_assessment():
    st.write("Patient Information")
    patient_name = st.text_input("Your Name")

    if patient_name:
        st.session_state.responses['patient_name'] = patient_name
        if st.button("Begin Test"):
            next_page()

    if st.session_state.page == 2:  # Orientation - Time
        st.subheader("Orientation - Time")
        location_data = get_location_from_ip()
        if location_data:
            local_time = get_local_time(location_data['latitude'],
                                        location_data['longitude'])
        else:
            local_time = datetime.now()

        col1, col2 = st.columns(2)
        with col1:
            year = st.text_input("What year is it?")
            month = st.selectbox("What month is it?",
                                 ['January', 'February', 'March', 'April',
                                  'May', 'June', 'July', 'August',
                                  'September', 'October', 'November', 'December'])
            date = st.text_input("What date is it? (day of month)")

        with col2:
            season = st.selectbox("What season is it?",
                                  ['Spring', 'Summer', 'Fall', 'Winter'])
            day = st.selectbox("What day of the week is it?",
                               ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                                'Friday', 'Saturday', 'Sunday'])

        if all([year, month, date, season, day]):
            responses = {
                'year': year,
                'month': month,
                'date': date,
                'season': season,
                'day': day
            }
            st.session_state.responses.update(responses)

            if st.button("Next"):
                # Score calculation
                score = 0
                if str(local_time.year) == year:
                    score += 1
                if local_time.strftime('%B') == month:
                    score += 1
                if str(local_time.day) == date:
                    score += 1
                if local_time.strftime('%A') == day:
                    score += 1

                # Season scoring (adjusted as per requirement 3.2)
                seasons = {
                    'winter': [12, 1, 2],
                    'spring': [3, 4, 5],
                    'summer': [6, 7, 8],
                    'fall': [9, 10, 11]
                }
                current_season = next(s for s, months in seasons.items()
                                      if local_time.month in months)
                if current_season.lower() == season.lower():
                    score += 1

                # Adjust score as per requirement 3.2
                season_score = score * (5 / 4)
                st.session_state.score += round(season_score)
                next_page()

    elif st.session_state.page == 3:  # Orientation - Place
        st.subheader("Orientation - Place")
        location_data = get_location_from_ip()

        city_input = st.text_input("What city are you in?")
        country = st.text_input("What country are you")
        province = st.text_input("What province are you in ")

        if all([city_input, country, province]):
            if st.button("Next"):
                score = 0
                # Auto-score city based on GPS if available
                if location_data['city'] != 'Unknown':
                    if city_input.lower() == location_data['city'].lower():
                        score += 1
                else:
                    # If location service failed, give point if they entered anything
                    if city_input.strip():
                        score += 1
                if location_data['country'] != 'Unknown':
                    if country.lower() == location_data['country'].lower():
                        score += 1
                else:
                    # If location service failed, give point if they entered anything
                    if country.strip():
                        score += 1
                if location_data['state'] != 'Unknown':
                    if province.lower().replace("county", "").strip() == location_data['state'].lower().replace("county",
                                                                                                                "").strip():
                        score += 1
                else:
                    # If location service failed, give point if they entered anything
                    if province.strip():
                        score += 1

                # Adjust score as per requirement 3.5
                final_score = round(score * (5 / 3))
                st.session_state.score += final_score
                next_page()

        # Add debug information if needed
        if st.checkbox("Show location debug info"):
            st.write("Detected location information:")
            st.json(location_data)

    elif st.session_state.page == 4:  # Registration
        st.subheader("Registration")
        st.write("Please identify the following images:")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.image("img/apple.jpeg", caption="Image 1")
            response1 = st.text_input("What is this object?", key="response1")

        with col2:
            st.image("img/table.jpeg", caption="Image 2")
            response2 = st.text_input("What is this object?", key="response2")

        with col3:
            st.image("img/kiruce.jpeg", caption="Image 3")
            response3 = st.text_input("What is this object?", key="response3")

        if all([response1, response2, response3]):
            responses = [response1.lower(), response2.lower(), response3.lower()]
            correct = ['apple', 'table', 'coin']

            if st.button("Next"):
                score = sum(1 for resp, corr in zip(responses, correct)
                            if resp == corr)
                st.session_state.score += score
                st.session_state.responses['registration'] = responses
                next_page()

    elif st.session_state.page == 5:  # Attention and Calculation
        st.subheader("Attention and Calculation")
        task_choice = st.radio("Choose a task:",
                               ["Serial 7s", "Spell 'WORLD' backwards"])

        if task_choice == "Serial 7s":
            responses = []
            correct = [93, 86, 79, 72, 65]

            for i in range(5):
                resp = st.number_input(f"100 minus {(i + 1) * 7} equals:",
                                       min_value=0, max_value=100)
                responses.append(resp)

            if st.button("Next"):
                score = sum(1 for resp, corr in zip(responses, correct)
                            if resp == corr)
                st.session_state.score += score
                next_page()

        if task_choice == "Spell 'WORLD' backwards":  # Spell 'WORLD' backwards
            st.write("Please spell 'WORLD' backwards:")
            backwards_spelling = st.text_input("Your answer:")

            if backwards_spelling and st.button("Next"):
                score = sum(1 for a, b in zip(backwards_spelling.upper(), 'DLROW')
                            if a == b)
                st.session_state.score += score
                next_page()

    elif st.session_state.page == 6:  # Recall
        st.subheader("Recall")
        st.write("What were the three objects you identified in the images earlier?")

        recall1 = st.text_input("Object 1")
        recall2 = st.text_input("Object 2")
        recall3 = st.text_input("Object 3")

        if all([recall1, recall2, recall3]):
            responses = sorted([recall1.lower(), recall2.lower(), recall3.lower()])
            correct = sorted(['apple', 'table', 'coin'])

            if st.button("Next"):
                score = sum(1 for resp, corr in zip(responses, correct)
                            if resp == corr)
                st.session_state.score += score
                next_page()

    elif st.session_state.page == 7:  # Language - Naming
        st.subheader("Language - Naming")

        col1, col2 = st.columns(2)
        with col1:
            st.image("img/fejo.jpeg", caption="Object 1")
            pencil = st.text_input("What is this object?", key="pencil")

        with col2:
            st.image("img/s-tier.jpeg", caption="Object 2")
            watch = st.text_input("What is this object?", key="watch")

        if pencil and watch:
            if st.button("Next"):
                score = 0
                if pencil.lower() == "pencil":
                    score += 1
                if watch.lower() == "watch":
                    score += 1
                st.session_state.score += score
                next_page()

    elif st.session_state.page == 8:  # cookie Test
            cookie_test()
    elif st.session_state.page == 9:  # Final Score
        st.subheader("Assessment Complete")

        # Normalize the score to be out of 30
        max_possible_score = 24  # Adjusted for removed questions
        final_score = normalize_score(st.session_state.score, max_possible_score, 30)

        st.write(f"Your Name: {st.session_state.responses['patient_name']}")
        st.write(f"Total Score: {final_score}/30")

        if final_score <= 23:
            st.warning("Score indicates possible cognitive impairment. " +
                       "Please consult with a healthcare professional.")
        else:
            st.success("Score is within normal range.")

def main():
    st.title("Mini-Mental State Examination (MMSE)")
    # Add the render_examiner_section function here

    init_session_state()

    if st.session_state.page == 0:
        st.write("Welcome to the MMSE Assessment")
        exam_type = st.radio("Please select the type of examination:",
                             ["Self Examination", "With Examiner"])

        if st.button("Start Assessment"):
            st.session_state.exam_type = exam_type
            next_page()
    if st.session_state.exam_type == "With Examiner" and st.session_state.page > 0:
        render_examiner_section()
        return

    elif st.session_state.page >0 and st.session_state.exam_type == "Self Examination":
        render_self_assessment()
        return



if __name__ == "__main__":
    main()