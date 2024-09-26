
# Guess What? Game to Evaluate Chat-Optimized Language Models as Conversational Agents in clembench Framework


This repository contains the Clembench Framework and a contribution to the framework with the implementation of a dialogue game called **Guess What?**. It is an information seeking game with two players, where one player, the Guesser, attempts to guess a target word from a list of candidate words by asking questions. The other player, the Answerer, responds with simple "yes" or "no" answers. The goal is for the Guesser to correctly guess the target in as few turns as possible while following specific game rules that can be found in the initial prompts templates under utils.

Details of the framework and updated versions can be found [here](https://github.com/clembench/clembench).
This repository contains the code for setting up the framework and the implemented games are further discussed in

> Chalamalasetti, K., Götze, J., Hakimov, S., Madureira, B., Sadler, P., & Schlangen, D. (2023). clembench: Using Game Play to Evaluate Chat-Optimized Language Models as Conversational Agents (arXiv:2305.13455). arXiv. https://doi.org/10.48550/arXiv.2305.13455


### Guess What? Game details

There are 2 versions of the **Guess What?** game in this repository: a zero-shot version, called guesswhat_withoutreprompt, and one-shot version, called guesswhat. Additionally, we used two different datasets to create the instances of the games, one that mixed abstract and concrete words and another one from which we only used abstract words. 

The full datasets and all the information related to them can be found bellow: 

>Castro, N., Curley, T., & Hertzog, C. (2021). Category norms with a cross-sectional sample of adults in the United States: Consideration of cohort, age, and historical effects on semantic categories. Behavior Research Methods, 53(2), 898–917. https://doi.org/10.3758/s13428-020-01454-9

>Banks, B., & Connell, L. (2022). Category Production Norms for 117 Concrete and Abstract Categories. OSF. https://osf.io/jgcu6

This game aims to assess whether cLLMs can develop efficient information-seeking strategies to narrow down possible options quickly, while considering how semantic relationships between words impact this process. With this purpose, we created candidate lists of 8 words with varying degrees of semantic similarity, grouped into distinct categories and subcategories.
The goal is to see if the model can identify the shared property among these words and ask strategic questions based on that understanding. This ability is evaluated using a Quality Score, where fewer turns to guess the correct word indicate a more effective search strategy.
## Experiments
According to the semantic relationship of the words there are 3 experiments in the game that goes from less related to more, and they are structured as follows: 

- **Level 1**: 4 categories, each containing 2 subcategories, with 1 word per subcategory.
- **Level 2**: 2 categories, each containing 2 subcategories, with 2 words per subcategory.
- **Level 3**: 1 category, containing 4 subcategories, with 2 words per subcategory.


## Scores
Apart from the common metrics of the framework the game also measures the following:

- **Speed**: How quickly the correct guess was made relative to the ideal number of turns for each level (lower bound).
- **Quality Score**: Speed minus a penalty of 10 when a reprompt is made.
- **Invalid Content response**: Counts the number of content invalid responses from each player.
- **Invalid Format response**: Counts the number of invalid form responses from each player.
- **Reprompts to player**: Counts the reprompts made to each of the players.


## Running the game

To generate new instances with the mixed dataset run the instancegenerator.py

```bash
python -m games.guesswhat_withoutreprompting.instancegenerator
python -m games.guesswhat.instancegenerator

```
To generate new instances with the abstract dataset use the abstract_instancegenerator.py
```bash
python -m games.guesswhat_withoutreprompt.abstract_instancegenerator
python -m games.guesswhat.instancegenerator

```
To run the games you can use  these command:
```bash
python -m scripts.cli run -g guesswhat_withoutreprompting -m (MODEL_NAME) 
python -m scripts.cli run -g guesswhat -m (MODEL_NAME) 

```
If you do not indicate any experiment name when running the game all the experiments will be run. If you want to run a single experiment from any of the **Guess What?** versions add the flag -e and the name of the experiments, Level_1, Level_2 or Level_3 for the mixed dataset and Abs_Level_1, Abs_Level_2 or Abs_Level_3 for abstract words.


## Results

The results of running the guesswhat_withoutreprompt and guesswhat with both datasets can be found under results_eval_mixed_dataset.zip and results_eval_abstract_dataset.zip.


## Using the benchmark

This repository is tested on `Python 3.8+`

You can find more information on how to use the benchmark in the links below. For more details go to the framework main repository. 

- [How to run the benchmark and evaluation locally](docs/howto_run_benchmark.md)
- [How to run the benchmark, update leaderboard workflow](docs/howto_benchmark_workflow.md)
- [How to add a new model](docs/howto_add_models.md)
- [How to add and run your own game](docs/howto_add_games.md)
- [How to integrate with Slurk](docs/howto_slurk.md)

