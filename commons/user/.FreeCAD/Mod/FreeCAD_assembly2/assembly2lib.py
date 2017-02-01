'''
assembly2 constraints are stored under App::FeaturePython object (constraintObj)

cName = findUnusedObjectName('axialConstraint')
c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
c.addProperty("App::PropertyString","Type","ConstraintInfo","Object 1").Type = '...'
       
see http://www.freecadweb.org/wiki/index.php?title=Scripted_objects#Available_properties for more information
'''

import numpy, os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui, QtCore
from lib3D import fit_plane_to_surface1, fit_rotation_axis_to_surface1
from viewProviderProxies import ImportedPartViewProviderProxy, ConstraintViewProviderProxy,\
     create_constraint_mirror, repair_tree_view

path_assembly2 = os.path.dirname(__file__)
#path_assembly2_icons =  os.path.join( path_assembly2, 'Resources', 'icons')
#path_assembly2_ui =  os.path.join( path_assembly2, 'Resources', 'ui')
path_assembly2_resources = os.path.join( path_assembly2, 'Gui', 'Resources', 'resources.rcc')
resourcesLoaded = QtCore.QResource.registerResource(path_assembly2_resources)
assert resourcesLoaded
#update resources file using 
# $rcc -binary  Gui/Resources/resources.qrc -o Gui/Resources/resources.rcc 

__dir__ = path_assembly2
wb_globals = {}

def isLine(param):
    if hasattr(Part,"LineSegment"):
        return isinstance(param,(Part.Line,Part.LineSegment))
    else:
        return isinstance(param,Part.Line)

def debugPrint( level, msg ):
    if level <= debugPrint.level:
        FreeCAD.Console.PrintMessage(msg + '\n')
debugPrint.level = 4 if hasattr(os,'uname') and os.uname()[1].startswith('antoine') else 2
#debugPrint.level = 4 #maui to debug

def formatDictionary( d, indent):
    return '%s{' % indent + '\n'.join(['%s%s:%s' % (indent,k,d[k]) for k in sorted(d.keys())]) + '}'

class ConstraintSelectionObserver:
     def __init__(self, selectionGate, parseSelectionFunction, 
                  taskDialog_title, taskDialog_iconPath, taskDialog_text,
                  secondSelectionGate=None):
          self.selections = []
          self.parseSelectionFunction = parseSelectionFunction
          self.secondSelectionGate = secondSelectionGate
          FreeCADGui.Selection.addObserver(self)  
          FreeCADGui.Selection.removeSelectionGate()
          FreeCADGui.Selection.addSelectionGate( selectionGate )
          wb_globals['selectionObserver'] = self
          self.taskDialog = SelectionTaskDialog(taskDialog_title, taskDialog_iconPath, taskDialog_text)
          FreeCADGui.Control.showDialog( self.taskDialog )
     def addSelection( self, docName, objName, sub, pnt ):
         debugPrint(4,'addSelection: docName,objName,sub = %s,%s,%s' % (docName, objName, sub))
         obj = FreeCAD.ActiveDocument.getObject(objName)
         debugPrint(1,'addSelection: docName,obj.Label,sub = %s,%s,%s' % (docName, obj.Label, sub)) # to print selection name
         self.selections.append( SelectionRecord( docName, objName, sub ))
         if len(self.selections) == 2:
             self.stopSelectionObservation()
             self.parseSelectionFunction( self.selections)
         elif self.secondSelectionGate <> None and len(self.selections) == 1:
             FreeCADGui.Selection.removeSelectionGate()
             FreeCADGui.Selection.addSelectionGate( self.secondSelectionGate )
     def stopSelectionObservation(self):
         FreeCADGui.Selection.removeObserver(self) 
         del wb_globals['selectionObserver']
         FreeCADGui.Selection.removeSelectionGate()
         FreeCADGui.Control.closeDialog()


class SelectionRecord:
    def __init__(self, docName, objName, sub):
        self.Document = FreeCAD.getDocument(docName)
        self.ObjectName = objName
        self.Object = self.Document.getObject(objName)
        self.SubElementNames = [sub]


class SelectionTaskDialog:
    def __init__(self, title, iconPath, textLines ):
        self.form = SelectionTaskDialogForm( textLines )
        self.form.setWindowTitle( title )    
        if iconPath <> None:
            self.form.setWindowIcon( QtGui.QIcon( iconPath ) )
    def reject(self):
        wb_globals['selectionObserver'].stopSelectionObservation()
    def getStandardButtons(self): #http://forum.freecadweb.org/viewtopic.php?f=10&t=11801
        return 0x00400000 #cancel button
class SelectionTaskDialogForm(QtGui.QWidget):    
    def __init__(self, textLines ):
        super(SelectionTaskDialogForm, self).__init__()
        self.textLines = textLines 
        self.initUI()
    def initUI(self):
        vbox = QtGui.QVBoxLayout()
        for line in self.textLines.split('\n'):
            vbox.addWidget( QtGui.QLabel(line) )
        self.setLayout(vbox)


def findUnusedObjectName(base, counterStart=1, fmt='%02i', document=None):
    i = counterStart
    objName = '%s%s' % (base, fmt%i)
    if document == None:
        document = FreeCAD.ActiveDocument
    usedNames = [ obj.Name for obj in document.Objects ]    
    while objName in usedNames:
        i = i + 1
        objName = '%s%s' % (base, fmt%i)
    return objName

def findUnusedLabel(base, counterStart=1, fmt='%02i', document=None):
    i = counterStart
    label = '%s%s' % (base, fmt%i)
    if document == None:
        document = FreeCAD.ActiveDocument
    usedLabels = [ obj.Label for obj in document.Objects ]
    while label in usedLabels:
        i = i + 1
        label = '%s%s' % (base, fmt%i)
    return label


class ConstraintObjectProxy:
    def execute(self, obj):
        preferences = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
        if preferences.GetBool('autoSolveConstraintAttributesChanged', True):
            self.callSolveConstraints()
            #obj.touch()
    def onChanged(self, obj, prop):
        if hasattr(self, 'mirror_name'):
            cMirror = obj.Document.getObject( self.mirror_name )
            if cMirror.Proxy == None:
                return #this occurs during document loading ...
            if obj.getGroupOfProperty( prop ) == 'ConstraintInfo':
                cMirror.Proxy.disable_onChanged = True
                setattr( cMirror, prop, getattr( obj, prop) )
                cMirror.Proxy.disable_onChanged = False

    def reduceDirectionChoices( self, obj, value):
        if hasattr(self, 'mirror_name'):
            cMirror = obj.Document.getObject( self.mirror_name )
            cMirror.directionConstraint = ["aligned","opposed"] #value should be updated in onChanged call due to assignment in 2 lines
        obj.directionConstraint = ["aligned","opposed"]
        obj.directionConstraint = value
    def callSolveConstraints(self):
        from assembly2solver import solveConstraints
        preferences = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
        if preferences.GetBool('useCache', False):
            import cache_assembly2
            solverCache = cache_assembly2.defaultCache
        else:
            solverCache = None
        solveConstraints( FreeCAD.ActiveDocument, cache = solverCache )

def removeConstraint( constraint ):
    'required as constraint.Proxy.onDelete only called when deleted through GUI'
    doc = constraint.Document
    debugPrint(2, "removing constraint %s" % constraint.Name )
    if constraint.ViewObject != None: #do not this check is actually nessary ...
        constraint.ViewObject.Proxy.onDelete( constraint.ViewObject, None )
    doc.removeObject( constraint.Name )
    

class SelectConstraintObjectsCommand:
    def Activated(self):
        constraintObj = FreeCADGui.Selection.getSelectionEx()[0].Object
        obj1Name = constraintObj.Object1
        obj2Name = constraintObj.Object2
        FreeCADGui.Selection.addSelection( FreeCAD.ActiveDocument.getObject(obj1Name) )
        FreeCADGui.Selection.addSelection( FreeCAD.ActiveDocument.getObject(obj2Name) )
    def GetResources(self): 
        return { 'MenuText': 'Select Objects' }
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('selectConstraintObjects', SelectConstraintObjectsCommand())

class SelectConstraintElementsCommand:
    def Activated(self):
        constraintObj = FreeCADGui.Selection.getSelectionEx()[0].Object
        obj1Name = constraintObj.Object1
        obj2Name = constraintObj.Object2
        FreeCADGui.Selection.addSelection( FreeCAD.ActiveDocument.getObject(obj1Name), constraintObj.SubElement1 )
        FreeCADGui.Selection.addSelection( FreeCAD.ActiveDocument.getObject(obj2Name), constraintObj.SubElement2 )
    def GetResources(self): 
        return { 'MenuText': 'Select Object Elements' }
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('selectConstraintElements', SelectConstraintElementsCommand())

def printSelection(selection):
    entries = []
    for s in selection:
        for e in s.SubElementNames:
            entries.append(' - %s:%s' % (s.ObjectName, e))
            if e.startswith('Face'):
                ind = int( e[4:]) -1 
                face = s.Object.Shape.Faces[ind]
                entries[-1] = entries[-1] + ' %s' % str(face.Surface)
    return '\n'.join( entries[:5] )
                


def updateOldStyleConstraintProperties( doc ):
    'used to update old constraint attributes, [object, faceInd] -> [object, subElement]...'
    for obj in doc.Objects:
        if 'ConstraintInfo' in obj.Content:
            updateObjectProperties( obj )

def updateObjectProperties( c ):
    if hasattr(c,'FaceInd1'):
        debugPrint(3,'updating properties of %s' % c.Name )
        for i in [1,2]:
            c.addProperty('App::PropertyString','SubElement%i'%i,'ConstraintInfo')
            setattr(c,'SubElement%i'%i,'Face%i'%(getattr(c,'FaceInd%i'%i)+1))
            c.setEditorMode('SubElement%i'%i, 1) 
            c.removeProperty('FaceInd%i'%i)
        if hasattr(c,'planeOffset'):
            v = c.planeOffset
            c.removeProperty('planeOffset')
            c.addProperty('App::PropertyDistance','offset',"ConstraintInfo")
            c.offset = '%f mm' % v
        if hasattr(c,'degrees'):
            v = c.degrees
            c.removeProperty('degrees')
            c.addProperty("App::PropertyAngle","angle","ConstraintInfo")
            c.angle = v
    elif hasattr(c,'EdgeInd1'):
        debugPrint(3,'updating properties of %s' % c.Name )
        for i in [1,2]:
            c.addProperty('App::PropertyString','SubElement%i'%i,'ConstraintInfo')
            setattr(c,'SubElement%i'%i,'Edge%i'%(getattr(c,'EdgeInd%i'%i)+1))
            c.setEditorMode('SubElement%i'%i, 1) 
            c.removeProperty('EdgeInd%i'%i)
        v = c.offset
        c.removeProperty('offset')
        c.addProperty('App::PropertyDistance','offset',"ConstraintInfo")
        c.offset = '%f mm' % v
    if c.Type == 'axial' or c.Type == 'circularEdge':
        if not hasattr(c, 'lockRotation'):
            debugPrint(3,'updating properties of %s, to add lockRotation (default=false)' % c.Name )
            c.addProperty("App::PropertyBool","lockRotation","ConstraintInfo")
    if FreeCAD.GuiUp:
        if not isinstance( c.ViewObject.Proxy , ConstraintViewProviderProxy):
            iconPaths = {
                'angle_between_planes':':/assembly2/icons/angleConstraint.svg',
                'axial':':/assembly2/icons/axialConstraint.svg',
                'circularEdge':':/assembly2/icons/circularEdgeConstraint.svg',
                'plane':':/assembly2/icons/planeConstraint.svg',
                'sphericalSurface': ':/assembly2/icons/sphericalSurfaceConstraint.svg'
            }
            c.ViewObject.Proxy = ConstraintViewProviderProxy( c, iconPaths[c.Type] )
    
def getObjectFaceFromName( obj, faceName ):
    assert faceName.startswith('Face')
    ind = int( faceName[4:]) -1 
    return obj.Shape.Faces[ind]

class SelectionExObject:
    'allows for selection gate funtions to interface with classification functions below'
    def __init__(self, doc, Object, subElementName):
        self.doc = doc
        self.Object = Object
        self.ObjectName = Object.Name
        self.SubElementNames = [subElementName]
    

def planeSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Face'):
            face = getObjectFaceFromName( selection.Object, subElement)
            if str(face.Surface) == '<Plane object>':
                return True
            elif hasattr(face.Surface,'Radius'):
                return False
            elif str(face.Surface).startswith('<SurfaceOfRevolution'):
                return False
            else:
                plane_norm, plane_pos, error = fit_plane_to_surface1(face.Surface)
                error_normalized = error / face.BoundBox.DiagonalLength
                #debugPrint(2,'plane_norm %s, plane_pos %s, error_normalized %e' % (plane_norm, plane_pos, error_normalized))
                return error_normalized < 10**-6
    return False

def cylindricalPlaneSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Face'):
            face = getObjectFaceFromName( selection.Object, subElement)
            if hasattr(face.Surface,'Radius'):
                return True
            elif str(face.Surface).startswith('<SurfaceOfRevolution'):
                return True
            elif str(face.Surface) == '<Plane object>':
                return False
            else:
                axis, center, error = fit_rotation_axis_to_surface1(face.Surface)
                error_normalized = error / face.BoundBox.DiagonalLength
                #debugPrint(2,'fitted axis %s, center %s, error_normalized %e' % (axis, center,error_normalized))
                return error_normalized < 10**-6
    return False

def AxisOfPlaneSelected( selection ): #adding Planes/Faces selection for Axial constraints
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Face'):
            face = getObjectFaceFromName( selection.Object, subElement)
            if str(face.Surface) == '<Plane object>':
                return True
            else:
                axis, center, error = fit_rotation_axis_to_surface1(face.Surface)
                error_normalized = error / face.BoundBox.DiagonalLength
                #debugPrint(2,'fitted axis %s, center %s, error_normalized %e' % (axis, center,error_normalized))
                return error_normalized < 10**-6
    return False

def getObjectEdgeFromName( obj, name ):
    assert name.startswith('Edge')
    ind = int( name[4:]) -1 
    return obj.Shape.Edges[ind]

def CircularEdgeSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Edge'):
            edge = getObjectEdgeFromName( selection.Object, subElement)
            if not hasattr(edge, 'Curve'): #issue 39
                return False
            if hasattr( edge.Curve, 'Radius' ):
                return True
            elif isLine(edge.Curve):
                return False
            else:
                BSpline = edge.Curve.toBSpline()
                try:
                    arcs = BSpline.toBiArcs(10**-6)
                except:  #FreeCAD exception thrown ()
                    return False
                if all( hasattr(a,'Center') for a in arcs ):
                    centers = numpy.array([a.Center for a in arcs])
                    sigma = numpy.std( centers, axis=0 )
                    return max(sigma) < 10**-6
    return False

def LinearEdgeSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Edge'):
            edge = getObjectEdgeFromName( selection.Object, subElement)
            if not hasattr(edge, 'Curve'): #issue 39
                return False
            if isLine(edge.Curve):
                return True
            elif hasattr( edge.Curve, 'Radius' ):
                return False
            else:
                BSpline = edge.Curve.toBSpline()
                try:
                    arcs = BSpline.toBiArcs(10**-6)
                except:  #FreeCAD exception thrown ()
                    return False
                if all(isLine(a) for a in arcs):
                    lines = arcs
                    D = numpy.array([L.tangent(0)[0] for L in lines]) #D(irections)
                    return numpy.std( D, axis=0 ).max() < 10**-9
    return False

def vertexSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        return selection.SubElementNames[0].startswith('Vertex')
    return False

def getObjectVertexFromName( obj, name ):
    assert name.startswith('Vertex')
    ind = int( name[6:]) -1 
    return obj.Shape.Vertexes[ind]

def sphericalSurfaceSelected( selection ):
    if len( selection.SubElementNames ) == 1:
        subElement = selection.SubElementNames[0]
        if subElement.startswith('Face'):
            face = getObjectFaceFromName( selection.Object, subElement)
            return str( face.Surface ).startswith('Sphere ')
    return False

def getSubElementPos(obj, subElementName):
    pos = None
    if subElementName.startswith('Face'):
        face = getObjectFaceFromName(obj, subElementName)
        surface = face.Surface
        if str(surface) == '<Plane object>':
            pos = getObjectFaceFromName(obj, subElementName).Faces[0].BoundBox.Center
            # axial constraint for Planes
            # pos = surface.Position
        elif all( hasattr(surface,a) for a in ['Axis','Center','Radius'] ):
            pos = surface.Center
        elif str(surface).startswith('<SurfaceOfRevolution'):
            pos = getObjectFaceFromName(obj, subElementName).Edges[0].Curve.Center
        else: #numerically approximating surface
            plane_norm, plane_pos, error = fit_plane_to_surface1(face.Surface)
            error_normalized = error / face.BoundBox.DiagonalLength
            if error_normalized < 10**-6: #then good plane fit
                pos = plane_pos
            axis, center, error = fit_rotation_axis_to_surface1(face.Surface)
            error_normalized = error / face.BoundBox.DiagonalLength
            if error_normalized < 10**-6: #then good rotation_axis fix
                pos = center
    elif subElementName.startswith('Edge'):
        edge = getObjectEdgeFromName(obj, subElementName)
        if isLine(edge.Curve):
            pos = edge.Curve.StartPoint
        elif hasattr( edge.Curve, 'Center'): #circular curve
            pos = edge.Curve.Center
        else:
            BSpline = edge.Curve.toBSpline()
            arcs = BSpline.toBiArcs(10**-6)
            if all( hasattr(a,'Center') for a in arcs ):
                centers = numpy.array([a.Center for a in arcs])
                sigma = numpy.std( centers, axis=0 )
                if max(sigma) < 10**-6: #then circular curce
                    pos = centers[0]
            if all(isLine(a) for a in arcs):
                lines = arcs
                D = numpy.array([L.tangent(0)[0] for L in lines]) #D(irections)
                if numpy.std( D, axis=0 ).max() < 10**-9: #then linear curve
                    return lines[0].value(0)
    elif subElementName.startswith('Vertex'):
        return  getObjectVertexFromName(obj, subElementName).Point
    if pos <> None:
        return numpy.array(pos)
    else:
        raise NotImplementedError,"getSubElementPos Failed! Locals:\n%s" % formatDictionary(locals(),' '*4)

    
def getSubElementAxis(obj, subElementName):
    axis = None
    if subElementName.startswith('Face'):
        face = getObjectFaceFromName(obj, subElementName)
        surface = face.Surface
        if hasattr(surface,'Axis'):
            axis = surface.Axis
        elif str(surface).startswith('<SurfaceOfRevolution'):
            axis = face.Edges[0].Curve.Axis
        else: #numerically approximating surface
            plane_norm, plane_pos, error = fit_plane_to_surface1(face.Surface)
            error_normalized = error / face.BoundBox.DiagonalLength
            if error_normalized < 10**-6: #then good plane fit
                axis = plane_norm
            axis_fitted, center, error = fit_rotation_axis_to_surface1(face.Surface)
            error_normalized = error / face.BoundBox.DiagonalLength
            if error_normalized < 10**-6: #then good rotation_axis fix
                axis = axis_fitted
    elif subElementName.startswith('Edge'):
        edge = getObjectEdgeFromName(obj, subElementName)
        if isLine(edge.Curve):
            axis = edge.Curve.tangent(0)[0]
        elif hasattr( edge.Curve, 'Axis'): #circular curve
            axis =  edge.Curve.Axis
        else:
            BSpline = edge.Curve.toBSpline()
            arcs = BSpline.toBiArcs(10**-6)
            if all( hasattr(a,'Center') for a in arcs ):
                centers = numpy.array([a.Center for a in arcs])
                sigma = numpy.std( centers, axis=0 )
                if max(sigma) < 10**-6: #then circular curce
                    axis = a.Axis
            if all(isLine(a) for a in arcs):
                lines = arcs
                D = numpy.array([L.tangent(0)[0] for L in lines]) #D(irections)
                if numpy.std( D, axis=0 ).max() < 10**-9: #then linear curve
                    return D[0]
    if axis <> None:
        return numpy.array(axis)
    else:
        raise NotImplementedError,"getSubElementAxis Failed! Locals:\n%s" % formatDictionary(locals(),' '*4)


