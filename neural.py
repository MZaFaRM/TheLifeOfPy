import numpy as np
import agents


class OrganismNN:
    def __init__(self, input_size, hidden_size, output_size):
        # Randomly initialize weights for the neural network
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.weights_input_hidden = np.random.uniform(
            -1, 1, (self.input_size, self.hidden_size)
        )
        self.weights_hidden_output = np.random.uniform(
            -1, 1, (self.hidden_size, self.output_size)
        )
        self.bias_hidden = np.random.uniform(-1, 1, self.hidden_size)
        self.bias_output = np.random.uniform(-1, 1, self.output_size)

    def get_best_action(self, inputs):
        output = self.forward(inputs)
        best_action = np.argmax(output)
        return best_action

    def forward(self, inputs):
        # Forward pass through the network
        hidden = np.tanh(np.dot(inputs, self.weights_input_hidden)) + self.bias_hidden
        output = np.tanh(np.dot(hidden, self.weights_hidden_output)) + self.bias_output
        return output

    def get_weights(self):
        # Retrieve weights and biases as a single flattened array
        return np.concatenate(
            (
                self.weights_input_hidden.flatten(),
                self.weights_hidden_output.flatten(),
                self.bias_hidden.flatten(),
                self.bias_output.flatten(),
            )
        )

    def set_weights(self, weight_array):
        # Set weights and biases from a single flattened array
        input_size, hidden_size, output_size = (
            self.input_size,
            self.hidden_size,
            self.output_size,
        )
        input_hidden_size = input_size * hidden_size
        hidden_output_size = hidden_size * output_size
        bias_hidden_size = hidden_size
        bias_output_size = output_size

        self.weights_input_hidden = weight_array[:input_hidden_size].reshape(
            input_size, hidden_size
        )
        self.weights_hidden_output = weight_array[
            input_hidden_size : input_hidden_size + hidden_output_size
        ].reshape(hidden_size, output_size)
        self.bias_hidden = weight_array[
            input_hidden_size
            + hidden_output_size : input_hidden_size
            + hidden_output_size
            + bias_hidden_size
        ]
        self.bias_output = weight_array[
            input_hidden_size + hidden_output_size + bias_hidden_size :
        ]


# Implement Genetic Algorithm functions
def crossover(parent1, parent2):
    """Crossover operation to combine weights from two parents."""
    split = np.random.randint(0, len(parent1))
    child1 = np.concatenate((parent1[:split], parent2[split:]))
    child2 = np.concatenate((parent2[:split], parent1[split:]))
    return child1, child2


def mutate(weights, mutation_rate=0.01):
    """Apply random mutations to the weights."""
    for i in range(len(weights)):
        if np.random.rand() < mutation_rate:
            weights[i] += np.random.uniform(-1, 1) * 0.1  # Random mutation
    return weights


# Example fitness function (for demonstration)
def fitness_function(creature):
    # Define your custom fitness metric
    return creature.time_alive
