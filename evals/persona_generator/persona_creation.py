import json
import random
import sys
import uuid
from pathlib import Path

import yaml

# -----------------------------
# Utility Functions
# -----------------------------


def weighted_choice(values, probabilities):
    return random.choices(values, weights=probabilities, k=1)[0]


def generate_name(nationality):
    first_names = {
        "American": ["John", "Emily", "Michael", "Sophia"],
        "Indian": ["Arjun", "Priya", "Rahul", "Ananya"],
        "British": ["Oliver", "Amelia", "Harry", "Isla"],
        "Australian": ["Liam", "Charlotte", "Noah", "Mia"],
        "Canadian": ["Ethan", "Ava", "Lucas", "Chloe"],
    }

    last_names = {
        "American": ["Smith", "Johnson"],
        "Indian": ["Sharma", "Reddy"],
        "British": ["Brown", "Taylor"],
        "Australian": ["Wilson", "Martin"],
        "Canadian": ["Anderson", "Thomas"],
    }

    first = random.choice(first_names[nationality])
    last = random.choice(last_names[nationality])
    return f"{first} {last}"


def generate_email(name):
    number = random.randint(10, 9999)
    email = name.lower().replace(" ", ".")
    return f"{email}{number}@gmail.com"


# -----------------------------
# Persona Generator
# -----------------------------


class PersonaGenerator:
    def __init__(self, config_path):
        with open(config_path) as file:
            self.config = yaml.safe_load(file)["persona_config"]

        self.segments = self.config["segments"]

        self.industry_intent_map = {
            "Travel": ["Flight_Booking", "Hotel_Booking"],
            "Banking_Finance": ["Loan_Requirement", "New_Bank_Account_Creation"],
            "Ecommerce": ["Product_Return_Request", "Order_Tracking"],
            "Telecommunications": ["New_SIM_Activation", "Plan_Upgrade_Request"],
        }

    def sample_attribute(self, segment, attribute):
        values = self.segments[segment][attribute]["values"]
        distribution = self.segments[segment][attribute]["distribution"]
        return weighted_choice(values, distribution)

    def get_industry_for_intent(self, intent_name):
        for industry, intents in self.industry_intent_map.items():
            if intent_name in intents:
                return industry
        return None

    def generate_persona(self, intent_name):
        industry = self.get_industry_for_intent(intent_name)
        if not industry:
            raise ValueError(f"Intent '{intent_name}' not found in configuration.")

        nationality = self.sample_attribute("demographics", "nationality")
        gender = self.sample_attribute("demographics", "gender")

        name = generate_name(nationality)
        email = generate_email(name)

        persona = {
            "persona_id": str(uuid.uuid4()),
            "primary_intent": intent_name,
            "industry": industry,
            "demographics": {
                "name": name,
                "email": email,
                "nationality": nationality,
                "gender": gender,
                "age_group": self.sample_attribute("demographics", "age_group"),
                "marital_status": self.sample_attribute(
                    "demographics",
                    "marital_status",
                ),
                "employment_status": self.sample_attribute(
                    "demographics",
                    "employment_status",
                ),
                "income_level": self.sample_attribute("demographics", "income_level"),
            },
            "identity": {
                "education_level": self.sample_attribute("identity", "education_level"),
            },
            "language_style": {
                "slang_style": self.sample_attribute("language_style", "slang_style"),
                "politeness_level": self.sample_attribute(
                    "language_style",
                    "politeness_level",
                ),
                "verbosity": self.sample_attribute("language_style", "verbosity"),
                "punctuation_style": self.sample_attribute(
                    "language_style",
                    "punctuation_style",
                ),
                "emotional_tone": self.sample_attribute(
                    "language_style",
                    "emotional_tone",
                ),
            },
            "personality_traits": {
                "decision_style": self.sample_attribute(
                    "personality_traits",
                    "decision_style",
                ),
                "tech_savviness": self.sample_attribute(
                    "personality_traits",
                    "tech_savviness",
                ),
                "trust_level": self.sample_attribute(
                    "personality_traits",
                    "trust_level",
                ),
                "patience_level": self.sample_attribute(
                    "personality_traits",
                    "patience_level",
                ),
            },
            "behavioral_patterns": {
                "response_speed_expectation": self.sample_attribute(
                    "behavioral_patterns",
                    "response_speed_expectation",
                ),
                "clarification_tendency": self.sample_attribute(
                    "behavioral_patterns",
                    "clarification_tendency",
                ),
                "price_sensitivity": self.sample_attribute(
                    "behavioral_patterns",
                    "price_sensitivity",
                ),
                "error_reaction": self.sample_attribute(
                    "behavioral_patterns",
                    "error_reaction",
                ),
            },
            "conversation_behavior": {
                "greeting_style": self.sample_attribute(
                    "conversation_behavior",
                    "greeting_style",
                ),
                "information_provided_initially": self.sample_attribute(
                    "conversation_behavior",
                    "information_provided_initially",
                ),
            },
        }

        return persona


# -----------------------------
# Main Execution
# -----------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python persona_generator.py <Intent_Name> [number_of_personas]")
        sys.exit(1)

    intent_name = sys.argv[1]
    personas_per_intent = int(sys.argv[2]) if len(sys.argv) > 2 else 2

    generator = PersonaGenerator("evals/config/persona_config.yaml")

    personas = []
    for _ in range(personas_per_intent):
        personas.append(generator.generate_persona(intent_name))

    output_dir = Path("evals/config/personas")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"persona_{intent_name.lower()}.json"

    with open(output_file, "w") as f:
        json.dump(personas, f, indent=2)

    print(
        f"Generated {len(personas)} personas for intent '{intent_name}' in {output_file}",
    )
