import nltk
from nltk.corpus import wordnet as wn
import random
import os

# Function to get all simpler words from a specific synset
def get_all_simple_words_from_synset(synset_name, selected_words=set()):
    synset = wn.synset(synset_name)
    hyponyms = list(synset.closure(lambda s: s.hyponyms(), depth=2))
    
    words = set()
    for hyponym in hyponyms:
        for lemma in hyponym.lemmas():
            word = lemma.name().replace('_', ' ')
            if len(word.split()) == 1 and word.isalpha() and word not in selected_words:
                words.add(word)
    print("get all simple words:", words)
    return list(words)

def category_level(category, subcategories, num_words=8):
    selected_words = set()
    words = []
    subcategory_count = len(subcategories[category])
    words_per_subcategory = num_words // subcategory_count

    for subcategory in subcategories[category]:
        new_words = get_all_simple_words_from_synset(subcategory, selected_words)
        new_words = random.sample(new_words, min(words_per_subcategory, len(new_words)))
        words += new_words
        selected_words.update(new_words)

    # If we didn't get enough words, fill the remaining spots with random words from the subcategories
    if len(words) < num_words:
        remaining_subcategories = [s for s in subcategories[category] if s not in selected_words]
        while len(words) < num_words:
            subcategory = random.choice(remaining_subcategories)
            new_words = get_all_simple_words_from_synset(subcategory, selected_words)
            additional_words = random.sample(new_words, min(num_words - len(words), len(new_words)))
            words += additional_words
            selected_words.update(additional_words)
    
    return words

def mixed_category_level(categories, subcategories, num_words=8):
    selected_words = set()
    words = []
    chosen_categories = random.sample(categories, num_words)  # Select different categories

    for category in chosen_categories:
        subcategory = random.choice(subcategories[category])
        new_words = get_all_simple_words_from_synset(subcategory, selected_words)
        if new_words:
            chosen_word = random.choice(new_words)
            words.append(chosen_word)
            selected_words.add(chosen_word)
    
    return words[:num_words]

def subcategory_level(categories, subcategories, num_words=8):
    selected_words = set()
    words = []
    chosen_categories = random.sample(categories, 4)  # Select 4 different categories
    for category in chosen_categories:
        subcategory = random.choice(subcategories[category])
        new_words = get_all_simple_words_from_synset(subcategory, selected_words)
        if new_words:
            chosen_word = random.choice(new_words)
            words.append(chosen_word)
            selected_words.add(chosen_word)
    
    # If we didn't get enough words, fill the remaining spots with random words from the remaining subcategories
    remaining_categories = [category for category in categories if category not in chosen_categories]
    while len(words) < num_words:
        category = random.choice(remaining_categories)
        subcategory = random.choice(subcategories[category])
        new_words = get_all_simple_words_from_synset(subcategory, selected_words)
        if new_words:
            additional_words = random.sample(new_words, min(1, len(new_words)))
            words += additional_words
            selected_words.update(additional_words)
    
    return words[:num_words]

def generate_unique_lists_per_level(num_lists=100):
    categories = ['mammal', 'vehicle', 'device', 'reproductive_structure', 'bird', 'furniture', 'clothing', 'structure']
    subcategories = {
        'vehicle': ['wheeled_vehicle.n.01', 'aircraft.n.01'],
        'mammal': ['feline.n.01', 'canine.n.02'],
        'device': ['electronic_device.n.01', 'musical_instrument.n.01'],
        'reproductive_structure': ['flower.n.01', 'edible_fruit.n.01'],
        'bird': ['bird.n.01', 'passerine.n.01'],
        'furniture': ['chair.n.01', 'table.n.02'],
        'clothing': ['clothing.n.01', 'footwear.n.02'],
        'structure': ['building.n.01', 'housing.n.01'],
    }

    lists_level_1_0 = []
    lists_level_2_0 = []
    lists_level_3_0 = []
    all_selected_words = set() # To avoid repetion of target words

    for _ in range(num_lists):
        # Level 1: All words are closely related and equally distributed from subcategories
        category = random.choice(categories)
        words = category_level(category, subcategories, 8)
        target_word = random.choice(words)
        while target_word in all_selected_words:
            target_word = random.choice(words)
        all_selected_words.add(target_word)
        lists_level_1_0.append((words, target_word))

        # Level 2: Words from 4 different categories, one from each subcategory
        words = subcategory_level(categories, subcategories, 8)
        target_word = random.choice(words)
        while target_word in all_selected_words:
            target_word = random.choice(words)
        all_selected_words.add(target_word)
        lists_level_2_0.append((words, target_word))

        # Level 3: Each word is from a different category
        words = mixed_category_level(categories, subcategories, 8)
        target_word = random.choice(words)
        while target_word in all_selected_words:
            target_word = random.choice(words)
        all_selected_words.add(target_word)
        lists_level_3_0.append((words, target_word))


    return lists_level_1_0, lists_level_2_0, lists_level_3_0

def save_lists_to_txt(lists, level):
    file_path = f"games/guess_what/resources/categories/levels/level_{level}_0.txt"
    
    with open(file_path, 'w') as f:
        for i, (words, target_word) in enumerate(lists, 1):
            f.write(f"List {i}:\n")
            f.write(f"Target word: {target_word}\n")
            f.write(f"Words: {', '.join(words)}\n")
            f.write("\n")

# Generate the lists
lists_level_1_0, lists_level_2_0, lists_level_3_0 = generate_unique_lists_per_level()


# Save the lists to text files
save_lists_to_txt(lists_level_1_0, level=1_0)
save_lists_to_txt(lists_level_2_0, level=2_0)
save_lists_to_txt(lists_level_3_0, level=3_0)

# Print confirmation message
print("Lists have been saved.")
