"""
Generate instances for the Guess What game.

Creates files in ./instances
"""
""" import random
import json
from tqdm import tqdm
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))
import clemgame
from clemgame.clemgame import GameInstanceGenerator
 """
import os
import sys
from pathlib import Path

print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path}")

# Adjust the path to include the project root directory
sys.path.append(str(Path(__file__).resolve().parents[2]))

import random
import json
from tqdm import tqdm
import yaml
import clemgame
from clemgame.clemgame import GameInstanceGenerator


N_INSTANCES = 3 # how many different instances
N_GUESSES = 10  # how many tries the guesser will have


logger = clemgame.get_logger(__name__)
GAME_NAME = "guesswhat"


class GuessWhatGameInstanceGenerator(GameInstanceGenerator):
    def __init__(self):
        super().__init__(GAME_NAME)
        # Load the category JSON file
        category_file_path = os.path.join(os.path.dirname(__file__), "utils", "categories_subcategories.json")
        with open(category_file_path, 'r') as f:
            self.categories = json.load(f)["Categories"]

    def load_instances(self):
        return self.load_json("in/instances")

    def on_generate(self):
        output_instances = {
            "experiments": []
        }
        output_instance_details = {"Level 1": [], "Level 2": [], "Level 3": []}

        for level in range(1, 4):
            experiment_name = f"level_{level}"
            experiment = self.add_experiment(experiment_name)
            experiment["max_turns"] = N_GUESSES

            answerer_prompt = self.load_template("resources/initial_prompts/answerer_prompt")
            guesser_prompt = self.load_template("resources/initial_prompts/guesser_prompt")
            experiment["answerer_initial_prompt"] = answerer_prompt
            experiment["guesser_initial_prompt"] = guesser_prompt

            used_words = set()
            game_instances = []
            for game_id in tqdm(range(N_INSTANCES)):
                instance, instance_details = self.generate_instance(level, used_words)
                if instance:
                    game_instance = self.add_game_instance(experiment, game_id)
                    game_instance["target_word"] = instance["target"]
                    game_instance["candidate_list"] = instance["items"]
                    game_instances.append(game_instance)
                    output_instance_details[f"Level {level}"].append(instance_details)

            experiment["game_instances"] = game_instances
            output_instances["experiments"].append(experiment)

        # Save instances to the appropriate files
        os.makedirs("in", exist_ok=True)
        # self.save_json(output_instances, "in/instances.json")
        self.save_json(output_instance_details, "in/instances_details.json")

    def generate_instance(self, level, used_words):
        instance = {"items": [], "target": ""}
        instance_details = {"items": [], "target": ""}
        used_categories = set()
        used_features = set()

        while len(instance["items"]) < 8:
            category = random.choice([c for c in self.categories if c["Category"] not in used_categories])
            used_categories.add(category["Category"])
            subcategories = [sub for sub in category["Subcategories"] if sub["Subcategory"] not in used_features]

            if level == 1 and len(subcategories) >= 2:
                selected_subcategories = random.sample(subcategories, 2)
                for sub in selected_subcategories:
                    used_features.add(sub["Subcategory"])
                    available_words = [w for w in sub["Members"] if w not in used_words]
                    if len(available_words) < 2:
                        continue
                    words = random.sample(available_words, 2)
                    for word in words:
                        used_words.add(word)
                        instance["items"].append(word)
                        instance_details["items"].append({
                            "word": word,
                            "category": category["Category"],
                            "feature": sub["Subcategory"]
                        })

            elif level == 2:
                valid_subcategories = [sub for sub in subcategories if len(sub["Members"]) >= 4]
                if valid_subcategories:
                    sub = random.choice(valid_subcategories)
                    used_features.add(sub["Subcategory"])
                    available_words = [w for w in sub["Members"] if w not in used_words]
                    if len(available_words) < 4:
                        continue
                    words = random.sample(available_words, 4)
                    for word in words:
                        used_words.add(word)
                        instance["items"].append(word)
                        instance_details["items"].append({
                            "word": word,
                            "category": category["Category"],
                            "feature": sub["Subcategory"]
                        })

            elif level == 3 and len(subcategories) >= 2:
                selected_subcategories = random.sample(subcategories, 2)
                for sub in selected_subcategories:
                    used_features.add(sub["Subcategory"])
                    available_words = [w for w in sub["Members"] if w not in used_words]
                    if len(available_words) < 1:
                        continue
                    word = random.choice(available_words)
                    used_words.add(word)
                    instance["items"].append(word)
                    instance_details["items"].append({
                        "word": word,
                        "category": category["Category"],
                        "feature": sub["Subcategory"]
                    })

        if len(instance["items"]) >= 8:
            instance["items"] = instance["items"][:8]
            instance_details["items"] = instance_details["items"][:8]
            instance["target"] = random.choice(instance["items"])
            instance_details["target"] = instance["target"]
            return instance, instance_details
        else:
            return None, None

    def save_json(self, data, filepath):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)

if __name__ == '__main__':
    GuessWhatGameInstanceGenerator().generate()