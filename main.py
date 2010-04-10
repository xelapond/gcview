from __future__ import division
import random
import sys
import re

import pyglet
from pyglet.gl import *


'''
Unfortunately the design of NC Code lends itself to a state machine, 
so that's how this program works:/
'''

#Global states:(
absolute = True
inches = True

#Zoom level
gzl = 1

LERP_COLOR = (1, 1, 1, 1)
RAPID_POS_COLOR = (1, 0, 0, 0)

#Regex for finding a G-Code comment
fc = re.compile('\(.*\)')

#Return a list of all the comments(as strings)
fci = lambda t: fc.findall(t)

def remove_comments(t):
    comments = fci(t)
    for c in comments:
        t = ''.join(t.split(c))

    return t

#I Think this is depreciated, but maybe not
#We'll see
cdict = {
    .5  : (1, 0, 0), 
    .02 : (0, 0, 0),

     'EXCEPTION' : (1, 1, 1)
}

def draw_vertex(args):
    k = args.keys()
    '''
    Lots of stuff happens here.
    I don't want to explain how this works, it was too much fun to write.
    That would ruin the fun.
    
    What this does is see if there is an X, Y and Z coordinate.  
    It puts them in a list; [X, Y, Z].
    If any of them are missing, it checks for an old coordinate(from the last command(OX, OY or OZ).
    If there is one present, it uses that.
    If neither the current coordinate or its old counterpart exist, use the name of the coordinate(sans 'O')
    If there are any strings in the list(meaning there was a missing coordinate) it can't be drawn
    '''
    #p = [not (type(g) == str) or ('O' + g) in k for g in 
    #p = [((not (g[0] == 'O') and args[g])) or ((g in k) and args[g]) or (g[1]) for g in [((x in k) and x) or ('O' + x) for x in ['X', 'Y', 'Z']]]
    p = ['X', 'Y', 'Z']
    for cn in p:
        if cn in k:
            p[p.index(cn)] = args[cn]
        else:
            if 'O' + cn in k:
                p[p.index(cn)] = args['O' + cn]

    t = filter(lambda x: type(x) == str, p)
    if t:
        print 'Could not execute command, no ' + str(t) + ' Coordinate(s)'
        return False, p

    glVertex2f(p[0]*400, p[1]*400)
    return True
    
def draw_rapid(args):
    #We just do this so we don't get blending
    if args['OC'][0] == 'GO1':
        glEnd()
        glBegin(GL_LINE_STRIP)

    glColor4f(*RAPID_POS_COLOR)

    return draw_vertex(args)

def draw_lerp(args):
    #We just do this so we don't get blending
    if args['OC'][0] == 'GO1':
        glEnd()
        glBegin(GL_LINE_STRIP)

    glColor4f(*LERP_COLOR)

    return draw_vertex(args)

def set_imperial(args):
    global inches
    inches = True

def set_metric(args):
    global inches
    inches = False

def set_absolute(args):
    global absolute
    absolute = True

def set_incremental(args):
    global absolute
    absolute = False

#Maps G-Codes to python functions
fdict = {
   'G00' : draw_rapid,
   'G01' : draw_lerp,
   'G20' : set_imperial,
   'G21' : set_metric,
   'G90' : set_absolute,
   'G91' : set_incremental
}

def add_dict(d1, d2):
    #TODO: Take more then one dict(In one line)
    return dict(d1.items() + d2.items())

def start_display_list():
    dlist = glGenLists(1)
    glNewList(dlist, GL_COMPILE)
    
    return dlist

def args2dict(args):
    '''
    Converts a G-Code argument list into a dictionary

    Example:
       ['X1.010', 'Y0.045'] -> {'X':1.010, 'Y':0.045}
    '''
    return dict((exp[:1], float(exp[1:])) for exp in args)

def parse_line(line):
    #TODO: Implement multiple commands per line
    #Do this in one of two ways
    #   Hackish: Split by G, use list comprehension and add the G back, then recurse
    #   Not So Hackish: Write a function to split based on a regex
    #/TODO
    exp = line.split(' ')
    try:
        exp.remove('')
    except:
        if '-v' in sys.argv:
            print 'THERE IS NO \'\' TO REMOVE'
    pred = exp[0]
    args = args2dict(exp[1:])
    return pred, args

def parse_file(lines):
    dlist = start_display_list()
    glBegin(GL_LINE_STRIP)
    args = {'X':0, 'Y':0, 'Z':0}
    for l in lines:
        #The 'e' represents the args and predicate from the expression
        epred, eargs = parse_line(l)
        args['OX'], args['OY'], args['OZ'], args['OC'] = args['X'], args['Y'], args['Z'], [epred, eargs]
        args = add_dict(args, eargs)
        if not absolute:
            #If incremental
            for x in ['X', 'Y', 'Z']:
                args[c] = args['O' + c] + args[c]
        if epred in fdict.keys():
            fdict[epred](args)
        else:
            #This is just so I know what to implement
            if '-v' in sys.argv:
                print epred
            
            
    glEnd()
    glEndList()
    return dlist

def on_mouse_drag(x, y, dx, dy, buttons, mods):
    global gzl
    if buttons == 1:
        #For panning
        glTranslatef(dx*(gzl**-1), dy*(gzl**-1), 0)
    if buttons == 4:
        #Rotation.  Not sure why, maybe desirable in some obscure instances.
        glTranslatef(x, y, 0)
        glRotatef(dx, 0, 0, 1)
        glTranslatef(-x, -y, 0)

#TODO: Make this function do something
def on_mouse_scroll(x, y, dx, dy):
    #This will have to be a translation or a scale on the OpenGL Level
    #as we calculate all the graphics at the beginning of the program
    global gzl #This is only a global variable so we can multiply panning, to make it work on a 1:1 ratio at all zoom levels
    zl = 1 + (dy/10)
    gzl *= zl
    if '-Z' not in sys.argv:
        print 'Zoom Level: ' + str(gzl)
    #Translate to the mouse so we don't zoom about the origin
    glTranslatef(x, y, 0)
    glScalef(zl, zl, zl)
    glTranslatef(-x, -y, 0)


def on_draw(t, win, dlist):
    win.clear()

    glCallList(dlist)
    
    win.flip()

if __name__ == '__main__':
    #Get a G-Code file
    file = open(sys.argv[1])
    inp = file.read()

    nc = filter(lambda x: x != '', remove_comments(inp).split('\n'))
    dlist = parse_file(nc)

    print 'Coordinates: ' + {True:'Absolute', False:'Incremental'}[absolute]
    print 'Units: ' + {True:'Imperial', False:'Metric'}[inches]

    win = pyglet.window.Window(800, 800)

    win.on_mouse_drag = on_mouse_drag
    win.on_mouse_scroll = on_mouse_scroll

    pyglet.clock.schedule(on_draw, win, dlist)
    pyglet.app.run()
