from src.lambda_function import (
    lambda_handler,
    get_team_info,
    generate_json,
    write_to_s3,
    get_todays_game_information,
    get_yesterdays_game_information,
    get_win_status
)

####################
# get_win_status
####################
def test_get_win_status_is_won():
    assert get_win_status('rays', 'rays') == "won"

def test_get_win_status_is_lost():
    assert get_win_status('red sox', 'rays') == "lost"
