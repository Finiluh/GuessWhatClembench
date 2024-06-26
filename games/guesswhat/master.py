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

def check_question(question: str, candidate_list: List[str]) -> List[Dict]:
    """
    Checks if any element in the candidate list is mentioned in the question
    and if there are multiple questions in a single turn.
    """
    errors = []
    if question.count("QUESTION:") > 1:
        errors.append({
            "message": "Multiple questions detected in a single turn.",
            "type": 1
        })

    question = question.replace("QUESTION:", "").strip().lower()
    question_words = string_utils.remove_punctuation(question).split()

    for candidate in candidate_list:
        if candidate.lower() in question_words:
            errors.append({
                "message": f"Invalid question format.",
                "type": 0
            })
    
    return errors

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
        self.incorrect_guess = False 
        self.correct_guess = False

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
        # if self.correct_guess or self.guess_made:
        #     self.log_to_self("valid guess", "end game")
        #     return False
        if self.correct_guess:
            self.log_to_self("correct guess", "end game")
            return False
        if self.incorrect_guess: 
            self.log_to_self("incorrect guess", "end game")
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

            # Check for errors in the question
            if utterance.startswith("QUESTION:"):
                errors = check_question(utterance, self.candidate_list)
                if errors:
                    for error in errors:
                        self.log_to_self("error", error["message"])
                    self.invalid_response = True  
                    return False  
            self.log_to_self("valid response", "continue")

            if utterance.startswith("QUESTION:"):
                errors = check_question(utterance, self.candidate_list)
                if errors:
                    for error in errors:
                        self.log_to_self("error", error["message"])
                    self.invalid_response = True  
                    return False 
                
            elif utterance.startswith("GUESS:"):
                guess_word = utterance.replace("GUESS:", "").strip().lower()
                guess_word = string_utils.remove_punctuation(guess_word)
                self.guess_word = guess_word

                if guess_word == self.target_word.lower():
                    self.correct_guess = True
                    self.log_to_self("correct guess", guess_word)
                else:
                    self.incorrect_guess = True  # Mark that a guess has been made
                    self.log_to_self("incorrect guess", guess_word)
                return False  # End game after guess
        
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
            if not self.incorrect_guess and not self.correct_guess:  # Check if a guess has not been made
                self.add_user_message(self.guesser, utterance)

class GuessWhatScorer(GameScorer):
    
    def __init__(self, experiment: Dict, game_instance: Dict):
        super().__init__(GAME_NAME, experiment, game_instance)

    def compute_scores(self, episode_interactions: Dict) -> None:
        turn_scores = []
        prev_question = None
        prev_question_counter = 0
        invalid_response = False # Note: This only takes into consideration that both players were compliant or not
        guesser_won = False

        for turn_idx, turn in enumerate(episode_interactions["turns"]):
            turn_score = {"question": None, "request_count": 1}

            for event in turn:
                action = event["action"]
                if action["type"] == "invalid format":
                    invalid_response = True
                if action["type"] == "question":
                    turn_score["question"] = action["content"]
                if action["type"] == "correct guess":
                    guesser_won = True

            if invalid_response:
                turn_score["violated_request_count"] = 1
                turn_score["parsed_request_count"] = 0
            else:
                turn_score["violated_request_count"] = 0
                turn_score["parsed_request_count"] = 1

            if turn_score["question"] is not None and turn_score["question"] == prev_question:
                prev_question_counter += 1

            self.log_turn_score(turn_idx, 'Accuracy', 1 if guesser_won else 0)
            self.log_turn_score(turn_idx, METRIC_REQUEST_COUNT_VIOLATED, turn_score["violated_request_count"])
            self.log_turn_score(turn_idx, METRIC_REQUEST_COUNT_PARSED, turn_score["parsed_request_count"])
            self.log_turn_score(turn_idx, METRIC_REQUEST_COUNT, turn_score["request_count"])
            prev_question = turn_score["question"]
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

        # How often the Guesser repeated the same question
        self.log_episode_score('Repetition-Guesser', prev_question_counter)

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



