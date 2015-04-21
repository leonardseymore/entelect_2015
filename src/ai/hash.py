import ai.entelect


def hash_game_encode(game_state):
    game_map = game_state['Map']
    hash_str = ''
    running_length = 0
    running_symbol = None
    for column_index in range(1, 24):
        for row_index in range(1, 18):
            cell = game_map['Rows'][column_index][row_index]
            symbol = ai.entelect.cell_to_symbol(cell)

            if symbol == ' ':
                symbol = 'S'

            if not running_symbol:
                running_symbol = symbol
            elif not running_symbol == symbol:
                if running_length == 1:
                    hash_str += running_symbol
                else:
                    hash_str += running_symbol + str(running_length)
                running_symbol = symbol
                running_length = 0
            running_length += 1
    hash_str += symbol + str(running_length)

    hash_str += '_'
    hash_str += str(game_state['Players'][0]['AlienManager']['DeltaX'])
    hash_str += str(game_state['Players'][1]['AlienManager']['DeltaX'])
    return hash_str


