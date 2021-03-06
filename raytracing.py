"""
MIT License
Copyright (c) 2017 Cyrille Rossant
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import math
import numpy as np
import matplotlib.pyplot as plt
import random
w = 400
h = 300

def normalize(x):
    x /= np.linalg.norm(x)
    return x

def intersect_plane(O, D, P, N):
    # Return the distance from O to the intersection of the ray (O, D) with the 
    # plane (P, N), or +inf if there is no intersection.
    # O and P are 3D points, D and N (normal) are normalized vectors.
    denom = np.dot(D, N)
    if np.abs(denom) < 1e-6:
        return np.inf
    d = np.dot(P - O, N) / denom
    if d < 0:
        return np.inf
    return d

def intersect_sphere(O, D, S, R):
    # Return the distance from O to the intersection of the ray (O, D) with the 
    # sphere (S, R), or +inf if there is no intersection.
    # O and S are 3D points, D (direction) is a normalized vector, R is a scalar.
    a = np.dot(D, D)
    OS = O - S
    b = 2 * np.dot(D, OS)
    c = np.dot(OS, OS) - R * R
    disc = b * b - 4 * a * c
    if disc > 0:
        distSqrt = np.sqrt(disc)
        q = (-b - distSqrt) / 2.0 if b < 0 else (-b + distSqrt) / 2.0
        t0 = q / a
        t1 = c / q
        t0, t1 = min(t0, t1), max(t0, t1)
        if t1 >= 0:
            return t1 if t0 < 0 else t0
    return np.inf


def intersect_triangle(O, D, P, N):
    # comprobacion intersecciones
    dist = intersect_plane(0, D, np.array(P[0]), N)
    
    if (dist == np.inf):
        return np.inf
            
    a = -np.dot(N,(O-P[0]))
    b = np.dot(N,D)

    di = a / b
    I = O + D*di

    # vectores      
    v0 = np.subtract(P[1],P[0])
    v1 = np.subtract(P[2],P[0])
    v2 = I - P[0]

    # producto vectores
    v00 = np.dot(v0, v0)
    v01 = np.dot(v0, v1)
    v11 = np.dot(v1, v1)
    v20 = np.dot(v2,v0)
    v21 = np.dot(v2,v1)
    

    inter = v01 * v01 - v00 * v11 

    prod1 = (v01 * v21 - v11 * v20) / inter
    prod2 = (v01 * v20 - v00 * v21) / inter
    
    # comprobacion triangulo
    if (prod1 >= 0) and (prod2 >= 0) and (prod1 + prod2 < 1):
        return dist

    return np.inf


def intersect(O, D, obj):
    if obj['type'] == 'plane':
        return intersect_plane(O, D, obj['position'], obj['normal'])
    elif obj['type'] == 'sphere':
        return intersect_sphere(O, D, obj['position'], obj['radius'])
    elif obj['type'] == 'triangle':
        return intersect_triangle(O, D, obj['position'], obj['normal'])

def get_normal(obj, M):
    # Find normal.
    if obj['type'] == 'sphere':
        N = normalize(M - obj['position'])
    elif obj['type'] == 'plane':
        N = obj['normal']
    elif obj['type'] == 'triangle':
        N = obj['normal']
    return N
    
def get_color(obj, M):
    color = obj['color']
    if not hasattr(color, '__len__'):
        color = color(M)
    return color

def trace_ray(rayO, rayD):
    # Find first point of intersection with the scene.
    t = np.inf
    for i, obj in enumerate(scene):
        t_obj = intersect(rayO, rayD, obj)
        if t_obj < t:
            t, obj_idx = t_obj, i
    # Return None if the ray does not intersect any object.
    if t == np.inf:
        return
    # Find the object.
    obj = scene[obj_idx]
    # Find the point of intersection on the object.
    M = rayO + rayD * t
    # Find properties of the object.
    N = get_normal(obj, M)
    
    
    # Start computing the color.
    col_ray = ambient
    color = get_color(obj, M)
    light = 0

    for light in range(len(lights)):      
        toL = normalize(lights[light] - M)
        toO = normalize(O - M)
        # Shadow: find if the point is shadowed or not.
        l = [intersect(M + N * .0001, toL, obj_sh) 
                for k, obj_sh in enumerate(scene) if k != obj_idx]
        if l and min(l) >= np.inf:
            # Lambert shading (diffuse).
            col_ray += obj.get('diffuse_c', diffuse_c) * max(np.dot(N, toL), 0) * color
            # Blinn-Phong shading (specular).
            col_ray += obj.get('specular_c', specular_c) * max(np.dot(N, normalize(toL + toO)), 0) ** specular_k * color_lights[light]
    return obj, M, N, col_ray


def add_sphere(position, radius, color):
    return dict(type='sphere', position=np.array(position), 
        radius=np.array(radius), color=np.array(color), reflection=.5)
    
def add_plane(position, normal):
    return dict(type='plane', position=np.array(position), 
        normal=np.array(normal),
        color=lambda M: (color_plane0 
            if (int(M[0] * 2) % 2) == (int(M[2] * 2) % 2) else color_plane1),
        diffuse_c=.75, specular_c=.5, reflection=.25)

def add_triangle(position, color):
    n1 = np.subtract(position[1],position[0])
    n2 = np.subtract(position[2],position[0])
    return dict(type='triangle', position=(position), 
        color=np.array(color), reflection=.5,normal = (np.cross(n1,n2)))


def calculate_dist(P1,P2):
    PQ = np.subtract(P1,P2)
    d = math.sqrt((PQ[0]**2) + (PQ[1]**2) + (PQ[2]**2))
    return d

def add_concat_triangle(vertices,color):

    out1 = [add_triangle(vertices[0:3], color)]
    
    for i in range(3,len(vertices)):
        a = proces_concat_triangle(vertices[0:i],vertices[i])
        if i % 2 == 1:
            aux = [vertices[i],vertices[a[1]],vertices[a[0]]]   
        else:
            aux = [vertices[a[0]],vertices[a[1]],vertices[i]]   
        
        t = add_triangle(aux, draw_colors[(random.randint(0,5))])
        out1.append(t)
    return out1
    

def proces_concat_triangle(vertices,P2):
    d1 = [999,7.0]
    d2 = [999.0,7.0]
    for i in range(0,len(vertices)):
        di = calculate_dist(P2,vertices[i])
        if di < d1[0]:
            d2[0] = d1[0]
            d2[1] = d1[1]
            d1[0] = di
            d1[1] = float(i)
        elif di < d2[0]:
            d2[0] = di
            d2[1] = float(i)
    return [int(d1[1]),int(d2[1])]
             


    
# List of objects.
color_plane0 = 1. * np.ones(3)
color_plane1 = 0. * np.ones(3)



draw_colors = [[1.,0.,0.],[1.,1.,0.],[0.,1.,0.],[0.,1.,1.],[0.,0.,1.],[1.,0.,1.]]
    

scene = [

    add_plane([0., -.5, 0.], [0., 1., 0.]),
    ]

scene = add_concat_triangle( [[-1.,-0.5,1],[-0.5,0.5,1],[0.,-0.5,1],[0.5,0.5,1],[1.,-0.5,1]],[0.,0.,2.]) + scene

# Light position array. 
lights = np.array([[5., 4., -5.],[5., 5., 0.],[-20., 8., -25.]])

# Colors array 
color_lights = np.array([[2.,1.,1.],[1.,2.,3.],[1.,1.,1.]])

# Default light and material parameters.
ambient = .05
diffuse_c = 1.
specular_c = 1.
specular_k = 50

depth_max = 5  # Maximum number of light reflections.
col = np.zeros(3)  # Current color.
O = np.array([0., 0.35, -1.])  # Camera.
Q = np.array([0., 0., 0.])  # Camera pointing to.
img = np.zeros((h, w, 3))

r = float(w) / h
# Screen coordinates: x0, y0, x1, y1.
S = (-1., -1. / r + .25, 1., 1. / r + .25)

# Loop through all pixels.
for i, x in enumerate(np.linspace(S[0], S[2], w)):
    if i % 10 == 0:
        print (i / float(w) * 100, "%")
    for j, y in enumerate(np.linspace(S[1], S[3], h)):
        col[:] = 0
        Q[:2] = (x, y)
        D = normalize(Q - O)
        depth = 0
        rayO, rayD = O, D
        reflection = 1.
        # Loop through initial and secondary rays.
        while depth < depth_max:
            traced = trace_ray(rayO, rayD)
            if not traced:
                break
            obj, M, N, col_ray = traced
            # Reflection: create a new ray.
            rayO, rayD = M + N * .0001, normalize(rayD - 2 * np.dot(rayD, N) * N)
            depth += 1
            col += reflection * col_ray
            reflection *= obj.get('reflection', 1.)
        img[h - j - 1, i, :] = np.clip(col, 0, 1)

plt.imsave('fig.png', img)