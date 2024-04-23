import logging


class DtaBasics:
    def __init__(self, iteration=1, route=0, simu=0, ue_converge=0.1, length='meter', speed='mph', memory_blocks=1):

        if not isinstance(iteration, int) or iteration < 1:
            logging.warning("Invalid value for 'iteration', using default value (20)")
            iteration = 20

        if route not in {0, 1}:
            logging.warning("Invalid value for 'route', using default value (0)")
            route = 0

        if simu not in {0, 1}:
            logging.warning("Invalid value for 'simu', using default value (0)")
            simu = 0

        if not isinstance(ue_converge, float) or not (0 < ue_converge < 1):
            logging.warning("Invalid value for 'UE_converge', using default value (0.1)")
            ue_converge = 0.1

        if length not in {'meter', 'km', 'mile'}:
            logging.warning("Invalid value for 'length', using default value ('meter')")
            length = 'meter'

        if speed not in {'mph', 'kph'}:
            logging.warning("Invalid value for 'speed', using default value ('mph')")
            speed = 'mph'

        if not isinstance(memory_blocks, int) or memory_blocks < 1:
            logging.warning("Invalid value for 'memory_blocks', using default value (1)")
            memory_blocks = 1

        self.assignment = {
            'number_of_iterations': iteration,
            'route_output': route,
            'simulation_output': simu,
            'UE_convergence_percentage': ue_converge
        }

        self.cpu = {
            'number_of_memory_blocks': memory_blocks
        }

        self.unit = {
            'length_unit': length,
            'speed_unit': speed
        }
