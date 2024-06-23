from typing import Dict, List
import numpy as np
from backends import Model
from clemgame.clemgame import GameMaster, GameBenchmark, Player, DialogueGameMaster, GameScorer
from clemgame.metrics import METRIC_ABORTED, METRIC_SUCCESS, METRIC_LOSE, METRIC_REQUEST_COUNT, \
    METRIC_REQUEST_COUNT_VIOLATED, METRIC_REQUEST_COUNT_PARSED, METRIC_REQUEST_SUCCESS, BENCH_SCORE
from clemgame import get_logger
from clemgame import file_utils, string_utils


GAME_NAME = "guesswhat"

logger = get_logger(__name__)

class Guesser(Player):
    def __init__(self, model: Model, max_turns):
        super().__init__(model)
        self.max_turns = max_turns

    def _custom_response(self, messages, turn_idx):
        # mock response
        return 'QUESTION: Is it a mammal?'

class Answerer(Player):
    def __init__(self, model: Model):
        super().__init__(model)
        
    def _custom_response(self, messages, turn_idx):
        # mock response
        if 'QUESTION: Is it a mammal?' in messages[-1]:
            return "ANSWER: yes"
        return "ANSWER: no"

class GuessWhat(DialogueGameMaster):
    """
    This class implements a "Guess What" game in which player A (the Guesser) asks a
    question or makes a guess, and player B (the Answerer) responds with "yes" or "no".
    """
    def __init__(self, experiment: Dict, player_models: List[Model]):
        super().__init__(GAME_NAME, experiment, player_models)
        self.max_turns: int = experiment["max_turns"]
        self.guesser_initial_prompt = self.experiment["guesser_initial_prompt"]
        self.answerer_initial_prompt = self.experiment["answerer_initial_prompt"]
        self.guess_made = False  # Track if a guess has been made

    def _on_setup(self, **game_instance):
        logger.info("_on_setup")
        self.game_instance = game_instance

        self.target_word = game_instance["target_word"]
        self.candidate_list = game_instance["candidate_list"]

        self.guesser_initial_prompt = self.guesser_initial_prompt.replace("$LIST$", str(self.candidate_list))
        self.answerer_initial_prompt = self.answerer_initial_prompt.replace("$TARGET WORD$", str(self.target_word))
        self.guesser_initial_prompt = self.guesser_initial_prompt.replace("$N$", str(self.max_turns))
        self.answerer_initial_prompt = self.answerer_initial_prompt.replace("$N$", str(self.max_turns))

        self.guesser = Guesser(self.player_models[0], self.max_turns)
        self.answerer = Answerer(self.player_models[1])

        self.add_player(self.guesser)
        self.add_player(self.answerer)

        self.invalid_response = False
        self.guess_word = None

    def _on_before_game(self):
        self.add_user_message(self.guesser, self.guesser_initial_prompt)
        
    def _does_game_proceed(self):
        if self.invalid_response:
            self.log_to_self("invalid format", "abort game")
            return False
        if self.guess_word == self.target_word:
            self.log_to_self("correct guess", "end game")
            return False
        if self.guess_made:
            self.log_to_self("guess made", "end game")
            return False
        if self.current_turn >= self.max_turns:
            self.log_to_self("max turns reached", str(self.max_turns))
            return False
        return True

    def _validate_player_response(self, player: Player, utterance: str) -> bool:
        if player == self.guesser:
            if not (utterance.startswith("QUESTION:") or utterance.startswith("GUESS:")):
                self.invalid_response = True
                return False
            self.log_to_self("valid response", "continue")
            if utterance.startswith("GUESS:"):
                guess_word = utterance.replace("GUESS:", "").strip().lower()
                guess_word = string_utils.remove_punctuation(guess_word)
                self.guess_word = guess_word
                self.guess_made = True  # Mark that a guess has been made
                self.log_to_self("valid guess", self.guess_word)
        if player == self.answerer:
            if utterance not in ["ANSWER: yes", "ANSWER: no", "ANSWER: Yes.", "ANSWER: Yes", "ANSWER: No.", "ANSWER: No"]:
                self.invalid_response = True
                return False
            self.log_to_self("valid response", "continue")
        return True
    
    def _after_add_player_response(self, player: Player, utterance: str):
    
        if player == self.guesser:
            if self.current_turn == 0:
                prompt_with_first_question = f"{self.answerer_initial_prompt}\n\n{utterance}"  # Include first question in the prompt
                self.add_user_message(self.answerer, prompt_with_first_question)
            else:
                self.add_user_message(self.answerer, utterance)
        if player == self.answerer:  
            if self.guess_word != self.target_word:
                self.add_user_message(self.guesser, utterance)
            else: 
                self.add_user_message(self.guesser, utterance)

class GuessWhatScorer(GameScorer):
    def __init__(self, experiment: Dict, game_instance: Dict):
        super().__init__(GAME_NAME, experiment, game_instance)

    def compute_scores(self, episode_interactions: Dict) -> None:
        turn_scores = []
        prev_guess = None
        prev_guess_counter = 0
        prev_response = None
        prev_response_counter = 0
        invalid_response = False
        guesser_won = False
        for turn_idx, turn in enumerate(episode_interactions["turns"]):
            turn_score = {"guess": None, "response": None, "request_count": 1}

            for event in turn:
                action = event["action"]
                if action["type"] == "invalid format":
                    invalid_response = True
                if action["type"] == "guess":
                    turn_score["guess"] = action["content"]
                if action["type"] == "response":
                    turn_score["response"] = action["content"]
                if action["type"] == "correct guess":
                    guesser_won = True

            if invalid_response:
                turn_score["violated_request_count"] = 1
                turn_score["parsed_request_count"] = 0
            else:
                turn_score["violated_request_count"] = 0
                turn_score["parsed_request_count"] = 1

            if turn_score["guess"] is not None and turn_score["guess"] == prev_guess:
                prev_guess_counter += 1
            if turn_score["response"] is not None and turn_score["response"] == prev_response:
                prev_response_counter += 1
            self.log_turn_score(turn_idx, 'Accuracy', 1 if guesser_won else 0)
            self.log_turn_score(turn_idx, METRIC_REQUEST_COUNT_VIOLATED, turn_score["violated_request_count"])
            self.log_turn_score(turn_idx, METRIC_REQUEST_COUNT_PARSED, turn_score["parsed_request_count"])
            self.log_turn_score(turn_idx, METRIC_REQUEST_COUNT, turn_score["request_count"])
            prev_guess = turn_score["guess"]
            prev_response = turn_score["response"]
            turn_scores.append(turn_score)

        violated_request_count = sum([turn["violated_request_count"] for turn in turn_scores])
        self.log_episode_score(METRIC_REQUEST_COUNT_VIOLATED, violated_request_count)

        parsed_request_count = sum([turn["parsed_request_count"] for turn in turn_scores])
        self.log_episode_score(METRIC_REQUEST_COUNT_PARSED, parsed_request_count)

        request_count = sum([turn["request_count"] for turn in turn_scores])
        self.log_episode_score(METRIC_REQUEST_COUNT, request_count)

        self.log_episode_score(METRIC_REQUEST_SUCCESS, parsed_request_count / request_count)

        if invalid_response:
            self.log_episode_score(METRIC_ABORTED, 1)
            self.log_episode_score(METRIC_SUCCESS, 0)
            self.log_episode_score(METRIC_LOSE, 0)
            self.log_episode_score(BENCH_SCORE, np.nan)
        else:
            self.log_episode_score(METRIC_ABORTED, 0)
            if guesser_won:
                self.log_episode_score(METRIC_SUCCESS, 1)
                self.log_episode_score(METRIC_LOSE, 0)
                self.log_episode_score(BENCH_SCORE, 100 / len(turn_scores))
            else:
                self.log_episode_score(METRIC_SUCCESS, 0)
                self.log_episode_score(METRIC_LOSE, 1)
                self.log_episode_score(BENCH_SCORE, 0)

        self.log_episode_score('Repetition-Guesser', prev_guess_counter)
        self.log_episode_score('Repetition-Answerer', prev_response_counter)

class GuessWhatGameBenchmark(GameBenchmark):
    def __init__(self):
        super().__init__(GAME_NAME)

    def get_description(self):
        return "Guess What game between two agents where one asks questions and the other answers with yes or no."

    def create_game_master(self, experiment: Dict, player_models: List[Model]) -> GameMaster:
        return GuessWhat(experiment, player_models)

    def create_game_scorer(self, experiment: Dict, game_instance: Dict) -> GameScorer:
        return GuessWhatScorer(experiment, game_instance)

def main():
    # select one experiment and instance
    experiments = file_utils.load_json("in/instances.json", GAME_NAME)
    experiment_1 = experiments["experiments"][0]
    game_1 = experiment_1["game_instances"][0]
    master = GuessWhat(experiment_1, ["mock", "mock"])
    master.setup(**game_1)
    master.play()

if __name__ == '__main__':
    main()


