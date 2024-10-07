# General Sensors and Actions (Given by default to every creature)

-   Eating
-   Change direction
-   Move in direction

# Sensors

-   Nearest food location
-   Nearest food direction
-   Nearest home location
-   Nearest home direction
-   Current Energy
-   Number of agents trying to eat the nearest food
-   Nearest Carnivorous creatures
-   Nearest Creature
-   Target food speed

# Actions

-   Increase speed (uses more energy)
-   Increase Size (uses more energy, defends from smaller carnivores, passive)
-   Lower energy consumption
-   Eat other creatures
-   Reproduction


# Logs

```
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
 20220201   19.052    0.000   19.052    0.000 {method 'reduce' of 'numpy.ufunc' objects}
   105105   17.280    0.000   50.413    0.000 config.py:96(obs_Nfd)
    97097   15.727    0.000   46.337    0.000 config.py:85(obs_Nfl)
 20220200   14.044    0.000   35.427    0.000 fromnumeric.py:69(_wrapreduction)
 40440479   13.403    0.000   13.403    0.000 {built-in method numpy.array}
 20220200   11.404    0.000   48.751    0.000 fromnumeric.py:2255(sum)
 20220679    2.330    0.000    2.330    0.000 {method 'items' of 'dict' objects}
        2    2.000    1.000    2.000    1.000 {built-in method time.sleep}
20339524/20338572    1.934    0.000    1.935    0.000 {built-in method builtins.isinstance}
 20220200    1.357    0.000    1.357    0.000 fromnumeric.py:2250(_sum_dispatcher)
     1002    0.760    0.001    0.760    0.001 {built-in method pygame.display.update}
        1    0.505    0.505    0.506    0.506 {built-in method pygame.display.set_mode}
   100100    0.404    0.000   97.875    0.001 main.py:242(get_observation)
```