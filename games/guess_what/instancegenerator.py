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

print(f"yaml version: {yaml.__version__}")
N_INSTANCES = 20  # how many different target words"
N_GUESSES = 10  # how many tries the guesser will have


logger = clemgame.get_logger(__name__)
GAME_NAME = "guess_what"


class GuessWhatGameInstanceGenerator(GameInstanceGenerator):

    def __init__(self):
        super().__init__(GAME_NAME)

    def load_instances(self):
        # Loading instances from the specified levels
        instances = {}
        levels = ["level_1", "level_2", "level_3"]
        for level in levels:
            fp = f"games/guess_what/resources/categories/levels/{level}.txt"
            with open(fp, 'r') as file:
                instances[level] = file.read().strip().split('\n\n')
        return instances

    def on_generate(self):
        instances = self.load_instances()
        for level, instance_data in instances.items():
            print("Processing level:", level)
            target_words_data = self.parse_instance_data(instance_data)
            if N_INSTANCES > 0:
                assert len(target_words_data) >= N_INSTANCES, \
                    f'Fewer words available ({len(target_words_data)}) than requested ({N_INSTANCES}).'
                target_words_data = random.sample(target_words_data, k=N_INSTANCES)

            # use the same target_words for the different player assignments
            experiment = self.add_experiment(f"{level}")
            experiment["max_turns"] = N_GUESSES

            answerer_prompt = self.load_template("resources/initial_prompts/answerer_prompt")
            guesser_prompt = self.load_template("resources/initial_prompts/guesser_prompt")
            experiment["answerer_initial_prompt"] = answerer_prompt
            experiment["guesser_initial_prompt"] = guesser_prompt

            for game_id, (target, list_words) in enumerate(tqdm(target_words_data)):
                game_instance = self.add_game_instance(experiment, game_id)
                game_instance["target_word"] = target
                game_instance["list_word"] = list_words

    def parse_instance_data(self, data):
                        target_words_data = []
                        for block in data:
                            lines = block.strip().split('\n')
                            target_line = None
                            words_lines = []
                            for line in lines:
                                if line.startswith("Target word:"):
                                    target_line = line
                                elif line.startswith("Words:"):
                                    words_lines.append(line)
                            if target_line and words_lines:
                                target_word = target_line.split(': ')[1]
                                list_words = [word.strip() for words_line in words_lines for word in words_line.split(':')[1].split(',')]
                                target_words_data.append((target_word, list_words))
                            else:
                                print("Error: Target word or Words lines are missing or not formatted correctly in block:", block)
                        return target_words_data



if __name__ == '__main__':
    GuessWhatGameInstanceGenerator().generate()
