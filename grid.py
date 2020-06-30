#!/usr/bin/env python

import h5py
import numpy as np
import sys

# Node class

class Node:

    def __init__ (self, filename):

        self.filename = filename

        # Read data from file

        f = h5py.File(filename, 'r')

        self.Teff = f.attrs['Teff']
        self.logg = f.attrs['logg']

        self.data = f['data'][...]

        f.close()

# Grid class

class Grid:

    def __init__ (self, filenames, debug=False):

        # Sanity check

        if len(filenames) == 0:
            raise Exception('Empty grid')

        # Read nodes

        nodes_list = np.empty_like(filenames, dtype=object)

        for i, filename in enumerate(filenames):
            nodes_list[i] = Node(filename)

        # Extract axes

        self.Teff_axis = np.unique([node.Teff for node in nodes_list])
        self.logg_axis = np.unique([node.logg for node in nodes_list])

        self.n_Teff = len(self.Teff_axis)
        self.n_logg = len(self.logg_axis)

        # Set up the 2-D (Teff,logg) node array

        self.nodes = np.empty([self.n_Teff,self.n_logg], dtype=object)

        for node in nodes_list:

            # Find where the node belongs in the list

            i_Teff = np.where(node.Teff == self.Teff_axis)[0][0]
            i_logg = np.where(node.logg == self.logg_axis)[0][0]

            self.nodes[i_Teff,i_logg] = node

        # Set up the 2-D (Teff,logg) neighbors array
        
        self.neighbors = np.empty((self.n_Teff,self.n_logg), dtype=np.ndarray)
        
        for i_logg in range(self.n_logg):
            
            for i_Teff in range(self.n_Teff):
                
                # Identify node neighbors
                
                self.neighbors[i_Teff,i_logg] = self.find_neighbors((i_Teff,i_logg))

        # Set the debug flag

        self.debug = debug

            
    def lookup (self, Teff, logg):

        if Teff in self.Teff_axis and logg in self.logg_axis:

            # Find location in array

            i_Teff = np.where(Teff == self.Teff_axis)[0][0]
            i_logg = np.where(logg == self.logg_axis)[0][0]

            # Return the node if it exists

            node = self.nodes[i_Teff,i_logg]
            
            if isinstance(node, Node):
                return node
            else:
                return None

        else:

            return None
        

    def show_topology (self):

        for i_logg in range(self.n_logg):

            for i_Teff in range(self.n_Teff):

                if isinstance(self.nodes[i_Teff,i_logg], Node):
                    print("X", end=' ')
                else:
                    print(".", end=' ')

            print()
            print()
            

    def locate (self, Teff, logg):
        
        # First check Teff, logg within grid

        if (Teff < self.Teff_axis[0]) or (Teff > self.Teff_axis[-1]):
            raise IndexError(f'Teff={Teff} outside axis range')
        if (logg < self.logg_axis[0]) or (logg > self.logg_axis[-1]):
            raise IndexError(f'logg={logg} outside axis range')

        # Find indices

        def locate_x (x, x_axis):

            # Use bisection to find i such that
            # x_axis[k] <= x < x_axis[k+1].

            # Special case if x == x_axis[-1]

            if x == x_axis[0]:

                k = 0

            elif x == x_axis[-1]:

                k = len(x_axis) - 2

            else:

                k_0 = -1
                k_1 = len(x_axis)

                while (k_1 - k_0) > 1:
    
                    k = (k_0 + k_1)//2

                    if x >= x_axis[k]:
                        k_0 = k
                    else:
                        k_1 = k

                k = k_0

            return k

        i = locate_x(Teff, self.Teff_axis)
        j = locate_x(logg, self.logg_axis)

        # Return tuple (i,j) if all is well

        if self.debug:
            print(f'\nLocated grid point (i,j)=({i},{j}) such that \n')
            print(f'Teff_axis[i]={self.Teff_axis[i]}  <=  Teff={Teff}  <  Teff_axis[i+1]={self.Teff_axis[i+1]}')
            print(f'logg_axis[j]={self.logg_axis[j]}  <=  logg={logg}  <  logg_axis[j+1]={self.logg_axis[j+1]}\n')

        return (i,j)


    def find_neighbors (self, ij, show=False):
        
        stencil = np.zeros([3,3], dtype=bool)
        
        # Find where node has neighbors
        
        for k in range(-1,2):
            
            for h in range(-1,2):
                
                j_Teff = ij[0] + h
                j_logg = ij[1] + k
                
                # if neighbor exists, store True in bool stencil
                
                if ((0 <= j_Teff) and (j_Teff < self.n_Teff)) and \
                ((0 <= j_logg) and (j_logg < self.n_logg)):
                
                    if isinstance(self.nodes[j_Teff,j_logg], Node):
                        if show==True: print("X", end=' ')
                        stencil[h+1, k+1] = True
                    else:
                        if show==True: print(".", end=' ')
                    
            if show==True:    
                print()
                print()
        
        return stencil


    def find_derivs (self, ij, show=False):
  
        Teff = self.Teff_axis[ij[0]]
        logg = self.logg_axis[ij[1]]

        node = self.nodes[ij[0],ij[1]]

        nbrs = self.find_neighbors(ij)

        for j in [-1,1]:

            for i in [-1,1]:
                
                Teff_i = self.Teff_axis[ ij[0]+i ]
                logg_j = self.logg_axis[ ij[1]+j ]

                

                
                if show:
                    if j==0 and i==0:  print(f'({nbrs[i+1,j+1]})', end=' ')
                    else: print(nbrs[i+1,j+1], end=' ')
            
            if show: print('\n')

            
if __name__ == '__main__':

    filenames = sys.argv[1:]

    if len(filenames) == 0:
        raise Exception("Syntax: grid.py [filename list]")

    grid = Grid(filenames, debug=True)

    grid.show_topology()

    try:
        #user_Teff = float(input('Enter Teff [K]: '))
        #user_logg = float(input('Enter logg [dex]: '))
        
        #grid.locate(user_Teff, user_logg)
        
        print('Entering i=7 for Teff=30000K \nEntering j=3 for logg=4.0')
        user_i = 7 #int(input('Enter i=7 for Teff=30000K: '))
        user_j = 3 #int(input('Enter j=3 for logg=4.0: '))
        
        grid.find_derivs((user_i,user_j), show=True)

    except IndexError:
        print("\nOpe, that right there's gonna be a problem. How's 'bout we try a different (Teff,logg)?\n")
        raise
    

    