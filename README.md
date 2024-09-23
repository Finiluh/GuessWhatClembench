
# Guess What? Game to Evaluate Chat-Optimized Language Models as Conversational Agents in clembench Framework


This repository contains the implementation of a dialogue game called **GuessWhat?**. It is a two-player question-and-answer game where one player, the Guesser, attempts to guess a target word from a list of candidate words by asking questions. The other player, the Answerer, responds with simple "yes" or "no" answers. The goal is for the Guesser to correctly guess the target word within a certain number of turns while following specific game rules.

The game is designed to simulate a structured dialogue between two agents and includes built-in validation for question formats, content, and game rules.

This game is built in clembench framework https://github.com/clembench/clembench :

The cLLM (chat-optimized Large Language Model, "clem") framework tests such models' ability to engage in games – rule-constituted activities played using language.
The framework is a systematic way of probing for the situated language understanding of language using agents.

This repository contains the code for setting up the framework and implements a number of games that are further discussed in 

> Chalamalasetti, K., Götze, J., Hakimov, S., Madureira, B., Sadler, P., & Schlangen, D. (2023). clembench: Using Game Play to Evaluate Chat-Optimized Language Models as Conversational Agents (arXiv:2305.13455). arXiv. https://doi.org/10.48550/arXiv.2305.13455

### Game details

There is 2 versions of the game in this repository: Guess What? with reprompting system and Guess What? without reprompting system. Also, we used abstract and concrete and abstract mixed datasets for instances of both versions of the game. 

- **Two Players**: Guesser and Answerer.
- **Turn-based Gameplay**: Players take turns asking and answering questions.
- **Question Validation**: Checks for valid question formats and content.
- **Reprompt System**: If a player provides an invalid response, they are reprompted (up to a limit).
- **Scoring System**: Tracks game outcomes, speed, and penalties for invalid questions and reprompts.
- **Multiple Difficulty Levels**: Game difficulty can be adjusted by changing the number of categories and features in the candidate word list.
- **Abstract Version of Instances**: The instances can be generated with both of the datasets we provided in the repository. 
  
## How It Works

1. **Guesser**: Asks questions about the target word (e.g., "Is it a mammal?").
2. **Answerer**: Responds with either "yes" or "no".
3. **Game Ends**: When the Guesser either guesses the correct word or runs out of turns.

### Game Rules
- The Guesser can ask questions using the format `QUESTION: <question>?` or make a guess using `GUESS: <word>`.
- The Answerer can only respond with "ANSWER: yes" or "ANSWER: no".
- The game enforces limits on question types and allows reprompting if an invalid format or content is detected.
- The game ends after a correct guess, incorrect guess, or when the maximum number of turns is reached.

## Reprompt System
If a player violates the format or content rules for a question or answer, they will be reprompted, up to a specified limit (default: 1). Exceeding the reprompt limit aborts the game.

## Scoring System
The scoring system evaluates:
- **Success**: Whether the Guesser correctly guessed the word.
- **Lose**: When the Guesser incorrectly guessed the word. 
- **Speed**: How quickly the correct guess was made relative to the expected number of turns.
- **Penalties**: Points are deducted for invalid responses and reprompts.

## Running the game

To generate the instances with the abstract dataset use this command for the version without reprompting system
```bash
python -m games.guesswhat_withoutreprompt.abstract_instancegenerator
```
To run the game without the repromting system use this command:
```bash
python -m scripts.cli run -g guesswhat_withoutreprompt -m (MODEL_NAME)
```
To run the game with the reprompting system use this command:
```bash
python -m scripts.cli run -g guesswhat -m (MODEL_NAME)
```
Add flags of -e Level_1 or Level_2 or Level_3 to run the games with mixed dataset. Add flags of -e Abs_Level_1, Abs_Level_2, Abs_Level_3 
to run the game with the abstract version of the game.

To generate the instances with the mixed dataset use this command for the version with reprompting system
```bash
python -m games.guesswhat_withoutreprompting.instancegenerator
```



## Using the benchmark

This repository is tested on `Python 3.8+`

We welcome you to contribute to or extend the benchmark with your own games and models. 
Please simply open a pull request. You can find more information on how to use the benchmark in the links below.

- [How to run the benchmark and evaluation locally](docs/howto_run_benchmark.md)
- [How to run the benchmark, update leaderboard workflow](docs/howto_benchmark_workflow.md)
- [How to add a new model](docs/howto_add_models.md)
- [How to add and run your own game](docs/howto_add_games.md)
- [How to integrate with Slurk](docs/howto_slurk.md)
