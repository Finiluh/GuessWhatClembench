import json
import random

num_lists = 50
# file_path = "GuessWho-clembench/games/guess_what/resources/categories/words_lists"

def load_data_from_json(file_path):
    with open(file_path) as f:
        data = json.load(f)
    return data

def get_random_word(data):
    category = random.choice(list(data.keys()))
    subcategories = data[category]
    if isinstance(subcategories, list):
        # If subcategories is a list, directly select a word from it
        return random.choice(subcategories)
    else:
        # If subcategories is a dictionary, proceed as before
        subcategory = random.choice(list(subcategories.keys()))
        words = subcategories[subcategory]
        return random.choice(words)

def generate_lists_per_level(data, categories, num_lists, level, num_words=8):
    lists = []
    for _ in range(num_lists):
        if level == 1:
            # All words closely related, randomly selecting words from all categories
            words = [get_random_word(data) for _ in range(num_words)]
        elif level == 2:
            # Words less related, 2 words from the same subcategory and 2 from different subcategories
            words = []
            for _ in range(num_words):
                if len(words) < 4 or random.random() < 0.5:
                    words.append(get_random_word(data))
                else:
                    # Ensuring at least 2 words from the same subcategory
                    category = random.choice(categories)
                    words.append(get_random_word(data[category]))
        elif level == 3:
            # Each word is from a different category
            words = [get_random_word(data[category]) for category in random.sample(categories, num_words)]
        else:
            raise ValueError("Invalid level specified.")

        target_word = random.choice(words)
        lists.append((words, target_word))
    return lists

def save_lists_to_txt(lists, level):
    file_path = f"resources/categories/levels/level_{level}.txt"
    with open(file_path, 'w') as f:
        for i, (words, target_word) in enumerate(lists, 1):
            f.write(f"List {i} (Target word: {target_word}):\n")
            for word in words:
                f.write(f"{word}\n")
            f.write("\n")

# Load data from JSON
data = load_data_from_json('GuessWho-clembench/games/guess_what/resources\categories/words_list.json')
categories = list(data.keys())

# Generate the lists for each level
lists_level_1 = generate_lists_per_level(data, categories, num_lists, level=1)
lists_level_2 = generate_lists_per_level(data, categories, num_lists, level=2)
lists_level_3 = generate_lists_per_level(data, categories, num_lists, level=3)

# Save the lists to text files
save_lists_to_txt(lists_level_1, level=1)
save_lists_to_txt(lists_level_2, level=2)
save_lists_to_txt(lists_level_3, level=3)
