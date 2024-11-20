from typing import List
import matplotlib.pyplot as plt
from collections import defaultdict


class PopulationPlot:
    def __init__(self, creature_types, y_max=150):
        """
        Initialize the PopulationPlot class.

        Parameters:
            creature_types (list): List of creature types to track.
            y_max (int): Maximum y-axis value for population.
        """
        self.creature_types = creature_types
        self.data = defaultdict(list)  # Stores population data for each creature type
        self.time_data = []  # Tracks the timesteps (acts as "time")

        # Set up the figure and axis
        self.fig, self.ax = plt.subplots()
        self.ax.set_ylim(0, y_max)
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Population")
        self.ax.set_title("Population of Each Creature Type Over Time")

        # Initialize lines for each creature type
        self.lines = {}
        for creature in creature_types:
            (self.lines[creature],) = self.ax.plot([], [], lw=2, label=creature)

        # Add legend
        self.ax.legend()

        # Display the plot without blocking
        plt.show(block=False)

    def update_population(self, timestep: int, new_data: dict):
        """
        Update the plot with the latest population data for each creature type.

        Parameters:
            timestep (int): Current time or event count.
            new_data (dict): A dictionary where keys are creature types and values are their populations.
                             Example: {'Herbivore': 50, 'Carnivore': 30, 'Omnivore': 20}
        """
        # Track the timestep
        self.time_data.append(timestep)

        # Update the data for each creature type
        for creature, line in self.lines.items():
            self.data[creature].append(
                new_data.get(creature, 0)
            )  # Default to 0 if creature not in new_data

            # Update the line data
            line.set_data(self.time_data, self.data[creature])

        # Adjust x-axis limits to include all timesteps
        self.ax.set_xlim(0, max(self.time_data))

        # Redraw the plot with the updated data
        plt.draw()
        plt.pause(0.01)  # Small pause to allow the plot to update smoothly