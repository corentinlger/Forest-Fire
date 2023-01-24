import sys
import pygame
import pygame.draw
import numpy as np
from matplotlib import pyplot as plt

__screenSize__ = (1280,1280) #(900,900)
__cellSize__ = 10 
__gridDim__ = tuple(map(lambda x: int(x/__cellSize__), __screenSize__))
__density__ = 3
__colors__ = [(255,255,255),(0,175,0),(0,215,0), (200,100,0),(150,30,0),(100,0,0), (125,38,205),(0,60,255), (155,48,255)]
#            [    Terre       Arbre     Arbre2       Feu 1       Feu2     Cendres   Pompier   Eau      Canadair ]


def getColorCell(n):
    return __colors__[n]


class Grid:
    _grid= None
    _gridbis = None
    _indexVoisins = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    
    def __init__(self):
        print("Creating a grid of dimensions " + str(__gridDim__))
        self._grid = np.zeros(__gridDim__, dtype='int8')
        self._gridbis = np.zeros(__gridDim__, dtype='int8')
        nx, ny = __gridDim__
        tree_dens = 0.5
        self._grid = self.initialize_forest(tree_density=tree_dens)
        self.initial_trees = tree_dens * nx * ny
        self.tree_dens = tree_dens
        # Initialiser du feu
        #self.initialize_type_random_pos(3, nx, ny)
        # Initialiser 50 feux randoms
        for i in range(5):
            self.initialize_type_random_pos(3, nx, ny)

    def initialize_type_random_pos(self, type, nx, ny):
        pos = (np.random.randint(0,nx), np.random.randint(0,ny))
        print(f"Initial {type} at coordinates : {[pos]}")
        self._grid[pos] = type

    def initialize_forest(self, tree_density=0.50):
        forest = np.random.choice([0, 1], size=__gridDim__, p=[1 - tree_density, tree_density])
        print(f"Initializing a forest with {tree_density}% of trees")
        return forest

    # Les 4 fonctions ci-dessous nous permettent de calculer pour chaque pixel le nombre de voisin d'un certain type
    # Cela va nous permettre d'avoir accès au nombre de de voisins en feu mais aussi au nombre de voisins qui sont des arbres
    def indiceVoisinsType(self, type, x,y):
        return [(dx+x,dy+y) for (dx,dy) in self._indexVoisins if dx+x >=0 and dx+x < __gridDim__[0] and dy+y>=0 and dy+y < __gridDim__[1] and self._grid[dx+x,dy+y]==type]

    def voisinsType(self, type, x,y):
        return [self._grid[vx,vy] for (vx,vy) in self.indiceVoisinsType(type, x,y)]
    
    def sommeVoisinsType(self, type, x, y):
        return sum(self.voisinsType(type, x,y))

    def sumEnumerateType(self, type):
        return [(c, self.sommeVoisinsType(type, c[0], c[1])) for c, _ in np.ndenumerate(self._grid)]

    def drawMe(self):
        pass

class Scene:
    _mouseCoords = (0,0)
    _grid = None
    _font = None

    def __init__(self):
        pygame.init()
        self._screen = pygame.display.set_mode(__screenSize__)
        self._font = pygame.font.SysFont('Arial', 25)
        self._grid = Grid()
        # On initialise un compteur avec le nombre d'arbres pour pouvoir voir l'évolution au cours du temps
        self.trees = self._grid.initial_trees
        # Meme chose pour les arbres brûlés
        self.burnt_trees = 0
        self.tree_dens = self._grid.tree_dens
        # On initialise aléatoirement les coordonnées des pompiers et du camion
        self.fire_fighters_coords = self.create_firefighters(nb_fire_fighters=8)
        self.fire_fighter_truck_coords = (np.random.randint(0, __gridDim__[0]), np.random.randint(0, __gridDim__[1]))
        # On initialise ensuite les portées des canons du pompier et du camion
        self.fire_fighter_water_range = self.create_water_range(water_range=5)
        self.fire_fighter_truck_water_range = self.create_water_range(water_range=11)

    # Fonction pour créer une zone de portée de lance à incendie
    def create_water_range(self, water_range = 5):
        area_covered = []
        for i in range(-water_range,water_range+1):
            for j in range(-water_range,water_range+1):
                area_covered.append((i,j))
        return area_covered

    # Fonction pour créer un X pompiers
    def create_firefighters(self, nb_fire_fighters=1):
        fire_fighters_army = []
        for i in range(nb_fire_fighters):
            fire_fighter_coords = (np.random.randint(0, __gridDim__[0]), np.random.randint(0, __gridDim__[1]))
            fire_fighters_army.append(fire_fighter_coords)
        return fire_fighters_army

    def drawMe(self):
        if self._grid._grid is None:
            return
        self._screen.fill((255,255,255))
        # On dessine d'abord la carte
        for x in range(__gridDim__[0]):
            for y in range(__gridDim__[1]):
                color = getColorCell(self._grid._grid.item((x,y)))
                pygame.draw.rect(self._screen, color, (x*__cellSize__ + 1,
                                      y*__cellSize__ + 1, __cellSize__-2, __cellSize__-2))
        # Puis on dessine les pompiers et le camion par dessus
        for coords in self.fire_fighters_coords:
            pygame.draw.rect(self._screen, getColorCell(6), (coords[0] * __cellSize__ + 1,
                                                   coords[1] * __cellSize__ + 1, __cellSize__ - 2, __cellSize__ - 2))
        # Pour le camion, on le représente par un cube de 3 pixels sur 3 pour lel rendre plus visible
        for dx in range(-1,2):
            for dy in range(-1,2):
                pygame.draw.rect(self._screen, getColorCell(6), ((self.fire_fighter_truck_coords[0]+dx) * __cellSize__ + 1,
                                                                 (self.fire_fighter_truck_coords[1]+dy) * __cellSize__ + 1, __cellSize__ - 2,
                                                         __cellSize__ - 2))


        #self.drawText("Save the forest", (20,20))

    def drawText(self, text, position, color = (255,64,64)):
        self._screen.blit(self._font.render(text,1,color),position)


    def update_map(self):
        # On copie la grille pour ne pas avoir à modifier les éléments qui ne changent pas dans les règles
        self._grid._gridbis = np.copy(self._grid._grid)

        ## Forest Update ##
        # On crée une règle qui fait que les arbes ont plus de chance de repousser sur une case vide si
        # ils ont plusieurs voisins arbres
        for c, s in self._grid.sumEnumerateType(1):
            # Si on est de la terre (type = 0)
            if self._grid._grid [c[0],c[1]] == 0:
                # La proba de devenir un arbre est de nb_voisins_arbres * 0.05
                p_becoming_tree = 0.0001 + s*0.0005
                if p_becoming_tree > np.random.uniform(0,1) :
                    # On devient une jeune pousse
                    self._grid._gridbis[c[0], c[1]] = 2
                    # On incrémente le compteur d'arbres
                    self.trees += 1
            # Si on était une jeune pousse au tour précédent, on devient un arbre
            if self._grid._grid[c[0],c[1]] == 2:
                self._grid._gridbis[c[0],c[1]] = 1

        ## Fire Update ##
        # Si on est un arbre et qu'on a un voisin en feu on devient en feu également
        for c, s in self._grid.sumEnumerateType(3):
            if (s > 0) and self._grid._grid[c[0], c[1]] == 1:  # Si arbres et voisin feu alors arbre --> feu
                self._grid._gridbis[c[0], c[1]] = 3

        # La même règle s'applique pour le feu nv 2
        for c, s in self._grid.sumEnumerateType(4):
            if (s > 0) and self._grid._grid[c[0], c[1]] == 1:  # Si arbres et voisin feu alors arbre --> feu
                self._grid._gridbis[c[0], c[1]] = 3

            # S'occupe de montrer que l'arbre brûle pdt 3 tours et disparaît
            for i in range(3, 6):
                if i != 5:
                    if self._grid._grid[c[0], c[1]] == i:
                        self._grid._gridbis[c[0], c[1]] = i + 1
                # Dernière étape où l'arbre est en cendre, il disparait au prochain tour
                else:
                    if self._grid._grid[c[0], c[1]] == i:
                        self._grid._gridbis[c[0], c[1]] = 0
                        self.burnt_trees += 1
                        self.trees -= 1
        ## Canadair Update ##

        ## Fire Fighter Update ##
        for (x, y) in self.fire_fighters_coords:
            for dx, dy in self.fire_fighter_water_range:
                # On regarde les cases autour de nos pompiers : si elles sont en feu, ou bien vont l'être, elles se transforment en eau
                if dx+x >=0 and dx+x < __gridDim__[0] and dy+y>=0 and dy+y < __gridDim__[1] and self._grid._grid[x + dx, y + dy] in [3, 4]:
                    # On transforme le feu en eau
                    self._grid._gridbis[x + dx, y + dy] = 7
                elif dx+x >=0 and dx+x < __gridDim__[0] and dy+y>=0 and dy+y < __gridDim__[1] and self._grid._gridbis[x + dx, y + dy] == 3:
                    # On transforme le feu en eau
                    self._grid._gridbis[x + dx, y + dy] = 7
        ### Camion de pompiers ###
        (x,y) = self.fire_fighter_truck_coords
        for dx, dy in self.fire_fighter_water_range :
            if dx + x >= 0 and dx + x < __gridDim__[0] and dy + y >= 0 and dy + y < __gridDim__[1] and self._grid._grid[
                x + dx, y + dy] in [3, 4]:
                # On transforme le feu en eau
                self._grid._gridbis[x + dx, y + dy] = 7
            elif dx + x >= 0 and dx + x < __gridDim__[0] and dy + y >= 0 and dy + y < __gridDim__[1] and \
                    self._grid._gridbis[x + dx, y + dy] == 3:
                # On transforme le feu en eau
                self._grid._gridbis[x + dx, y + dy] = 7

        # Eau se retransforme en terre
        for c, _ in np.ndenumerate(self._grid._grid):
            if self._grid._grid[c[0], c[1]] == 7:
                self._grid._gridbis[c[0], c[1]] = 0

        self._grid._grid = np.copy(self._grid._gridbis)

    # Fonction qui permet aux pompiers (camion compris) de trouver le feu le plus proche
    def find_closest_fire(self, x, y, grid_fire):
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]
        if grid_fire[x][y] in [3, 4]:
            return x, y
        for i in range(1, len(grid_fire[0])):
            for dx, dy in directions:
                # print(f"dx dy : {dx, dy}")
                if (x + i * dx) >= 0 and (x + i * dx) < __gridDim__[0] and (y + i * dy) >= 0 and (y + i * dy) < __gridDim__[1]:
                    if grid_fire[x + i * dx][y + i * dy] in [3, 4]:
                        return x+2*dx, y+2*dy
        # Quand le feu est trouvé, on retourne les coordonnées d'un déplacement de 2 dans la direction trouvée
        return x, y

    # On applique la fonction précédente sur la liste de pompiers que l'on a créé
    def find_closest_fire_per_firefighter(self, grid_fire):
        moves_list = []
        for (x,y) in self.fire_fighters_coords :
            print(f"x y : {x, y}")
            moves_list.append(self.find_closest_fire(x,y,grid_fire))
        print(f"moves list : {moves_list}")
        return moves_list

    # On déplace la liste de pompiers dans leurs nouvelles coordonnées
    def move_firefighters(self, moves_list):
        for i, moves in enumerate(moves_list):
            self.fire_fighters_coords[i] = moves
        return None

    # on déplace le camion de la même manière
    def move_truck(self, move_truck):
        self.fire_fighter_truck_coords = move_truck
        return None
           
            
    def eventClic(self, coord, b):
        pass

    def recordMouseMove(self, coord):
        pass
    
    

def main():
    scene = Scene()
    done = False
    clock = pygame.time.Clock()
    count= 0

    # On initialise des listes pour stocker le nombre d'arbres à chaque itération
    nb_trees = []
    nb_burnt_trees = []
    while count < 1000:
        count +=1
        scene.drawMe()
        pygame.display.flip()
        scene.update_map()
        # On obtient les nouvelles cordonnées pour les pompiers
        moves_list = scene.find_closest_fire_per_firefighter(scene._grid._grid)
        move_truck = scene.find_closest_fire( scene.fire_fighter_truck_coords[0],scene.fire_fighter_truck_coords[1], scene._grid._grid)
        # On les déplace
        scene.move_firefighters(moves_list)
        scene.move_truck(move_truck)
        clock.tick(20)
        # On actualise les compteurs de nombre d'arbres
        nb_trees.append(scene.trees)
        nb_burnt_trees.append(scene.burnt_trees)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                print("Exiting")
                done=True

    pygame.quit()

# Code utilisé pour obtenir les graphiques sur le nombre d'arbres brûlés par rapport à la densité initiale d'arbres
"""
    print(f'Iteration number :  {count}')
    print(f"Initial number of trees : {scene.initial_trees}")
    print(f"Number of burnt trees : {scene.burnt_trees}")
    print(f"Number of Remaining trees : {scene.trees}")

    x = np.linspace(start=0, stop=count, num= count)
    plt.figure()
    plt.plot(x, nb_trees, label='Nb trees')
    # plt.plot(x, nb_burnt_trees, label='Nb burnt trees')
    plt.legend()
    plt.ylim(0, scene.nb_trees[0])
    plt.xlim(0, 200)
    plt.xlabel('Number of Iterations')
    plt.ylabel('Trees number')
    plt.title(f"Evolution of trees number with initial density = {scene.tree_dens}")
    plt.show()

"""

if not sys.flags.interactive: main()

