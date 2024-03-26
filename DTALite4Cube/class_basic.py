from user_input import iteration, route, simu, UE_converge, length, speed

# Define the basics as dictionaries
assignment = {
    'assignment': {
        'number_of_iterations': iteration,
        'route_output': route,
        'simulation_output': simu,
        'UE_convergence_percentage': UE_converge
    }
}

cpu = {
    'cpu': {
        'number_of_memory_blocks': 1
    }
}

unit = {
        'unit': {
            'length_unit': length,
            'speed_unit': speed
    }       
}

# Add the basic dictionaries into a single basic dictionary
basic_dict = {}
basic_dict.update(assignment)
basic_dict.update(cpu)
basic_dict.update(unit)
