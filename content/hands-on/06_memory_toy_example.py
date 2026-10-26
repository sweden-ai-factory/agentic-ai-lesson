"""
06_memory.py

A simple example showing how AI agents can use memory.

Concepts:
- Short-term memory
- Long-term memory
- Storing preferences
- Retrieving preferences
- Personalised recommendations

Run:
    python 06_memory.py
"""

import json
from pathlib import Path

MEMORY_FILE = "memory.json"


class TravelMemory:
    """Simple long-term memory using a JSON file."""

    def __init__(self, file_path=MEMORY_FILE):
        self.file_path = Path(file_path)

        if self.file_path.exists():
            self.load()
        else:
            self.memory = {}

    def load(self):
        with open(self.file_path, "r") as file:
            self.memory = json.load(file)

    def save(self):
        with open(self.file_path, "w") as file:
            json.dump(self.memory, file, indent=4)

    def remember(self, key, value):
        self.memory[key] = value
        self.save()

    def recall(self, key, default=None):
        return self.memory.get(key, default)

    def show_memory(self):
        return self.memory


def setup_preferences(memory):
    """Ask the user for preferences and store them."""

    print("\n=== Save Travel Preferences ===")

    seat = input("Preferred seat (window/aisle): ")

    airline = input("Preferred airline: ")

    diet = input("Diet preference: ")

    memory.remember("seat_preference", seat)
    memory.remember("preferred_airline", airline)
    memory.remember("dietary_preference", diet)

    print("\nPreferences saved.\n")


def plan_trip(memory):
    """Create a personalised travel recommendation."""

    print("\n=== Travel Recommendation ===")

    seat = memory.recall("seat_preference", "window")

    airline = memory.recall("preferred_airline", "Any airline")

    diet = memory.recall("dietary_preference", "No preference")

    print("Planning your trip...\n")

    print(f"Preferred airline : {airline}")
    print(f"Preferred seat    : {seat}")
    print(f"Diet preference   : {diet}")

    print("\nRecommended Flight")
    print("------------------")
    print(f"Airline : {airline}")
    print(f"Seat    : {seat}")

    if diet.lower() == "vegetarian":
        print("Meal    : Vegetarian meal requested")

    elif diet.lower() == "vegan":
        print("Meal    : Vegan meal requested")

    else:
        print("Meal    : Standard meal")


def show_saved_memory(memory):
    """Display what the agent remembers."""

    print("\n=== Agent Memory ===")

    for key, value in memory.show_memory().items():
        print(f"{key}: {value}")


def main():

    memory = TravelMemory()

    print("\nTravel Agent Memory Demo")
    print("------------------------")

    while True:
        print("\nChoose an option:")
        print("1. Save preferences")
        print("2. Plan trip")
        print("3. Show memory")
        print("4. Exit")

        choice = input("\nSelection: ")

        if choice == "1":
            setup_preferences(memory)

        elif choice == "2":
            plan_trip(memory)

        elif choice == "3":
            show_saved_memory(memory)

        elif choice == "4":
            print("\nGoodbye!")
            break

        else:
            print("\nInvalid choice.")


if __name__ == "__main__":
    main()
