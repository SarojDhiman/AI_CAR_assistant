# AI_CAR_assistant
This project implements a multi-agent auto dealership assistant for test drive booking. A conversation agent manages dialogue and intent, a knowledge agent retrieves car details from a structured database, and a booking agent schedules test drives using a simulated calendar.
Auto Dealership Multi-Agent Voice Assistant

This project is a multi-agent AI assistant that simulates a real auto dealership phone experience for booking test drives. The assistant can understand customer intent, provide car details, and schedule a test drive through a collaborative agent architecture.

Features

Multi-agent architecture (Conversation, Knowledge, Booking agents)

Intelligent dialogue flow with multi-turn memory

Car knowledge base with models, pricing, and features

Simulated test drive booking with availability checks

Streamlit-based interactive UI

Extendable to voice using STT/TTS (Whisper / Speech APIs)

Architecture Overview

Conversation Agent: Manages dialogue and delegates tasks

Knowledge Agent: Fetches car details from structured data

Booking Agent: Handles scheduling and confirmation logic

Tech Stack

Python

Streamlit

Agent-based architecture (rule-driven)

Optional STT/TTS integration

How to Run
pip install streamlit
streamlit run auto_assistant.py

Example Flow

User: “I want to book a test drive for an SUV tomorrow”
Assistant: Shows available SUVs → confirms model → schedules test drive → confirms booking

Notes

This project demonstrates agentic collaboration, context management, and real-world AI workflow design suitable for production-style assistants.
