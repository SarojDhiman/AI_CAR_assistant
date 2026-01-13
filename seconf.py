"""
Auto Dealership Multi-Agent Voice Assistant
A simple Streamlit app for test drive booking with STT/TTS capabilities
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import streamlit as st
from streamlit_mic_recorder import mic_recorder
import io
import tempfile
import os

# Try to import speech recognition, provide fallback if not available
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    st.warning("⚠️ speech_recognition not installed. Install with: pip install SpeechRecognition pyaudio")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# ============================================================================
# KNOWLEDGE BASE
# ============================================================================

CARS_DB: Dict[str, List[Dict]] = {
    "sedan": [
        {
            "model": "Civic",
            "brand": "Honda",
            "price": 25000,
            "features": ["Cruise Control", "Backup Camera", "Apple CarPlay"],
        },
        {
            "model": "Camry",
            "brand": "Toyota",
            "price": 28000,
            "features": ["Lane Assist", "Adaptive Cruise", "Premium Audio"],
        },
        {
            "model": "Accord",
            "brand": "Honda",
            "price": 30000,
            "features": ["Leather Seats", "Sunroof", "Navigation"],
        },
    ],
    "suv": [
        {
            "model": "CR-V",
            "brand": "Honda",
            "price": 32000,
            "features": ["AWD", "Panoramic Roof", "7 Seats"],
        },
        {
            "model": "RAV4",
            "brand": "Toyota",
            "price": 35000,
            "features": ["Hybrid Option", "Safety Sense", "Power Liftgate"],
        },
        {
            "model": "Pilot",
            "brand": "Honda",
            "price": 40000,
            "features": ["8 Seats", "4WD", "Premium Interior"],
        },
    ],
    "truck": [
        {
            "model": "F-150",
            "brand": "Ford",
            "price": 45000,
            "features": ["Towing Package", "Off-Road", "Large Bed"],
        },
        {
            "model": "Silverado",
            "brand": "Chevrolet",
            "price": 43000,
            "features": ["V8 Engine", "4WD", "Crew Cab"],
        },
    ],
}

BOOKINGS_DB: List[Dict] = []

# ============================================================================
# SPEECH UTILITIES
# ============================================================================

def audio_to_text(audio_bytes):
    """Convert audio bytes to text using speech recognition."""
    if not SPEECH_AVAILABLE:
        return None
    
    try:
        recognizer = sr.Recognizer()
        
        # Save audio bytes to temporary WAV file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
        
        # Read audio file
        with sr.AudioFile(tmp_file_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        return text
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand the audio."
    except sr.RequestError as e:
        return f"Speech recognition error: {e}"
    except Exception as e:
        return f"Error processing audio: {e}"

def text_to_speech(text):
    """Convert text to speech (optional feature)."""
    if not TTS_AVAILABLE:
        return
    
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        st.error(f"TTS Error: {e}")

# ============================================================================
# AGENT CLASSES
# ============================================================================

class KnowledgeAgent:
    """Handles queries about car inventory and features."""

    def search_cars(self, car_type: str = None, model: str = None) -> List[Dict]:
        """Search for cars by type or model."""
        results = []

        if car_type and car_type.lower() in CARS_DB:
            results = CARS_DB[car_type.lower()]
        elif model:
            for car_list in CARS_DB.values():
                for car in car_list:
                    if model.lower() in car["model"].lower():
                        results.append(car)
        else:
            for car_list in CARS_DB.values():
                results.extend(car_list)

        return results

    def get_car_details(self, model: str) -> Optional[Dict]:
        """Get details of a specific car model."""
        for car_list in CARS_DB.values():
            for car in car_list:
                if model.lower() in car["model"].lower():
                    return car
        return None

    def answer_question(self, question: str) -> str:
        """Answer general questions about inventory."""
        question_lower = question.lower()

        if "how many" in question_lower or "what cars" in question_lower:
            total = sum(len(cars) for cars in CARS_DB.values())
            types = ", ".join(CARS_DB.keys())
            return f"We have {total} models available across {types}."

        if "cheapest" in question_lower or "affordable" in question_lower:
            all_cars: List[Dict] = []
            for car_list in CARS_DB.values():
                all_cars.extend(car_list)
            cheapest = min(all_cars, key=lambda x: x["price"])
            return (
                f"Our most affordable option is the {cheapest['brand']} "
                f"{cheapest['model']} at ${cheapest['price']:,}."
            )

        if "suv" in question_lower:
            suvs = CARS_DB.get("suv", [])
            suv_names = [f"{car['brand']} {car['model']}" for car in suvs]
            return f"We have {len(suvs)} SUVs: {', '.join(suv_names)}."

        return "I can help you find information about our cars. What would you like to know?"


class BookingAgent:
    """Handles test drive scheduling."""

    def check_availability(self, date: str, time: str) -> bool:
        """Check if a time slot is available."""
        for booking in BOOKINGS_DB:
            if booking["date"] == date and booking["time"] == time:
                return False
        return True

    def create_booking(self, customer_name: str, car_model: str, date: str, time: str) -> Dict:
        """Create a new test drive booking."""
        booking = {
            "id": len(BOOKINGS_DB) + 1,
            "customer_name": customer_name,
            "car_model": car_model,
            "date": date,
            "time": time,
            "status": "confirmed",
        }
        BOOKINGS_DB.append(booking)
        return booking

    def get_available_slots(self, date: str) -> List[str]:
        """Get available time slots for a date."""
        all_slots = ["9:00 AM", "10:00 AM", "11:00 AM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM"]
        booked_slots = [b["time"] for b in BOOKINGS_DB if b["date"] == date]
        return [slot for slot in all_slots if slot not in booked_slots]


class ConversationAgent:
    """Orchestrates the conversation and delegates to other agents."""

    def __init__(self):
        self.knowledge_agent = KnowledgeAgent()
        self.booking_agent = BookingAgent()
        self.state = {
            "stage": "greeting",
            "car_type": None,
            "car_model": None,
            "date": None,
            "time": None,
            "customer_name": None,
        }

    def process_input(self, user_input: str) -> str:
        """Main logic to process user input and generate response."""
        user_lower = user_input.lower()

        # Stage: Greeting
        if self.state["stage"] == "greeting":
            if any(word in user_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
                self.state["stage"] = "car_selection"
                return (
                    "Hello! Welcome to our dealership. I can help you book a test drive. "
                    "What type of car are you interested in? We have sedans, SUVs, and trucks."
                )
            self.state["stage"] = "car_selection"
            return self.process_input(user_input)

        # Stage: Car Selection
        if self.state["stage"] == "car_selection":
            if "sedan" in user_lower:
                self.state["car_type"] = "sedan"
            elif "suv" in user_lower:
                self.state["car_type"] = "suv"
            elif "truck" in user_lower:
                self.state["car_type"] = "truck"

            for car_list in CARS_DB.values():
                for car in car_list:
                    if car["model"].lower() in user_lower:
                        self.state["car_model"] = car["model"]
                        self.state["car_type"] = [k for k, v in CARS_DB.items() if car in v][0]

            if self.state["car_type"]:
                cars = self.knowledge_agent.search_cars(car_type=self.state["car_type"])
                response = f"Great! Here are our {self.state['car_type']}s:\n\n"
                for car in cars:
                    response += f"• {car['brand']} {car['model']} - ${car['price']:,}\n"
                    response += f"  Features: {', '.join(car['features'][:2])}\n\n"

                if self.state["car_model"]:
                    self.state["stage"] = "booking"
                    response += f"\nWould you like to book a test drive for the {self.state['car_model']}?"
                else:
                    response += "Which model would you like to test drive?"
                return response

            if "?" in user_input:
                return self.knowledge_agent.answer_question(user_input)

            return "I'd be happy to help! What type of car interests you - sedan, SUV, or truck?"

        # Stage: Booking
        if self.state["stage"] == "booking":
            if not self.state["car_model"]:
                for car_list in CARS_DB.values():
                    for car in car_list:
                        if car["model"].lower() in user_lower:
                            self.state["car_model"] = car["model"]
                            return (
                                f"Excellent choice! The {self.state['car_model']} is a great vehicle. What's your name?"
                            )
                return "Please tell me which model you'd like to test drive."

            if not self.state["customer_name"]:
                if any(word in user_lower for word in ["my name is", "i'm", "i am", "this is"]):
                    name_words = user_input.split()
                    self.state["customer_name"] = name_words[-1].capitalize()
                else:
                    self.state["customer_name"] = user_input.strip().title()
                return (
                    f"Nice to meet you, {self.state['customer_name']}! "
                    "What date works for you? (e.g., tomorrow, or a specific date like Jan 15)"
                )

            if not self.state["date"]:
                if "tomorrow" in user_lower:
                    tomorrow = datetime.now() + timedelta(days=1)
                    self.state["date"] = tomorrow.strftime("%Y-%m-%d")
                elif "today" in user_lower:
                    self.state["date"] = datetime.now().strftime("%Y-%m-%d")
                else:
                    try:
                        date_match = re.search(r"(\w+)\s+(\d+)", user_input)
                        if date_match:
                            self.state["date"] = f"2026-01-{date_match.group(2).zfill(2)}"
                        else:
                            self.state["date"] = "2026-01-15"
                    except Exception:
                        self.state["date"] = "2026-01-15"

                available_slots = self.booking_agent.get_available_slots(self.state["date"])
                return (
                    f"Great! For {self.state['date']}, we have these times available: "
                    f"{', '.join(available_slots[:4])}. What time works best?"
                )

            if not self.state["time"]:
                time_patterns = [r"\d+:\d+\s*(?:AM|PM)", r"\d+\s*(?:AM|PM)"]
                for pattern in time_patterns:
                    match = re.search(pattern, user_input, re.IGNORECASE)
                    if match:
                        self.state["time"] = match.group(0).upper()
                        break

                if not self.state["time"]:
                    available_slots = self.booking_agent.get_available_slots(self.state["date"])
                    self.state["time"] = available_slots[0] if available_slots else "10:00 AM"

                booking = self.booking_agent.create_booking(
                    self.state["customer_name"],
                    self.state["car_model"],
                    self.state["date"],
                    self.state["time"],
                )

                self.state["stage"] = "confirmation"
                return (
                    "Perfect! Your test drive is confirmed!\n\n"
                    "📋 Booking Details:\n"
                    f"• Name: {booking['customer_name']}\n"
                    f"• Vehicle: {booking['car_model']}\n"
                    f"• Date: {booking['date']}\n"
                    f"• Time: {booking['time']}\n"
                    f"• Confirmation ID: #{booking['id']}\n\n"
                    "We'll see you then! Is there anything else I can help you with?"
                )

        # Stage: Confirmation
        if self.state["stage"] == "confirmation":
            if any(word in user_lower for word in ["no", "nothing", "that's all", "thank"]):
                return "Thank you for choosing our dealership! Have a great day!"
            self.state = {
                "stage": "car_selection",
                "car_type": None,
                "car_model": None,
                "date": None,
                "time": None,
                "customer_name": None,
            }
            return self.process_input(user_input)

        return "I'm here to help! Let's start - what type of car are you interested in?"


# ============================================================================
# STREAMLIT UI
# ============================================================================

def main():
    st.set_page_config(
        page_title="Auto Dealership Voice Assistant", 
        page_icon="🚗",
        layout="wide"
    )

    st.title("🚗 Auto Dealership Voice Assistant")
    st.markdown("*Multi-Agent System with Voice & Text Input*")

    # Initialize session state
    if "conversation_agent" not in st.session_state:
        st.session_state.conversation_agent = ConversationAgent()
        st.session_state.messages = []
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "Hello! Welcome to our dealership. I can help you book a test drive. "
                "What type of car are you interested in?",
            }
        )
    
    if "input_mode" not in st.session_state:
        st.session_state.input_mode = "text"
    
    if "enable_tts" not in st.session_state:
        st.session_state.enable_tts = False

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Input mode selector
        st.subheader("Input Mode")
        input_mode = st.radio(
            "Choose your input method:",
            ["💬 Text Input", "🎤 Voice Input"],
            index=0 if st.session_state.input_mode == "text" else 1,
            label_visibility="collapsed"
        )
        st.session_state.input_mode = "text" if "Text" in input_mode else "voice"
        
        # TTS toggle
        if TTS_AVAILABLE:
            st.session_state.enable_tts = st.checkbox("🔊 Enable Text-to-Speech", value=st.session_state.enable_tts)
        
        st.markdown("---")
        
        st.header("📊 System Info")
        st.write(f"**Current Stage:** {st.session_state.conversation_agent.state['stage'].title()}")

        if st.session_state.conversation_agent.state["car_type"]:
            st.write(f"**Selected Type:** {st.session_state.conversation_agent.state['car_type'].title()}")
        if st.session_state.conversation_agent.state["car_model"]:
            st.write(f"**Selected Model:** {st.session_state.conversation_agent.state['car_model']}")

        st.markdown("---")
        
        st.header("🗓️ Bookings")
        if BOOKINGS_DB:
            for booking in BOOKINGS_DB:
                with st.container():
                    st.write(f"**#{booking['id']}** {booking['customer_name']}")
                    st.caption(f"{booking['car_model']}")
                    st.caption(f"📅 {booking['date']} at {booking['time']}")
                    st.markdown("---")
        else:
            st.info("No bookings yet")

        st.markdown("---")
        
        if st.button("🔄 Reset Conversation", use_container_width=True):
            st.session_state.conversation_agent = ConversationAgent()
            st.session_state.messages = []
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": "Hello! Welcome to our dealership. I can help you book a test drive. "
                    "What type of car are you interested in?",
                }
            )
            st.rerun()

    # Main chat area
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input area
    st.markdown("---")
    
    if st.session_state.input_mode == "voice":
        st.info("🎤 **Voice Input Mode**: Click the microphone button below and speak your message")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            audio_data = mic_recorder(
                start_prompt="🎤 Start Recording",
                stop_prompt="⏹️ Stop Recording",
                just_once=True,
                use_container_width=True,
                key="voice_input"
            )
        
        if audio_data:
            st.success("✅ Audio received! Processing...")
            
            # Convert audio to text
            audio_bytes = audio_data['bytes']
            user_text = audio_to_text(audio_bytes)
            
            if user_text and not user_text.startswith("Sorry") and not user_text.startswith("Error"):
                st.info(f"📝 You said: {user_text}")
                
                # Add user message
                st.session_state.messages.append({"role": "user", "content": user_text})
                
                # Process with conversation agent
                response = st.session_state.conversation_agent.process_input(user_text)
                
                # Add assistant response
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Text-to-speech if enabled
                if st.session_state.enable_tts and TTS_AVAILABLE:
                    text_to_speech(response)
                
                st.rerun()
            else:
                st.error(user_text if user_text else "Could not process audio")
    
    else:
        # Text input mode
        if user_input := st.chat_input("💬 Type your message here..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Process with conversation agent
            response = st.session_state.conversation_agent.process_input(user_input)
            
            # Add assistant response
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Text-to-speech if enabled
            if st.session_state.enable_tts and TTS_AVAILABLE:
                text_to_speech(response)
            
            st.rerun()

    # Instructions
    with st.expander("ℹ️ How to Use"):
        st.markdown(
            """
        ### 🎯 Quick Start Guide
        
        **Choose Your Input Method:**
        - **Text Input**: Type your messages in the chat box
        - **Voice Input**: Click the microphone and speak your message
        
        **Conversation Flow:**
        1. Start by greeting or mention car type (sedan/SUV/truck)
        2. Choose a specific model from the options shown
        3. Provide your name when asked
        4. Select a date (e.g., "tomorrow" or "Jan 15")
        5. Choose a time (e.g., "10:00 AM")
        6. Get your booking confirmation!
        
        **Example Voice Commands:**
        - "I'm interested in an SUV"
        - "Show me sedans"
        - "I want to test drive the Civic"
        - "My name is John"
        - "Tomorrow at 2 PM"
        
        **Tips:**
        - Speak clearly when using voice input
        - Enable Text-to-Speech in settings for voice responses
        - Use the Reset button to start a new conversation
        """
        )
    
    # Installation instructions
    if not SPEECH_AVAILABLE:
        with st.expander("⚠️ Voice Input Setup Required"):
            st.markdown(
                """
            ### Install Required Packages
            
            To use voice input, install these packages:
            
            ```bash
            pip install SpeechRecognition
            pip install PyAudio
            pip install streamlit-mic-recorder
            ```
            
            **For PyAudio issues on Windows:**
            ```bash
            pip install pipwin
            pipwin install pyaudio
            ```
            
            **For PyAudio issues on Mac:**
            ```bash
            brew install portaudio
            pip install pyaudio
            ```
            
            **For PyAudio issues on Linux:**
            ```bash
            sudo apt-get install portaudio19-dev python3-pyaudio
            pip install pyaudio
            ```
            """
            )


if __name__ == "__main__":
    main()