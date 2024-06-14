import json
from nltk.corpus import wordnet as wn
import nltk
import os

# Download WordNet data if not already downloaded
nltk.download('wordnet')

# # Define categories and subcategories
# categories = ['mammal', 'vehicle', 'device', 'reproductive_structure']
# subcategories = {
#     'vehicle': ['wheeled_vehicle.n.01', 'aircraft.n.01'],
#     'mammal': ['feline.n.01', 'canine.n.02'],
#     'device': ['electronic_device.n.01', 'musical_instrument.n.01'],
#     'reproductive_structure': ['flower.n.01', 'edible_fruit.n.01']
# }

categories = ['mammal', 'vehicle', 'device', 'reproductive_structure', 'bird', 'food', 'clothing', 'structure']
subcategories = {
    'vehicle': ['wheeled_vehicle.n.01', 'aircraft.n.01'],
    'mammal': ['feline.n.01', 'canine.n.02'],
    'device': ['electronic_device.n.01', 'musical_instrument.n.01'],
    'reproductive_structure': ['flower.n.01', 'edible_fruit.n.01'],
    'bird': ['bird.n.01', 'passerine.n.01'],
    'food': ['vegetable.n.01', 'solid_food.n.01'],
    'clothing': ['clothing.n.01', 'footwear.n.02'],
    'structure': ['building.n.01', 'housing.n.01'],
}

# Function to get all hyponyms of a synset
def get_hyponyms(synset):
    hyponyms = set()
    hyponym_synsets = synset.hyponyms()
    for hyponym in hyponym_synsets:
        hyponyms.add(hyponym.name())
        hyponyms.update(get_hyponyms(hyponym))
    return hyponyms

# Function to filter out compound nouns
def filter_compound_nouns(words):
    return {word for word in words if '_' not in word and ' ' not in word}

# Create taxonomy dictionary
taxonomy = {}
for category, synsets in subcategories.items():
    taxonomy[category] = {}
    for synset_name in synsets:
        synset = wn.synset(synset_name)
        words = {lemma.name() for lemma in synset.lemmas()}
        hyponyms = get_hyponyms(synset)
        for hyponym in hyponyms:
            hyponym_synset = wn.synset(hyponym)
            words.update({lemma.name() for lemma in hyponym_synset.lemmas()})
        # Filter out compound nouns
        filtered_words = filter_compound_nouns(words)
        taxonomy[category][synset_name] = list(filtered_words)


# Save taxonomy to JSON file
output_path = "GuessWho-clembench/games/guess_what/resources/categories"

# Save taxonomy to JSON file
output_file = os.path.join(output_path, 'words_list.json')
with open(output_file, 'w') as json_file:
    json.dump(taxonomy, json_file, indent=4)

print("Taxonomy JSON file created successfully.")

