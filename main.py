import random
import sys
import re


import pyglet
from pyglet.gl import *

'''
Unfortunately the design of NC Code lends itself to a state machine, 
so that's how this program works:/
'''

'''
Some G Codes:

# Denotes a code that needs to be implemented

G00 Rapid positioning
# G01 Linear interpolation
# G02 CW circular interpolation
# G03 CCW circular interpolation
G04 Dwell
G05.1 Q1. Ai Nano contour control
G05 P10000 HPCC
G07 Imaginary axis designation
G09 Exact stop check
G10/G11 Programmable Data input/Data write cancel
# G12 CW Circle Cutting
# G13 CCW Circle Cutting
G17 X-Y plane selection
G18 X-Z plane selection
G19 Y-Z plane selection
## G20 Programming in inches
## G21 Programming in mm
# G28 Return to home position
G30 2nd reference point return
G31 Skip function (used for probes and tool length measurement systems)
G33 Constant pitch threading
G34 Variable pitch threading
G40 Tool radius compensation off
G41 Tool radius compensation left
G42 Tool radius compensation right
G43 Tool height offset compensation negative
G44 Tool height offset compensation positive
G45 Axis offset single increase
G46 Axis offset single decrease
G47 Axis offset double increase
G48 Axis offset double decrease
G49 Tool offset compensation cancel
G50 Define the maximum spindle speed
G53 Machine coordinate system
G54 to G59 Work coordinate systems
G54.1 P1 to P48 Extended work coordinate systems
G73 High speed drilling canned cycle
G74 Left hand tapping canned cycle
G76 Fine boring canned cycle
G80 Cancel canned cycle
G81 Simple drilling cycle
G82 Drilling cycle with dwell
G83 Peck drilling cycle
G84 Tapping cycle
G84.2 Direct right hand tapping canned cycle
### G90 Absolute programming (type B and C systems)
### G91 Incremental programming (type B and C systems)
# G92 Programming of absolute zero point
G94/G95 Inch per minute/Inch per revolution feed (type A system) Note: Some CNCs use the SI unit system
G96 Constant surface speed
G97 Constant Spindle speed
G98/G99 Return to Initial Z plane/R plane in canned cycle

'''

LERP_COLOR = (1, 1, 1, 1)
RAPID_POS_COLOR = (1, 0, 0, 1)

#Get a sample file
sf = open('sample/untitledtop.nc')
sfc = sf.read()

#Regex for finding a comment
fc = re.compile('\(.*\)')

#Return a list of all the comments(as strings)
fci = lambda t: fc.findall(t)

def remove_comments(t):
    comments = fci(t)
    for c in comments:
        t = ''.join(t.split(c))

    return t

#TODO:
'''
Use pyglet -> Display lists

Write a function to convert applicable gcode into a display list
Then manipulate this
'''

def dRect(pos, size, rgba):
    glColor4f(*rgba)

    #glBegin(GL_POLYGON)
    glVertex2f(pos[0], pos[1])
    glVertex2f(pos[0], pos[1] + size[1])
    glVertex2f(pos[0] + size[0], pos[1] + size[1])
    glVertex2f(pos[0] + size[0], pos[1])
    #glEnd()
    #glFlush()

cdict = {
    .5  : (1, 0, 0), 
    .02 : (0, 0, 0),

     'EXCEPTION' : (1, 1, 1)
}


def test(t):
    #win.clear()
    
    '''
    glLoadIdentity()
    glViewport(-1, -1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glFrustum(-width/2, width/2, -height/2, height/2, .1, 100)
    glScalef(5000, 5000, 1)
    glTranslatef(0, 0, -500)
    glMatrixMode(GL_MODELVIEW)
    '''


 
    #win.flip()


def draw_vertex(args):
    global zl
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

    #print [x*200 for x in p]
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

#Maps G-Codes to python functions
fdict = {
   'G00' : draw_rapid,
   'G01' : draw_lerp,
}

#TODO:
'''
STARTDISPLAYLIST()
args = {'OX':0, 'OY':0, 'OZ':0}
for l in lines:
    pred, args = PARSEIT()
    args['OX'], args['OY'], args['OZ'], args['OC'] = OZ, OY, OZ, [pred, args]
    fdict[pred](args)

ENDDISPLAYLIST()
'''

def add_dict(d1, d2):
    #TODO: Take more then one dict(In one line)
    #WORKS
    return dict(d1.items() + d2.items())



def start_display_list():
    dlist = glGenLists(1)
    glNewList(dlist, GL_COMPILE)
    
    return dlist

def end_display_list():
    glEndList()

def args2dict(args):
    '''
    Converts a G-Code argument list into a dictionary

    Example:
       ['X1.010', 'Y0.045'] -> {'X':1.010, 'Y':0.045}
    '''
    #WORKS
    return dict((exp[:1], float(exp[1:])) for exp in args)

###TODO: Replace the fdict reference call with a glVertex for testing, it doesn't work:/
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
        print 'THERE IS NO \'\' TO REMOVE'
    pred = exp[0]
    args = args2dict(exp[1:])
    return pred, args

def gen_display_list(lines):
    dlist = start_display_list()
    glBegin(GL_LINE_STRIP)
    args = {'OX':0, 'OY':0, 'OZ':0, 'X':0, 'Y':0, 'Z':0}
    for l in lines:
        #The 'e' represents the args and predicate from the expression
        epred, eargs = parse_line(l)
        args['OX'], args['OY'], args['OZ'], args['OC'] = args['X'], args['Y'], args['Z'], [epred, eargs]
        args = add_dict(args, eargs)
        if epred in fdict.keys():
            #print 'Call'
            #test(6)
            fdict[epred](args)
        else:
            print epred
            
    glEnd()
    end_display_list()
    return dlist


nc = remove_comments(sfc).split('\n')
nc = filter(lambda x: x != '', nc)
dlist = gen_display_list(nc)
'''
rect = glGenLists(1)
glNewList(rect, GL_COMPILE)
dRect((0, 0), (40, 40), (1, 0, 0, 1))
glEndList()
'''
'''
def on_draw(*argarg):
    global win, nc
    win.clear()
    #glClear(GL_COLOR_BUFFER_BIT)

    #dRect((0, 0), (500, 500), (0, 1, 0, 1))

    glColor3f(1, 0, 0)
    glBegin(GL_LINE_STRIP)

    for line in nc:
        x = y = z = None
        exp = line.split(' ')
        if exp[0] == 'G01' or exp[0] == 'G00':
            try:
                exp.remove('')
            except:
                pass
            args = exp[1:]
            
            for arg in args:
                if arg[0].lower() == 'x':
                    x = float(arg[1:])
                elif arg[0].lower() == 'y':
                    y = float(arg[1:])
                elif arg[0].lower() == 'z':
                    z = float(arg[1:])
                else:
                    if '-w' in sys.argv:
                        print 'FAIL ' + str(exp)
                        
            if z:
                try:
                    glColor3f(*cdict[z])
                except:
                    glColor3f(*cdict['EXCEPTION'])
            if x and y:
                glVertex2f(x*zl, y*zl)

    

    glEnd()
    
    win.flip()
'''
def on_mouse_drag(x, y, dx, dy, buttons, mods):
    print buttons
    if buttons == 1:
        glTranslatef(dx, dy, 0)
    if buttons == 4:
        
        glRotatef(dx, 0, 0, 1)

def on_mouse_scroll(x, y, dx, dy):
    global zl
    print dy
    zl += 10*dy


def on_draw(*argarg):
    global win, ne, dlist
    win.clear()

    glColor3f(1, 0, 0)

#    glBegin(GL_LINE_STRIP)
#    #dRect((0, 0), (400, 400), (.5, .2, .6, 1))
#    gen_display_list(nc)
#    glEnd()

 #   glBegin(GL_LINE_STRIP)
    #gen_display_list(nc)
   # glEnd()
    
    glCallList(dlist)
    
    win.flip()


width, height = 400, 400
zl = 0

if __name__ == '__main__':
    win = pyglet.window.Window(400, 400)

    '''
    glViewport(-1, -1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glFrustum(-width/2, width/2, -height/2, height/2, .1, 100)
    glScalef(5000, 5000, 1)
    glTranslatef(0, 0, -500)
    glMatrixMode(GL_MODELVIEW)
    '''

    nc = remove_comments(sfc).split('\n')
    nc = filter(lambda x: x != '', nc)

    #glShadeModel(GL_FLAT)
    #glClearColor(0, 0, 0, 0)

    win.on_mouse_drag = on_mouse_drag
    win.on_mouse_scroll = on_mouse_scroll


    
   # while 1:
   #     on_draw()
   #     win.dispatch_events()
        #win.dispatch_event('on_mouse_drag')

#    win.on_draw = on_draw
    pyglet.clock.schedule(on_draw)
    pyglet.app.run()