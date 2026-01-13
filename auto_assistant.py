"""
Auto Dealership Multi-Agent Voice Assistant
A simple Streamlit app for test drive booking with STT/TTS capabilities
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import streamlit as st

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
        {
            "model": "City",
            "brand": "Honda",
            "price": 24000,
            "features": ["LED Headlamps", "Cruise Control", "Wireless CarPlay"],
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
        {
            "model": "XUV700",
            "brand": "Mahindra",
            "price": 37000,
            "features": ["ADAS", "Panoramic Sunroof", "Premium Sound"],
        },
        {
            "model": "XUV300",
            "brand": "Mahindra",
            "price": 29000,
            "features": ["7 Airbags", "Dual-Zone AC", "Wireless Charging"],
        },
        {
            "model": "Seltos",
            "brand": "Kia",
            "price": 31000,
            "features": ["Turbo Option", "Ventilated Seats", "360 Camera"],
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
        {
            "model": "Gladiator",
            "brand": "Jeep",
            "price": 46000,
            "features": ["Trail Rated 4x4", "Removable Top", "Rubicon Package"],
        },
    ],
    "hatchback": [
        {
            "model": "Swift",
            "brand": "Maruti",
            "price": 18000,
            "features": ["Dual-Tone Roof", "SmartPlay Studio", "LED DRLs"],
        },
        {
            "model": "Baleno",
            "brand": "Maruti",
            "price": 19500,
            "features": ["HUD Display", "360 Camera", "Connected Car Tech"],
        },
        {
            "model": "i20",
            "brand": "Hyundai",
            "price": 20500,
            "features": ["Sunroof", "Bose Audio", "6 Airbags"],
        },
    ],
}

BOOKINGS_DB: List[Dict] = []

# ============================================================================
# AGENT CLASSES
# ============================================================================


class KnowledgeAgent:
    """Handles queries about car inventory and features."""

    def __init__(self):
        self.all_cars: List[Dict] = []
        for car_type, car_list in CARS_DB.items():
            for car in car_list:
                car_with_type = dict(car)
                car_with_type["type"] = car_type
                self.all_cars.append(car_with_type)

    def search_cars(self, car_type: str = None, model: str = None, brand: str = None) -> List[Dict]:
        """Search for cars by type, model, or brand."""
        results = []

        if car_type and car_type.lower() in CARS_DB:
            results = CARS_DB[car_type.lower()]
        elif model:
            for car in self.all_cars:
                if model.lower() in car["model"].lower():
                    results.append(car)
        elif brand:
            for car in self.all_cars:
                if brand.lower() in car["brand"].lower():
                    results.append(car)
        else:
            results = list(self.all_cars)

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
            cheapest = min(self.all_cars, key=lambda x: x["price"])
            return (
                f"Our most affordable option is the {cheapest['brand']} "
                f"{cheapest['model']} at ${cheapest['price']:,}."
            )

        if "suv" in question_lower:
            suvs = CARS_DB.get("suv", [])
            suv_names = [f"{car['brand']} {car['model']}" for car in suvs]
            return f"We have {len(suvs)} SUVs: {', '.join(suv_names)}."

        # Budget-based suggestion
        price_matches = re.findall(r"\d{2,6}", question_lower)
        if price_matches and any(word in question_lower for word in ["under", "below", "budget", "less"]):
            budget = int(price_matches[0])
            options = [car for car in self.all_cars if car["price"] <= budget]
            if options:
                top_options = ", ".join(
                    f"{car['brand']} {car['model']} (${car['price']:,})" for car in options[:4]
                )
                return f"Here are options under ${budget:,}: {top_options}."
            return f"We currently don't have models under ${budget:,}, but I can show you the closest matches."

        # Model-specific details
        for car in self.all_cars:
            if car["model"].lower() in question_lower:
                key_features = ", ".join(car["features"][:3])
                return (
                    f"{car['brand']} {car['model']} ({car['type'].title()}): "
                    f"${car['price']:,} with features like {key_features}."
                )

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
            "stage": "greeting",  # greeting, car_selection, booking, confirmation
            "car_type": None,
            "car_model": None,
            "brand": None,
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
            return self.process_input(user_input)  # Re-process as car selection

        # Stage: Car Selection
        if self.state["stage"] == "car_selection":
            # Check for car type
            if "sedan" in user_lower:
                self.state["car_type"] = "sedan"
            elif "suv" in user_lower:
                self.state["car_type"] = "suv"
            elif "truck" in user_lower:
                self.state["car_type"] = "truck"
            elif "hatchback" in user_lower:
                self.state["car_type"] = "hatchback"

            # Check for specific model
            for car_list in CARS_DB.values():
                for car in car_list:
                    if car["model"].lower() in user_lower:
                        self.state["car_model"] = car["model"]
                        self.state["car_type"] = [k for k, v in CARS_DB.items() if car in v][0]

            # Detect brand interest
            brand_keywords = {"maruti", "mahindra", "honda", "toyota", "ford", "chevrolet", "kia", "hyundai", "jeep"}
            for brand in brand_keywords:
                if brand in user_lower:
                    self.state["brand"] = brand
                    break

            # If we have car type or model, show options
            if self.state["car_type"] or self.state["brand"]:
                cars = self.knowledge_agent.search_cars(
                    car_type=self.state["car_type"], brand=self.state["brand"]
                )
                label = (
                    f"{self.state['car_type']}s"
                    if self.state["car_type"]
                    else f"{self.state['brand'].title()} models"
                )
                response = f"Great! Here are our {label}:\n\n"
                for car in cars:
                    response += f"- {car['brand']} {car['model']} - ${car['price']:,}\n"
                    response += f"  Features: {', '.join(car['features'][:2])}\n\n"

                if self.state["car_model"]:
                    self.state["stage"] = "booking"
                    response += f"\nWould you like to book a test drive for the {self.state['car_model']}?"
                else:
                    response += "Which model would you like to test drive?"
                return response

            # Answer general questions
            if "?" in user_input:
                return self.knowledge_agent.answer_question(user_input)

            return "I'd be happy to help! What type of car interests you - sedan, SUV, or truck?"

        # Stage: Booking
        if self.state["stage"] == "booking":
            # Check if selecting a model
            if not self.state["car_model"]:
                for car_list in CARS_DB.values():
                    for car in car_list:
                        if car["model"].lower() in user_lower:
                            self.state["car_model"] = car["model"]
                            return (
                                f"Excellent choice! The {self.state['car_model']} is a great vehicle. What's your name?"
                            )
                return "Please tell me which model you'd like to test drive."

            # Collect customer name
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

            # Collect date
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
                            self.state["date"] = "2026-01-15"  # Default
                    except Exception:
                        self.state["date"] = "2026-01-15"

                available_slots = self.booking_agent.get_available_slots(self.state["date"])
                return (
                    f"Great! For {self.state['date']}, we have these times available: "
                    f"{', '.join(available_slots[:4])}. What time works best?"
                )

            # Collect time
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
                    "Booking Details:\n"
                    f"- Name: {booking['customer_name']}\n"
                    f"- Vehicle: {booking['car_model']}\n"
                    f"- Date: {booking['date']}\n"
                    f"- Time: {booking['time']}\n"
                    f"- Confirmation ID: #{booking['id']}\n\n"
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
                "brand": None,
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
    st.set_page_config(page_title="Auto Dealership Voice Assistant", page_icon=":car:")

    st.title("Auto Dealership Voice Assistant")
    st.markdown("*Multi-Agent System for Test Drive Booking*")

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

    # Sidebar
    with st.sidebar:
        st.header("System Info")
        st.write(f"**Current Stage:** {st.session_state.conversation_agent.state['stage'].title()}")

        if st.session_state.conversation_agent.state["car_type"]:
            st.write(f"**Selected Type:** {st.session_state.conversation_agent.state['car_type'].title()}")
        if st.session_state.conversation_agent.state["brand"]:
            st.write(f"**Preferred Brand:** {st.session_state.conversation_agent.state['brand'].title()}")
        if st.session_state.conversation_agent.state["car_model"]:
            st.write(f"**Selected Model:** {st.session_state.conversation_agent.state['car_model']}")

        st.markdown("---")
        st.header("Bookings")
        if BOOKINGS_DB:
            for booking in BOOKINGS_DB:
                st.write(f"#{booking['id']}: {booking['customer_name']} - {booking['car_model']}")
                st.caption(f"{booking['date']} at {booking['time']}")
        else:
            st.write("No bookings yet")

        st.markdown("---")
        if st.button("Reset Conversation"):
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

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if user_input := st.chat_input("Type your message here..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        response = st.session_state.conversation_agent.process_input(user_input)

        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

        st.rerun()

    # Instructions
    with st.expander("How to Use"):
        st.markdown(
            """
        **Simple Conversation Flow:**
        1. Start by greeting or directly mention car type (sedan/SUV/truck)
        2. Choose a specific model from the options shown
        3. Provide your name when asked
        4. Select a date (e.g., "tomorrow" or "Jan 15")
        5. Choose a time (e.g., "10:00 AM")
        6. Get your booking confirmation!

        **Example Messages:**
        - "I'm interested in an SUV"
        - "Tell me about the Civic"
        - "I want to test drive the RAV4"
        - "Tomorrow at 2 PM works for me"
        """
        )


if __name__ == "__main__":
    main()
