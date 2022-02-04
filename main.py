import difflib
from matplotlib.colors import ListedColormap
import numpy as np
import random
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import math
from typing import List as list
from typing import List
import random as r


class Grid(object):
    def __init__(self, g: list[list[bool]], n, fitness=0):
        self.grid = g
        self.N = n
        self.fitness = fitness

    def get_grid(self):
        return self.grid

    def get_fitness_line_By_line(self, lines: list[list[bool]], rules: list[list[int]], rows_or_cols: str):
        fitness = 0
        for i, (line, rule) in enumerate(zip(lines, rules)):
            fitness += self.get_line_fitness(line, rule, i, rows_or_cols)
        return fitness

    def set_fitness(self, rows_rules: list[list[int]], cols_rules: list[list[int]]):
        grid_rows_fitness = self.get_fitness_line_By_line(self.grid, rows_rules, "row")
        grid_by_cols = zip(*self.grid)
        grid_cols_fitness = self.get_fitness_line_By_line(grid_by_cols, cols_rules, "cols")
        grid_fitness = grid_rows_fitness + grid_cols_fitness
        self.fitness = grid_fitness

    def get_fitness(self):
        return self.fitness

    # get fitness based on how close was the solution to the desired one
    def get_line_fitness(self, line: List[bool], line_rules: List[int], i: int, rows_or_cols: str):
        segments = get_segments(line)
        a = get_line_bits_difference_score(segments, line_rules, self.N)
        b = get_list_similarity(segments, line_rules)
        retval = a + b
        if retval >= 2:
            retval *= bonus_score
        return retval

    def improve_line(self, line: list[bool], rule: list[int]):
        segments = get_segments(line)
        # switch 1 bit
        if get_line_bits_difference_score(segments, rule) < 1:
            i = random.randrange(0, self.N)
            line[i] = not line[i]

        segments = get_segments(line)
        # replace 2 bits
        if get_list_similarity(segments, rule) < 1:
            i, j = random.randrange(0, self.N), random.randrange(0, self.N)
            line[i], line[j] = line[j], line[i]

    def improve(self, line_rules: list[list[int]]):
        for line, rule in zip(self.grid, line_rules):
            self.improve_line(line, rule)

    def copy(self):
        copied = []
        for g in self.grid:
            copied.append(g.copy())
        return Grid(copied, self.N, self.fitness)

    def mutate(self, p):
        for line in self.grid:
            for i in range(self.N):
                line[i] = random.choices([line[i], not line[i]], [p, 1 - p], k=1)[0]


def get_segments(line):
    segments = []
    segment_length = 0
    for square in line:
        if not square:  # if we're at 0
            if segment_length > 0:
                segments.append(segment_length)
                segment_length = 0
        else:
            segment_length += 1
    if segment_length > 0:
        segments.append(segment_length)
    return segments


def pad_or_truncate(some_list, target_len):
    return some_list[:target_len] + [0] * (target_len - len(some_list))


# returns similarity between 2 lists
def get_list_similarity(l1: List[int], l2: List[int]):
    # sm = difflib.SequenceMatcher(None, l1, l2)
    # grade_sequence = sm.ratio()
    if len(l1) > len(l2):
        l2 = pad_or_truncate(l2, len(l1))
    elif len(l1) < len(l2):
        l1 = pad_or_truncate(l1, len(l2))
    difference = 0
    for i, j in zip(l1, l2):
        difference += abs(i - j)
    sum_all = sum(l1) + sum(l2)
    grade_sequence = (sum_all - difference) / sum_all
    return grade_sequence


def get_sum_different(l1: list[int], l2: list[int]):
    a = abs(sum(l1) - sum(l2))
    return abs(sum(l1) - sum(l2))


def get_lists_sum_difference(segments: List[int], line_rules: List[int]):
    bits_on_difference = get_sum_different(line_rules, segments)
    return bits_on_difference


# returns fitness by bits similarity
def get_line_bits_difference_score(segments: List[int], line_rules: List[int], n: int = 10):
    bits_on_difference = get_lists_sum_difference(segments, line_rules)
    grade_bits = (n - bits_on_difference) / n
    return grade_bits


# returns txt file as array where each cell represent line
def get_lines_as_list(filename):
    with open(filename) as f:
        content = f.readlines()
    content = [x.strip() for x in content]
    return content


# takes string and return it as int_array splitted by separator
def from_string_to_int_array(string: str, separator: str):
    splitted = string.split(sep=separator)
    int_array = []
    for s in splitted:
        int_array.append(int(s))
    return int_array


# takes string array and return integers matrix out of it
def from_string_array_to_int_matrix(string_array: list[str]):
    int_matrix = []
    for string in string_array:
        int_matrix.append(from_string_to_int_array(string, " "))
    return int_matrix


# assuming the number is even (means we can split it for half)
# also assume the file is legal and that the matrix is squared (len(rows) = len(cols))
def get_rows_cols_from_txt_file(filename: str):
    content = from_string_array_to_int_matrix(get_lines_as_list(filename))
    cols = content[:len(content) // 2]
    rows = content[len(content) // 2:]
    return rows, cols


def init_grid(N: int, p: float):
    return np.random.choice(a=[False, True], size=(N, N), p=[p, 1 - p]).tolist()


# returns array of lines according to their probability
def display_each_value_by_probability(grids: list[Grid]):
    arr = []
    probabilities = dict()
    # get total sum of all grades
    total_sum = 0
    for grid in grids:
        if grid.get_fitness() == 0:
            i = 1
        total_sum += grid.get_fitness()

    for grid in grids:
        probability = (grid.get_fitness() / total_sum) * 100
        probabilities[grid] = int(math.ceil(probability))  # rounded
    for grid, probability in probabilities.items():
        for i in range(probability):
            arr.insert(0, grid)
    return arr


def display_each_value_by_probability2(grids: list[Grid]):
    arr = []
    sum = 0
    for grid in grids:
        for i in range(0, int(grid.get_fitness())):
            arr.append(grid)
    return arr


# generates child from parents details
def cross_over(parent1: Grid, parent2: Grid, N: int):
    grid_size = N*N  # N*N
    place_to_cut_grid = random.randrange(0, grid_size)
    parent1_grid: list[bool] = []

    for line in parent1.get_grid():
        for cell in line:
            parent1_grid.append(cell)
    parent2_grid: list[bool] = []
    for line in parent2.get_grid():
        for cell in line:
            parent2_grid.append(cell)

    if place_to_cut_grid % N == 0:
        new_child = Grid(parent1.get_grid(), N)
    else:
        place_to_cut_line = place_to_cut_grid
        place_of_broken_line = N - place_to_cut_grid #!!!!!!!!!!!!!!!!
        broken_line: list[bool] = parent1_grid[:place_to_cut_line] \
                                  + parent2_grid[place_to_cut_line:]

        new_broken_line : list[list[bool]] = []
        for i in range (0,N):
            first = i * N
            last = first + N
            new_broken_line.append(broken_line[first:last])

        new_child = Grid(new_broken_line,N)
    new_child.mutate(p=mutate_p)
    return new_child

def elitism (grids: list[Grid], len: int):
    list_of_best: list[Grid] = []
    for i in range(0, len):
        list_of_best.append(grids[i])
    list_of_best.sort(key=lambda x: x.fitness)
    for grid in grids:
        if grid.get_fitness() > list_of_best[0].get_fitness():
            list_of_best.pop(0)
            list_of_best.append(grid)
            list_of_best.sort(key=lambda x: x.fitness)
    return list_of_best


# return new grid after changing it
def prepare_next_generation(grids: list[Grid], N: int):
    new_grids = []
    # arr = display_each_value_by_probability(grids)
    arr = display_each_value_by_probability2(grids)
    best_grids = elitism(grids, 10)  # save the best 10 grids
    best_grids_copy = best_grids.copy()

    for grid in grids:
        for best in best_grids:
            if best == grid:
                best_grids.remove(best)
                grids.remove(grid)

    for _ in range(len(grids)):
        grid_parent1: Grid = random.choice(arr)
        grid_parent2: Grid = random.choice(arr)
        new_grids.append(cross_over(grid_parent1, grid_parent2, N))

    length = int(len(best_grids_copy) - len(best_grids))
    i = 0
    for grid in best_grids_copy:
        if i >= length:
            break
        new_grids.append(grid)
        i += 1

    return new_grids


# sets fitness for each grid based on rules given
def calculate_fitness_for_each_grid(grids: list[Grid], rows_rules: list[list[int]], cols_rules: list[list[int]]):
    best_grid: Grid = grids[0]  # init best
    worst_grid: Grid = grids[0]  # init worst
    for grid in grids:
        grid.set_fitness(rows_rules, cols_rules)  # so each grid will have grade calculated
        if grid.get_fitness() > best_grid.get_fitness():
            best_grid = grid
    for grid in grids:
        grid.set_fitness(rows_rules, cols_rules)  # so each grid will have grade calculated
        if grid.get_fitness() < worst_grid.get_fitness():
            worst_grid = grid
    return best_grid, worst_grid


def check_if_early_convergence(grids: list[Grid]):
    fitness = grids[0].get_fitness()
    size = int(len(grids))
    tenth_size = int(len(grids)/10)
    j = 0
    for i in range(0, tenth_size):
        j = r.randint(0, size - 1)
        if fitness != grids[j].get_fitness():
            return False
    return True


current_gen_girds: list[Grid] = []
best_grid_all_gen: Grid = None
worst_grid_all_gen: Grid = None
population_size = 200
total_frames = 0
inherit_after_improvement = False
bonus_score = 1.5
ani: animation.FuncAnimation
mutate_p = 0.1


# simulates life cycle
def life_cycle(frameNum, img, N: int, rows_rules: list[list[int]], cols_rules: list[list[int]],
               best_possible_grade: int):
    global current_gen_girds, best_grid_all_gen, worst_grid_all_gen, total_frames
    total_frames += 1

    not_improved_grids: list[Grid] = []
    # improve each grid by rows
    for grid in current_gen_girds:
        not_improved_grids.append(grid.copy())
        grid.improve(line_rules=rows_rules)

    # calculate_fitness_for_each_grid(not_improved_grids, rows_rules, cols_rules)

    # get best grid
    best_grid_current_gen, worst_grid_all_gen = calculate_fitness_for_each_grid(current_gen_girds, rows_rules, cols_rules)
    if check_if_early_convergence(current_gen_girds):
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


    if best_grid_current_gen.get_fitness() > best_grid_all_gen.get_fitness():
        # if we got better grid, lets notify user and put it as the img
        best_grid_all_gen = best_grid_current_gen.copy()
    img.set_data(best_grid_all_gen.get_grid())
    percent_done = (best_grid_all_gen.get_fitness() / best_possible_grade) * 100
    print('best %.2f' % best_grid_current_gen.get_fitness(),
          'worst %.2f' % worst_grid_all_gen.get_fitness(), "| frame number %4d" % total_frames,
          "| %.2f%% done" % percent_done)
    # is it perfect score?
    if best_grid_all_gen.get_fitness() >= best_possible_grade:
        print('this is the best you will get')
        ani.event_source.stop()  # stop because there is no reason to continue

    # notify user 200 frames has passed
    if total_frames % 200 == 0:
        print("--------frame number %4d--------" % total_frames)

    generation_to_inherit: list[Grid] = not_improved_grids
    if inherit_after_improvement:
        generation_to_inherit = current_gen_girds

    for grid in generation_to_inherit: #!!!!!!!!!!!!
        grid.set_fitness(rows_rules, cols_rules)

    current_gen_girds = prepare_next_generation(generation_to_inherit, N)

    return img



def main():
    global current_gen_girds, best_grid_all_gen, worst_grid_all_gen, ani
    rows, cols = get_rows_cols_from_txt_file("5x5_1.txt")
    N = len(cols)  # since every1 is square
    for _ in range(population_size):
        current_gen_girds.append(Grid(init_grid(N=N, p=0.5), N))
    best_grid_all_gen = current_gen_girds[0]  # init best grid
    worst_grid_all_gen = current_gen_girds[0]  # init worst grid
    best_possible_score = (2 * bonus_score) * (N * 2)
    figure, axes = plt.subplots()
    cmap = ListedColormap(['w', 'k'])
    img = axes.imshow(current_gen_girds[0].get_grid(), interpolation='nearest', cmap=cmap)
    ani = animation.FuncAnimation(figure,
                                  func=life_cycle,
                                  fargs=(img, N, rows, cols, best_possible_score),
                                  frames=10,
                                  interval=10,  # millisecond to interval
                                  save_count=50,
                                  repeat=True)
    plt.show()


if __name__ == '__main__':
    main()