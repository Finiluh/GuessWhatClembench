""" import json
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
 """
 
""" import nltk
from nltk.corpus import wordnet as wn
import random

# Function to get simpler words from a specific synset
def get_simple_words_from_synset(synset_name, num_words=8, selected_words=set()):
    synset = wn.synset(synset_name)
    hyponyms = list(synset.closure(lambda s: s.hyponyms(), depth=1))
    
    words = set()
    for hyponym in hyponyms:
        for lemma in hyponym.lemmas():
            word = lemma.name().replace('_', ' ')
            if len(word.split()) == 1 and word.isalpha() and word not in selected_words:
                words.add(word)
    
    if len(words) < num_words:
        additional_hyponyms = list(synset.closure(lambda s: s.hyponyms(), depth=2))
        for hyponym in additional_hyponyms:
            for lemma in hyponym.lemmas():
                word = lemma.name().replace('_', ' ')
                if len(word.split()) == 1 and word.isalpha() and word not in selected_words:
                    words.add(word)
            if len(words) >= num_words:
                break
    
    words_list = list(words)
    random_words = random.sample(words_list, min(num_words, len(words_list)))
    
    return random_words

def category_level(category, subcategories, num_words=8):
    selected_words = set()
    words = []
    while len(words) < num_words:
        subcategory = random.choice(subcategories[category])
        new_words = get_simple_words_from_synset(subcategory, num_words - len(words), selected_words)
        words += new_words
        selected_words.update(new_words)
    return words

def mixed_category_level(categories, subcategories, num_words=8):
    selected_words = set()
    words = []
    while len(words) < num_words:
        for category in categories:
            subcategory = random.choice(subcategories[category])
            new_words = get_simple_words_from_synset(subcategory, 1, selected_words)
            words += new_words
            selected_words.update(new_words)
    return words[:num_words]

def subcategory_level(categories, subcategories, num_words=8):
    selected_words = set()
    words = []
    while len(words) < num_words:
        if len(words) % 4 == 0:
            category = random.choice(categories)
        subcategory = random.choice(subcategories[category])
        new_words = get_simple_words_from_synset(subcategory, 2, selected_words)
        words += new_words
        selected_words.update(new_words)
    return words[:num_words]

def generate_unique_lists_per_level(num_lists=100):
    categories = ['mammal', 'vehicle', 'device', 'reproductive_structure']
    subcategories = {
        'vehicle': ['wheeled_vehicle.n.01', 'aircraft.n.01', ],
        'mammal': ['feline.n.01', 'canine.n.02'],
        'device': ['electronic_device.n.01', 'musical_instrument.n.01'],
        'reproductive_structure': ['flower.n.01', 'edible_fruit.n.01'],
        
    }

    lists_level_1 = []
    lists_level_2 = []
    lists_level_3 = []

    for _ in range(num_lists):
        # Level 1: All words are closely related
        category = random.choice(categories)
        words = category_level(category, subcategories, 8)
        target_word = random.choice(words)
        lists_level_1.append((words, target_word))

        # Level 2: Words are less related, with 2 words from the same subcategory and 2 subcategories
        words = subcategory_level(categories, subcategories, 8)
        target_word = random.choice(words)
        lists_level_2.append((words, target_word))

        # Level 3: Each word is from a different category
        words = mixed_category_level(categories, subcategories, 8)
        target_word = random.choice(words)
        lists_level_3.append((words, target_word))

    return lists_level_1, lists_level_2, lists_level_3

# Generate the lists
lists_level_1, lists_level_2, lists_level_3 = generate_unique_lists_per_level()

# Print the lists for each level
for idx, (words, target_word) in enumerate(lists_level_1):
    print(f"Level 1, List {idx + 1}:")
    print(f"Words: {words}")
    print(f"Target Word: {target_word}")
    print()

for idx, (words, target_word) in enumerate(lists_level_2):
    print(f"Level 2, List {idx + 1}:")
    print(f"Words: {words}")
    print(f"Target Word: {target_word}")
    print()

for idx, (words, target_word) in enumerate(lists_level_3):
    print(f"Level 3, List {idx + 1}:")
    print(f"Words: {words}")
    print(f"Target Word: {target_word}")
    print()
    
    def save_lists_to_txt(lists, level):
        file_path = f"games/guess_what/resources/categories/levels/level_{level}.txt"
        with open(file_path, 'w') as f:
            for i, (words, target_word) in enumerate(lists, 1):
                f.write(f"List {i} (Target word: {target_word}):\n")
                for word in words:
                    f.write(f"{word}\n")
                f.write("\n")

# Generate the lists
lists_level_1, lists_level_2, lists_level_3 = generate_unique_lists_per_level()

# Save the lists to text files
save_lists_to_txt(lists_level_1, level=1)
save_lists_to_txt(lists_level_2, level=2)
save_lists_to_txt(lists_level_3, level=3)

# Print confirmation message
print("Lists have been saved to their respective files.") """

import nltk
from nltk.corpus import wordnet as wn
import random

# Function to get simpler words from a specific synset
def get_simple_words_from_synset(synset_name, num_words=8, selected_words=set()):
    synset = wn.synset(synset_name)
    hyponyms = list(synset.closure(lambda s: s.hyponyms(), depth=1))
    
    words = set()
    for hyponym in hyponyms:
        for lemma in hyponym.lemmas():
            word = lemma.name().replace('_', ' ')
            if len(word.split()) == 1 and word.isalpha() and word not in selected_words:
                words.add(word)
    
    if len(words) < num_words:
        additional_hyponyms = list(synset.closure(lambda s: s.hyponyms(), depth=2))
        for hyponym in additional_hyponyms:
            for lemma in hyponym.lemmas():
                word = lemma.name().replace('_', ' ')
                if len(word.split()) == 1 and word.isalpha() and word not in selected_words:
                    words.add(word)
            if len(words) >= num_words:
                break
    
    words_list = list(words)
    random_words = random.sample(words_list, min(num_words, len(words_list)))
    
    return random_words

def category_level(category, subcategories, num_words=8):
    selected_words = set()
    words = []
    while len(words) < num_words:
        subcategory = random.choice(subcategories[category])
        new_words = get_simple_words_from_synset(subcategory, num_words - len(words), selected_words)
        words += new_words
        selected_words.update(new_words)
    return words

def mixed_category_level(categories, subcategories, num_words=8):
    selected_words = set()
    words = []
    while len(words) < num_words:
        for category in categories:
            subcategory = random.choice(subcategories[category])
            new_words = get_simple_words_from_synset(subcategory, 1, selected_words)
            words += new_words
            selected_words.update(new_words)
    return words[:num_words]

def subcategory_level(categories, subcategories, num_words=8):
    selected_words = set()
    words = []
    while len(words) < num_words:
        if len(words) % 4 == 0:
            category = random.choice(categories)
        subcategory = random.choice(subcategories[category])
        new_words = get_simple_words_from_synset(subcategory, 2, selected_words)
        words += new_words
        selected_words.update(new_words)
    return words[:num_words]

def generate_unique_lists_per_level(num_lists=100):
    categories = ['mammal', 'vehicle', 'device', 'reproductive_structure']
    subcategories = {
        'vehicle': ['wheeled_vehicle.n.01', 'aircraft.n.01'],
        'mammal': ['feline.n.01', 'canine.n.02'],
        'device': ['electronic_device.n.01', 'musical_instrument.n.01'],
        'reproductive_structure': ['flower.n.01', 'edible_fruit.n.01'],
    }

    lists_level_1 = []
    lists_level_2 = []
    lists_level_3 = []

    for _ in range(num_lists):
        # Level 1: All words are closely related
        category = random.choice(categories)
        words = category_level(category, subcategories, 8)
        target_word = random.choice(words)
        lists_level_1.append((words, target_word))

        # Level 2: Words are less related, with 2 words from the same subcategory and 2 subcategories
        words = subcategory_level(categories, subcategories, 8)
        target_word = random.choice(words)
        lists_level_2.append((words, target_word))

        # Level 3: Each word is from a different category
        words = mixed_category_level(categories, subcategories, 8)
        target_word = random.choice(words)
        lists_level_3.append((words, target_word))

    return lists_level_1, lists_level_2, lists_level_3

def save_lists_to_txt(lists, level):
    file_path = f"games/guess_what/resources/categories/levels/level_{level}.txt"
    with open(file_path, 'w') as f:
        for i, (words, target_word) in enumerate(lists, 1):
            f.write(f"List {i}:\n")
            f.write(f"Target word: {target_word}\n")
            f.write(f"Words: {', '.join(words)}\n")
            f.write("\n")

# Generate the lists
lists_level_1, lists_level_2, lists_level_3 = generate_unique_lists_per_level()

# Save the lists to text files
save_lists_to_txt(lists_level_1, level=1)
save_lists_to_txt(lists_level_2, level=2)
save_lists_to_txt(lists_level_3, level=3)

# Print confirmation message
print("Lists have been saved to their respective files.")
