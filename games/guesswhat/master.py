from typing import Dict, List
import numpy as np
from backends import Model
from clemgame.clemgame import GameMaster, GameBenchmark, Player, DialogueGameMaster, GameScorer
from clemgame.metrics import METRIC_ABORTED, METRIC_SUCCESS, METRIC_LOSE, METRIC_REQUEST_COUNT, \
    METRIC_REQUEST_COUNT_VIOLATED, METRIC_REQUEST_COUNT_PARSED, METRIC_REQUEST_SUCCESS, BENCH_SCORE
from clemgame import get_logger
from clemgame import file_utils, string_utils
import math
import re


GAME_NAME = "guesswhat"
REPROMPT_LIMIT = 1

logger = get_logger(__name__)

class Guesser(Player):
    def __init__(self, model: Model, max_turns):
        super().__init__(model)
        self.max_turns = max_turns

    def _custom_response(self, messages, turn_idx):
        # mock response
        if turn_idx < self.max_turns-1: 
            return "QUESTION: Is it a mammal?"
        else: 
            return "GUESS: Table"

class Answerer(Player):
    def __init__(self, model: Model, max_turns):
        super().__init__(model)
        self.max_turns = max_turns
        
    def _custom_response(self, messeges, turn_idx):
        if turn_idx < self.max_turns:
            return "ANSWER: No."
        elif turn_idx >= self.max_turns:
            raise Exception("We should not be here...")


class GuessWhat(DialogueGameMaster):
    """
    This class implements a "Guess What?" game in which player A (the Guesser) asks a
    question or makes a guess, and player B (the Answerer) responds with "yes" or "no".
    """

    def __init__(self, experiment: Dict, player_models: List[Model]):

        super().__init__(GAME_NAME, experiment, player_models)

        self.max_turns: int = experiment["max_turns"]
        self.guesser_initial_prompt = self.experiment["guesser_initial_prompt"]
        self.guesser_reprompt = self.experiment["guesser_re_prompt"]
        self.answerer_initial_prompt = self.experiment["answerer_initial_prompt"]
        self.answerer_reprompt = self.experiment["answerer_re_prompt"] 

        self.reprompt_count = {}
        # self.target_word = None
        # self.candidate_list = None
        # self.incorrect_guess = False
        # self.correct_guess = False
        # self.invalid_response = False
        # self.reprompt_count = {}
        # self.guess_word = None
        # self.history = []   

    
    def check_question(self, question: str, candidate_list: List[str]) -> List[Dict]:

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

        # question = question.replace("QUESTION:", "").strip().lower()

        question_text = question.replace("QUESTION:", "").strip().lower()
        question_words = string_utils.remove_punctuation(question).split()
        pattern = re.compile(r"^does the target word (start|end)", re.IGNORECASE)
        positional_question_pattern = re.compile(r"is.[first|second|third|fourth|fifth].*letter.[a-z]", re.IGNORECASE)
        letter_question_pattern = re.compile(r"does.contain.*letter.[a-z]", re.IGNORECASE)
        direct_guess_pattern = re.compile(r"^is the target word\s*(['\"])[^'\"]+?\1\s*\?", re.IGNORECASE)
        length_question_pattern = re.compile(r"does the target word (have|contain) (more|less|exactly) \d+ (letters|letter)", re.IGNORECASE)
        letter_presence_pattern = re.compile(r"does the target word have the letter\s*[a-z]", re.IGNORECASE)
        syllable_question_pattern = re.compile(r"does the target word (have|contain) (more|less|exactly) \d+ (syllables|syllable)", re.IGNORECASE)


        # for candidate in candidate_list:

        #     if candidate.lower() in question_words:
        #         errors.append({
        #             "message": "Invalid question format.",
        #             "type": 0
        #         })

        if "does the target word start with the letter" in question_text or "does the target word contain the letter" in question_text:
                errors.append({
                    "message": "Invalid question. Asking about specific letters is not allowed.",
                    "type": 2
                })

        if pattern.match(question_text):
            errors.append({
                "message": "Invalid question. Asking if the target word starts or ends with something is not allowed.",
                "type": 2
            })

        if positional_question_pattern.search(question_text):
            errors.append({
                "message": "Invalid question format: Positional letter-based questions are forbidden.",
                "type": 3
            })

        if letter_question_pattern.search(question_text):
            errors.append({
                "message": "Invalid question format: Letter-based questions are forbidden.",
                "type": 2
            })

        if direct_guess_pattern.match(question_text):
            errors.append({
                "message": "Invalid question format. Direct guessing of the target word is not allowed.",
                "type": 4
            })

        direct_guess_match = direct_guess_pattern.match(question_text)

        if direct_guess_match:
            guessed_word = direct_guess_match.group(1).strip()
            if guessed_word.lower() in [word.lower() for word in self.candidate_list]:
                errors.append({
                    "message": "Invalid question format. Direct guessing of the target word is not allowed.",
                    "type": 4
                })

        if length_question_pattern.search(question_text):
            errors.append({
                "message": "Invalid question. Asking about the length of the target word is not allowed.",
                "type": 5
            })
            
        if letter_presence_pattern.search(question_text):
            errors.append({
                "message": "Invalid question format: Asking about the presence of specific letters is not allowed.",
                "type": 6
            })

        if syllable_question_pattern.search(question_text):
            errors.append({
               "message": "Invalid question format: Asking about the number of syllables is not allowed.",
                "type": 7
            })

        return errors

    def _on_setup(self, **game_instance):
        logger.info("_on_setup")
        self.game_instance = game_instance

        self.target_word = game_instance["target_word"]
        self.candidate_list = game_instance["candidate_list"]

        self.guesser_initial_prompt = self.guesser_initial_prompt.replace("$LIST$", str(self.candidate_list)).replace("$N$", str(self.max_turns-1))
        self.answerer_initial_prompt = self.answerer_initial_prompt.replace("$TARGET WORD$", str(self.target_word))
       
        self.guesser_reprompt = self.guesser_reprompt.replace("$N$", str(REPROMPT_LIMIT)) # if the repompts are higher than 1 this reprompt limit should be updated in each turn.
        self.answerer_reprompt = self.answerer_reprompt.replace("$N$", str(REPROMPT_LIMIT))
  
        self.guesser = Guesser(self.player_models[0], self.max_turns)
        self.answerer = Answerer(self.player_models[1], self.max_turns)

        self.add_player(self.guesser)
        self.add_player(self.answerer)

        # self.invalid_response = False

        # Two different variables for the errors 
        self.invalid_format = False
        self.invalid_content = False

        self.reprompt_count = {self.guesser: 0, self.answerer: 0}
        #self.history = []

        self.guess_word = None
        self.incorrect_guess = False
        self.correct_guess = False


    def _on_before_game(self):
        self.add_user_message(self.guesser, self.guesser_initial_prompt)

    def _does_game_proceed(self):

        for player, count in self.reprompt_count.items():
        # Check if the player has reached the max reprompts
            if count >= REPROMPT_LIMIT:
                # If there has been an invalid response after reaching the limit, stop the game
                if self.invalid_format or self.invalid_content:
                    self.log_to_self(f"max reprompts reached for player {player.descriptor}", "abort")
                    return False
                
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

        self.invalid_format = False  # Reset the flags at the beginning of validation
        self.invalid_content = False 

        if player == self.guesser:

            # Check if the response is neither a valid question nor a valid guess
            if not (utterance.startswith("QUESTION: ") or utterance.startswith("GUESS: ")):
                self.log_to_self("invalid format", "Invalid format. Guesser must use 'QUESTION: ' or 'GUESS: '.")
                self.invalid_format = True

                return False

            # Validate the question format
            if utterance.startswith("QUESTION: "):
                question_text = utterance[len("QUESTION: "):].strip()

                # Check if there is text after the question mark
                if "?" in question_text:
                    parts = question_text.split("?")
                    if len(parts) > 2 or parts[1].strip() != "":
                        self.log_to_self("invalid format", "Invalid format. Question must stop after the question mark.")
                        self.invalid_format = True
                        return False
                    
                # Check for specific invalid question formats
                errors = self.check_question(utterance, self.candidate_list)
                if errors:

                    # Log errors based on their type
                    for error in errors:
                        if error["type"] == 1:
                            self.log_to_self("invalid format", "Multiple questions detected in a single turn.")
                            self.invalid_format = True
                        elif error["type"] == 2:
                            self.log_to_self("invalid format", "Invalid question format.")
                            self.invalid_content = True
                        elif error["type"] == 3:
                            self.log_to_self("invalid content", "Invalid question format: Positional letter-based questions are forbidden.")
                            self.invalid_content = True
                        elif error["type"] == 4:
                            self.log_to_self("invalid content", "Invalid question format. Direct guessing of the target word is not allowed.")
                            self.invalid_content = True
                        elif error["type"] == 5:
                            self.log_to_self("invalid content", "Invalid question format. Asking length of the target word is not allowed.")
                            self.invalid_content = True
                        elif error["type"] == 6:
                            self.log_to_self("invalid content", "Invalid question format. Asking letters of the target word is not allowed.")
                            self.invalid_content = True
                        elif error["type"] == 7:
                            self.log_to_self("invalid content", "Invalid question format. Asking letters of the target word is not allowed.")
                            self.invalid_content = True
    
                    return False

                # If question format is valid, allow it
                return True

            # Validate the guess format

            elif utterance.startswith("GUESS: "):

                guess_word = utterance[len("GUESS: "):].strip().lower()
                guess_word = string_utils.remove_punctuation(guess_word)
                self.guess_word = guess_word

                # add invalid_format if the text after guess is more than a word

                if guess_word == self.target_word.lower():
                    self.correct_guess = True
                    self.log_to_self("correct guess", guess_word)
                else:
                    self.incorrect_guess = True
                    self.log_to_self("incorrect guess", guess_word)

                # If guess format is valid, allow it
                return True

        elif player == self.answerer:
            if utterance not in ["ANSWER: yes", "ANSWER: no", "ANSWER: Yes.", "ANSWER: Yes", "ANSWER: No.", "ANSWER: No"]:
                self.invalid_format = True
                return False
        return True

    def _on_before_reprompt(self, player: Player):

        self.reprompt_count[player] += 1

        if self.reprompt_count[player] <= REPROMPT_LIMIT:
            if player == self.guesser:
                new_prompt = self.guesser_reprompt
            else:
                new_prompt = self.answerer_reprompt
            self.add_user_message(player, new_prompt)

        else:
            self.log_to_self("max reprompts reached", "abort")
            return False

    def _should_reprompt(self, player: Player):
        return self.invalid_format or self.invalid_content and self.reprompt_count[player] < REPROMPT_LIMIT


    def _after_add_player_response(self, player: Player, utterance: str):
        
        #### THIS FUNCTION IS TO ADD THE PREVIOUS PLAYER'S MESSAGE TO THE CURRENT ONE, IT'S NOT NECESSARY IF THE RESPONSE IS INVALID IT WONT
        # CONTINUE THE GAME, IT WILL REPROMPT OR ABORT THE GAME: 
        
        # if self.invalid_response:
        #     return  # Do not proceed if the response was invalid

        if player == self.guesser:
            #self.history.append({"role": "guesser", "content": utterance})

            if self.current_turn == 0:
                prompt_with_first_question = f"{self.answerer_initial_prompt}\n\n{utterance}"
                self.add_user_message(
                    self.answerer, prompt_with_first_question)
            else:
                self.add_user_message(self.answerer, utterance)
        elif player == self.answerer:
            #self.history.append({"role": "answerer", "content": utterance})

            if not self.incorrect_guess and not self.correct_guess:
                self.add_user_message(self.guesser, utterance)


class GuessWhatScorer(GameScorer):
    
    def __init__(self, experiment: Dict, game_instance: Dict):
        super().__init__(GAME_NAME, experiment, game_instance)

    def compute_scores(self, episode_interactions: Dict) -> None:
        turn_scores = []
        # invalid_response = False  # Indicates whether any invalid responses were detected
        invalid_format_count = 0  # Counter for invalid format responses
        invalid_content_count = 0  # Counter for invalid content responses
        guesser_won = False
        max_turns = self.experiment["max_turns"]
        lower_bound_turns = math.log2(max_turns) + 1 ###### needs to be ajusted according to the levels
        reprompt_counts = { "guesser": 0, "answerer": 0 }

        speed_score = 0

        for turn_idx, turn in enumerate(episode_interactions["turns"]):

            turn_score = {"request_count": 1}

            for event in turn:
                action = event["action"]
                if action["type"] == "invalid format":
                    invalid_format_count += 1 
                if action["type"] == "invalid content":
                    invalid_content_count += 1
                # if action["type"] == "question":
                #     turn_score["question"] = action["content"]
                if action["type"] == "correct guess":
                    guesser_won = True

                # Add reprompt count
                if action["type"] == "send message (reprompt)":
                    if event["to"] == "Player 1":
                        reprompt_counts["guesser"] += 1
                    elif event["to"] == "Player 2":
                        reprompt_counts["answerer"] += 1
                    
            if invalid_format_count > 0 or invalid_content_count > 0:
                turn_score["violated_request_count"] = 1
                turn_score["parsed_request_count"] = 0
            else:
                turn_score["violated_request_count"] = 0
                turn_score["parsed_request_count"] = 1

            self.log_turn_score(turn_idx, 'Accuracy', 1 if guesser_won else 0)
            self.log_turn_score(turn_idx, METRIC_REQUEST_COUNT_VIOLATED, turn_score["violated_request_count"])
            self.log_turn_score(turn_idx, METRIC_REQUEST_COUNT_PARSED, turn_score["parsed_request_count"])
            self.log_turn_score(turn_idx, METRIC_REQUEST_COUNT, turn_score["request_count"])
            turn_scores.append(turn_score)

        violated_request_count = sum([turn["violated_request_count"] for turn in turn_scores])
        self.log_episode_score(METRIC_REQUEST_COUNT_VIOLATED, violated_request_count)

        parsed_request_count = sum([turn["parsed_request_count"] for turn in turn_scores])
        self.log_episode_score(METRIC_REQUEST_COUNT_PARSED, parsed_request_count)

        request_count = sum([turn["request_count"] for turn in turn_scores])
        self.log_episode_score(METRIC_REQUEST_COUNT, request_count)

        if request_count != 0:
            self.log_episode_score(METRIC_REQUEST_SUCCESS, parsed_request_count / request_count)
        else: 
            self.log_episode_score(METRIC_REQUEST_SUCCESS, 0)

        if (invalid_format_count > 0 or invalid_content_count > 0) and any(count >= REPROMPT_LIMIT for count in reprompt_counts.values()):
            self.log_episode_score(METRIC_ABORTED, 1)
            self.log_episode_score(BENCH_SCORE, np.nan)
        else:
            self.log_episode_score(METRIC_ABORTED, 0)
            if guesser_won:
                self.log_episode_score(METRIC_SUCCESS, 1)
                self.log_episode_score(METRIC_LOSE, 0)
                
                if request_count == lower_bound_turns:
                    self.log_episode_score("Speed", 100)
                else: 
                    speed_score = 100 * (max_turns - request_count) / (max_turns - lower_bound_turns)
                    
                self.log_episode_score("Speed", max(0, speed_score))
                
                # BENCH_SCORE = SPEED_SCORE - violated_request_count
                bench_score = max(0, speed_score - violated_request_count)
                self.log_episode_score(BENCH_SCORE, bench_score)

            else:
                self.log_episode_score(METRIC_SUCCESS, 0)
                self.log_episode_score(METRIC_LOSE, 1)
                self.log_episode_score(BENCH_SCORE, 0)

         # Log the reprompt counts for both players
        self.log_episode_score("Reprompt Guesser", reprompt_counts["guesser"])
        self.log_episode_score("Reprompt Answerer", reprompt_counts["answerer"])

         # Log the number of invalid format responses
        self.log_episode_score("Invalid format response", invalid_format_count)

        # Log the number of invalid content responses
        self.log_episode_score("Invalid content response", invalid_content_count)
                
class GuessWhatGameBenchmark(GameBenchmark):
    def __init__(self):
        super().__init__(GAME_NAME)

    def get_description(self):
        return "Guess What? game between two agents where one asks questions to guess the target word from list of candidates and the other answers with 'yes' or 'no'."

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



