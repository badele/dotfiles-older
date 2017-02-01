'''
Used for importing parts from other FreeCAD documents.
When update parts is executed, this library import or updates the parts in the assembly document.
'''
if __name__ == '__main__': #then testing library.
    import sys
    sys.path.append('/usr/lib/freecad/lib/') #path to FreeCAD library on Linux
    import FreeCADGui
    assert not hasattr(FreeCADGui, 'addCommand')
    FreeCADGui.addCommand = lambda x,y: 0

from assembly2lib import *
from assembly2lib import __dir__
import Part
from PySide import QtGui
import os, numpy, shutil, copy, time, posixpath, ntpath
from lib3D import *
from assembly2solver import solveConstraints
from muxAssembly import muxObjects, Proxy_muxAssemblyObj, muxMapColors
from viewProviderProxies import group_constraints_under_parts

def importPart( filename, partName=None, doc_assembly=None ):
    if doc_assembly == None:
        doc_assembly = FreeCAD.ActiveDocument
    updateExistingPart = partName <> None
    if updateExistingPart:
        FreeCAD.Console.PrintMessage("updating part %s from %s\n" % (partName,filename))
    else:
        FreeCAD.Console.PrintMessage("importing part from %s\n" % filename)
    doc_already_open = filename in [ d.FileName for d in FreeCAD.listDocuments().values() ]
    debugPrint(4, "%s open already %s" % (filename, doc_already_open))
    if doc_already_open:
        doc = [ d for d in FreeCAD.listDocuments().values() if d.FileName == filename][0]
    else:
        if filename.lower().endswith('.fcstd'):
            debugPrint(4, '  opening %s' % filename)
            doc = FreeCAD.openDocument(filename)
            debugPrint(4, '  succesfully opened %s' % filename)
        else: #trying shaping import http://forum.freecadweb.org/viewtopic.php?f=22&t=12434&p=99772#p99772x
            import ImportGui
            doc = FreeCAD.newDocument( os.path.basename(filename) )
            shapeobj=ImportGui.insert(filename,doc.Name)

    visibleObjects = [ obj for obj in doc.Objects
                       if hasattr(obj,'ViewObject') and obj.ViewObject.isVisible()
                       and hasattr(obj,'Shape') and len(obj.Shape.Faces) > 0 and 'Body' not in obj.Name] # len(obj.Shape.Faces) > 0 to avoid sketches, skip Body

    debugPrint(3, '%s objects %s' % (doc.Name, doc.Objects))
    if any([ 'importPart' in obj.Content for obj in doc.Objects]) and not len(visibleObjects) == 1:
        subAssemblyImport = True
        debugPrint(2, 'Importing subassembly from %s' % filename)
        tempPartName = 'import_temporary_part'
        obj_to_copy = doc_assembly.addObject("Part::FeaturePython",tempPartName)
        obj_to_copy.Proxy = Proxy_muxAssemblyObj()
        obj_to_copy.ViewObject.Proxy = ImportedPartViewProviderProxy()
        obj_to_copy.Shape =  muxObjects(doc)
        if (not updateExistingPart) or \
                (updateExistingPart and getattr( doc_assembly.getObject(partName),'updateColors',True)):
            muxMapColors(doc, obj_to_copy)
    else:
        subAssemblyImport = False
        if len(visibleObjects) <> 1:
            if not updateExistingPart:
                msg = "A part can only be imported from a FreeCAD document with exactly one visible part. Aborting operation"
                QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Value Error", msg )
            else:
                msg = "Error updating part from %s: A part can only be imported from a FreeCAD document with exactly one visible part. Aborting update of %s" % (partName, filename)
            QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Value Error", msg )
        #QtGui.QMessageBox.warning( QtGui.qApp.activeWindow(), "Value Error!", msg, QtGui.QMessageBox.StandardButton.Ok )
            return
        obj_to_copy  = visibleObjects[0]

    if updateExistingPart:
        obj = doc_assembly.getObject(partName)
        prevPlacement = obj.Placement
        if not hasattr(obj, 'updateColors'):
            obj.addProperty("App::PropertyBool","updateColors","importPart").updateColors = True
        importUpdateConstraintSubobjects( doc_assembly, obj, obj_to_copy )
    else:
        partName = findUnusedObjectName( doc.Label + '_', document=doc_assembly )
        try:
            obj = doc_assembly.addObject("Part::FeaturePython",partName)
        except UnicodeEncodeError:
            safeName = findUnusedObjectName('import_', document=doc_assembly)
            obj = doc_assembly.addObject("Part::FeaturePython", safeName)
            obj.Label = findUnusedLabel( doc.Label + '_', document=doc_assembly )
        obj.addProperty("App::PropertyFile",    "sourceFile",    "importPart").sourceFile = filename
        obj.addProperty("App::PropertyFloat", "timeLastImport","importPart")
        obj.setEditorMode("timeLastImport",1)
        obj.addProperty("App::PropertyBool","fixedPosition","importPart")
        obj.fixedPosition = not any([i.fixedPosition for i in doc_assembly.Objects if hasattr(i, 'fixedPosition') ])
        obj.addProperty("App::PropertyBool","updateColors","importPart").updateColors = True
    obj.Shape = obj_to_copy.Shape.copy()
    if updateExistingPart:
        obj.Placement = prevPlacement
    else:
        for p in obj_to_copy.ViewObject.PropertiesList: #assuming that the user may change the appearance of parts differently depending on the assembly.
            if hasattr(obj.ViewObject, p) and p not in ['DiffuseColor']:
                setattr(obj.ViewObject, p, getattr(obj_to_copy.ViewObject, p))
        obj.ViewObject.Proxy = ImportedPartViewProviderProxy()
    if getattr(obj,'updateColors',True):
        obj.ViewObject.DiffuseColor = copy.copy( obj_to_copy.ViewObject.DiffuseColor )
        #obj.ViewObject.Transparency = copy.copy( obj_to_copy.ViewObject.Transparency )   # .Transparency property
        tsp = copy.copy( obj_to_copy.ViewObject.Transparency )   #  .Transparency workaround for FC 0.17 @ Nov 2016
        if tsp < 100 and tsp<>0:
            obj.ViewObject.Transparency = tsp+1
        if tsp == 100:
            obj.ViewObject.Transparency = tsp-1
        obj.ViewObject.Transparency = tsp   # .Transparency workaround end 
    obj.Proxy = Proxy_importPart()
    obj.timeLastImport = os.path.getmtime( filename )
    #clean up
    if subAssemblyImport:
        doc_assembly.removeObject(tempPartName)
    if not doc_already_open: #then close again
        FreeCAD.closeDocument(doc.Name)
        FreeCAD.setActiveDocument(doc_assembly.Name)
        FreeCAD.ActiveDocument = doc_assembly
    return obj

class Proxy_importPart:
    def execute(self, shape):
        pass

class ImportPartCommand:
    def Activated(self):
        if FreeCADGui.ActiveDocument == None:
            FreeCAD.newDocument()
        view = FreeCADGui.activeDocument().activeView()
        #filename, filetype = QtGui.QFileDialog.getOpenFileName(
        #    QtGui.qApp.activeWindow(),
        #    "Select FreeCAD document to import part from",
        #    "",# "" is the default, os.path.dirname(FreeCAD.ActiveDocument.FileName),
        #    "FreeCAD Document (*.fcstd)"
        #    )
        dialog = QtGui.QFileDialog(
            QtGui.qApp.activeWindow(),
            "Select FreeCAD document to import part from"
            )
        dialog.setNameFilter("Supported Formats (*.FCStd *.brep *.brp *.imp *.iges *.igs *.obj *.step *.stp);;All files (*.*)")
        if dialog.exec_():
            filename = dialog.selectedFiles()[0]
        else:
            return
        importedObject = importPart( filename )
        FreeCAD.ActiveDocument.recompute()
        if not importedObject.fixedPosition: #will be true for the first imported part
            PartMover( view, importedObject )
        else:
            from PySide import QtCore
            self.timer = QtCore.QTimer()
            QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.GuiViewFit)
            self.timer.start( 200 ) #0.2 seconds

    def GuiViewFit(self):
        FreeCADGui.SendMsgToActiveView("ViewFit")
        self.timer.stop()

    def GetResources(self):
        return {
            'Pixmap' : ':/assembly2/icons/importPart.svg',
            'MenuText': 'Import a part from another FreeCAD document',
            'ToolTip': 'Import a part from another FreeCAD document'
            }
FreeCADGui.addCommand('importPart', ImportPartCommand())



def path_split( pathLib, path):
    parentPath, childPath = pathLib.split( path )
    parts = [childPath]
    while childPath <> '':
        parentPath, childPath = pathLib.split( parentPath )
        parts.insert(0, childPath)
    parts[0] = parentPath
    if  pathLib == ntpath and parts[0].endswith(':/'): #ntpath ...
        parts[0] = parts[0][:-2] + ':\\'
    return parts

def path_join( pathLib, parts):
    if pathLib == posixpath and parts[0].endswith(':\\'):
        path = parts[0][:-2]+ ':/'
    else:
        path = parts[0]
    for part in parts[1:]:
        path = pathLib.join( path, part)
    return path

def path_convert( path, pathLibFrom, pathLibTo):
    parts =  path_split( pathLibFrom, path)
    return path_join(pathLibTo, parts )

def path_rel_to_abs(path):
    j = FreeCAD.ActiveDocument.FileName.rfind('/')
    k = path.find('/')
    absPath = FreeCAD.ActiveDocument.FileName[:j] + path[k:]
    FreeCAD.Console.PrintMessage("First %s\n" % FreeCAD.ActiveDocument.FileName[:j])
    FreeCAD.Console.PrintMessage("Next %s\n" % path[k:])
    FreeCAD.Console.PrintMessage("absolutePath is %s\n" % absPath)
    if path.startswith('.') and os.path.exists( absPath ):
        return absPath
    else:
        return None



class UpdateImportedPartsCommand:
    def Activated(self):
        #disable proxies solving the system as their objects are updated
        doc_assembly = FreeCAD.ActiveDocument
        solve_assembly_constraints = False
        YesToAll_clicked = False
        for obj in doc_assembly.Objects:
            if hasattr(obj, 'sourceFile'):
                if not hasattr( obj, 'timeLastImport'):
                    obj.addProperty("App::PropertyFloat", "timeLastImport","importPart") #should default to zero which will force update.
                    obj.setEditorMode("timeLastImport",1)
                if not os.path.exists( obj.sourceFile ) and  path_rel_to_abs( obj.sourceFile ) is None:
                    debugPrint( 3, '%s.sourceFile %s is missing, attempting to repair it' % (obj.Name,  obj.sourceFile) )
                    replacement = None
                    aFolder, aFilename = posixpath.split( doc_assembly.FileName )
                    sParts = path_split( posixpath, obj.sourceFile)
                    debugPrint( 3, '  obj.sourceFile parts %s' % sParts )
                    replacement = None
                    previousRejects = []
                    while replacement == None and aFilename <> '':
                        for i in reversed(range(len(sParts))):
                            newFn = aFolder
                            for j in range(i,len(sParts)):
                                newFn = posixpath.join( newFn,sParts[j] )
                            debugPrint( 4, '    checking %s' % newFn )
                            if os.path.exists( newFn ) and not newFn in previousRejects :
                                if YesToAll_clicked:
                                    replacement = newFn
                                    break
                                reply = QtGui.QMessageBox.question(
                                    QtGui.qApp.activeWindow(), "%s source file not found" % obj.Name,
                                    "Unable to find\n  %s \nUse \n  %s\n instead?" % (obj.sourceFile, newFn) ,
                                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.YesToAll | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
                                if reply == QtGui.QMessageBox.Yes:
                                    replacement = newFn
                                    break
                                if reply == QtGui.QMessageBox.YesToAll:
                                    replacement = newFn
                                    YesToAll_clicked = True
                                    break
                                else:
                                    previousRejects.append( newFn )
                        aFolder, aFilename = posixpath.split( aFolder )
                    if replacement <> None:
                        obj.sourceFile = replacement
                    else:
                        QtGui.QMessageBox.critical(  QtGui.qApp.activeWindow(), "Source file not found", "update of %s aborted!\nUnable to find %s" % (obj.Name, obj.sourceFile) )
                        obj.timeLastImport = 0 #force update if users repairs link
                if path_rel_to_abs( obj.sourceFile ) is not None:
                    absolutePath = path_rel_to_abs( obj.sourceFile )
                    if os.path.getmtime( absolutePath ) > obj.timeLastImport:
                        importPart( absolutePath, obj.Name,  doc_assembly )
                        solve_assembly_constraints = True
                if os.path.exists( obj.sourceFile ):
                    if os.path.getmtime( obj.sourceFile ) > obj.timeLastImport:
                        importPart( obj.sourceFile, obj.Name,  doc_assembly )
                        solve_assembly_constraints = True

        if solve_assembly_constraints:
            solveConstraints( doc_assembly )
        # constraint mirror house keeping

        for obj in doc_assembly.Objects: #for adding creating mirrored constraints in old files
            if 'ConstraintInfo' in obj.Content:
                if doc_assembly.getObject( obj.Object1 ) == None or doc_assembly.getObject( obj.Object2 ) == None:
                    debugPrint(2, 'removing %s which refers to non-existent objects' % obj.Name)
                    doc_assembly.removeObject( obj.Name ) #required for FreeCAD 0.15 which does not support the on-delete method
                if group_constraints_under_parts():
                    if not hasattr( obj.ViewObject.Proxy, 'mirror_name'):
                        if isinstance( doc_assembly.getObject( obj.Object1 ).Proxy, Proxy_importPart) \
                                or isinstance( doc_assembly.getObject( obj.Object2 ).Proxy, Proxy_importPart):
                            debugPrint(2, 'creating mirror of %s' % obj.Name)
                            doc_assembly.getObject( obj.Object2 ).touch()
                            obj.ViewObject.Proxy.mirror_name = create_constraint_mirror(  obj, obj.ViewObject.Proxy.iconPath )
            elif 'ConstraintNfo' in obj.Content: #constraint mirror
                if  doc_assembly.getObject( obj.ViewObject.Proxy.constraintObj_name ) == None:
                    debugPrint(2, 'removing %s which mirrors/links to a non-existent constraint' % obj.Name)
                    doc_assembly.removeObject( obj.Name ) #clean up for FreeCAD 0.15 which does not support the on-delete method
                elif not group_constraints_under_parts():
                     debugPrint(2, 'removing %s since group_constraints_under_parts=False' % obj.Name)
                     delattr( doc_assembly.getObject( obj.ViewObject.Proxy.constraintObj_name ),  'mirror_name' )
                     doc_assembly.removeObject( obj.Name )
            elif hasattr(obj,'Proxy') and isinstance( obj.Proxy, Proxy_importPart) and not isinstance( obj.ViewObject.Proxy, ImportedPartViewProviderProxy):
                obj.ViewObject.Proxy = ImportedPartViewProviderProxy()
                debugPrint(2, '%s.ViewObject.Proxy = ImportedPartViewProviderProxy()'%obj.Name)
        doc_assembly.recompute()


    def GetResources(self):
        return {
            'Pixmap' : ':/assembly2/icons/importPart_update.svg',
            'MenuText': 'Update parts imported into the assembly',
            'ToolTip': 'Update parts imported into the assembly'
            }


FreeCADGui.addCommand('updateImportedPartsCommand', UpdateImportedPartsCommand())

def duplicateImportedPart( part ):
    nameBase = part.Label
    while nameBase[-1] in '0123456789' and len(nameBase) > 0:
        nameBase = nameBase[:-1]
    try:
        newObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", findUnusedObjectName(nameBase))
    except UnicodeEncodeError:
        safeName = findUnusedObjectName('import_')
        newObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", safeName)
        newObj.Label = findUnusedLabel( nameBase )
    newObj.addProperty("App::PropertyFile",    "sourceFile",    "importPart").sourceFile = part.sourceFile
    newObj.addProperty("App::PropertyFloat", "timeLastImport","importPart").timeLastImport =  part.timeLastImport
    newObj.setEditorMode("timeLastImport",1)
    newObj.addProperty("App::PropertyBool","fixedPosition","importPart").fixedPosition = False# part.fixedPosition
    newObj.addProperty("App::PropertyBool","updateColors","importPart").updateColors = getattr(part,'updateColors',True)
    newObj.Shape = part.Shape.copy()
    for p in part.ViewObject.PropertiesList: #assuming that the user may change the appearance of parts differently depending on their role in the assembly.
        if hasattr(newObj.ViewObject, p) and p not in ['DiffuseColor','Proxy']:
            setattr(newObj.ViewObject, p, getattr( part.ViewObject, p))
    newObj.ViewObject.DiffuseColor = copy.copy( part.ViewObject.DiffuseColor )
    newObj.Proxy = Proxy_importPart()
    newObj.ViewObject.Proxy = ImportedPartViewProviderProxy()
    newObj.Placement.Base = part.Placement.Base
    newObj.Placement.Rotation = part.Placement.Rotation
    return newObj


class PartMover:
    def __init__(self, view, obj):
        self.obj = obj
        self.initialPostion = self.obj.Placement.Base
        self.copiedObject = False
        self.view = view
        self.callbackMove = self.view.addEventCallback("SoLocation2Event",self.moveMouse)
        self.callbackClick = self.view.addEventCallback("SoMouseButtonEvent",self.clickMouse)
        self.callbackKey = self.view.addEventCallback("SoKeyboardEvent",self.KeyboardEvent)
    def moveMouse(self, info):
        newPos = self.view.getPoint( *info['Position'] )
        debugPrint(5, 'new position %s' % str(newPos))
        self.obj.Placement.Base = newPos
    def removeCallbacks(self):
        self.view.removeEventCallback("SoLocation2Event",self.callbackMove)
        self.view.removeEventCallback("SoMouseButtonEvent",self.callbackClick)
        self.view.removeEventCallback("SoKeyboardEvent",self.callbackKey)
    def clickMouse(self, info):
        debugPrint(4, 'clickMouse info %s' % str(info))
        if info['Button'] == 'BUTTON1' and info['State'] == 'DOWN':
            if not info['ShiftDown'] and not info['CtrlDown']:
                self.removeCallbacks()
            elif info['ShiftDown']: #copy object
                self.obj = duplicateImportedPart( self.obj )
                self.copiedObject = True
            elif info['CtrlDown']:
                azi   =  ( numpy.random.rand() - 0.5 )*numpy.pi*2
                ela   =  ( numpy.random.rand() - 0.5 )*numpy.pi
                theta =  ( numpy.random.rand() - 0.5 )*numpy.pi
                axis = azimuth_and_elevation_angles_to_axis( azi, ela )
                self.obj.Placement.Rotation.Q = quaternion( theta, *axis )

    def KeyboardEvent(self, info):
        debugPrint(4, 'KeyboardEvent info %s' % str(info))
        if info['State'] == 'UP' and info['Key'] == 'ESCAPE':
            if not self.copiedObject:
                self.obj.Placement.Base = self.initialPostion
            else:
                FreeCAD.ActiveDocument.removeObject(self.obj.Name)
            self.removeCallbacks()



class PartMoverSelectionObserver:
     def __init__(self):
         FreeCADGui.Selection.addObserver(self)
         FreeCADGui.Selection.removeSelectionGate()
     def addSelection( self, docName, objName, sub, pnt ):
         debugPrint(4,'addSelection: docName,objName,sub = %s,%s,%s' % (docName, objName, sub))
         FreeCADGui.Selection.removeObserver(self)
         obj = FreeCAD.ActiveDocument.getObject(objName)
         view = FreeCADGui.activeDocument().activeView()
         PartMover( view, obj )


class MovePartCommand:
    def Activated(self):
        selection = [s for s in FreeCADGui.Selection.getSelectionEx() if s.Document == FreeCAD.ActiveDocument ]
        if len(selection) == 1:
            PartMover(  FreeCADGui.activeDocument().activeView(), selection[0].Object )
        else:
            PartMoverSelectionObserver()

    def GetResources(self):
        return {
            'Pixmap' : ':/assembly2/icons/Draft_Move.svg',
            'MenuText': 'move',
            'ToolTip': 'move part  ( shift+click to copy )'
            }

FreeCADGui.addCommand('assembly2_movePart', MovePartCommand())

class DuplicatePartCommand:
    def Activated(self):
        selection = [s for s in FreeCADGui.Selection.getSelectionEx() if s.Document == FreeCAD.ActiveDocument ]
        if len(selection) == 1:
            PartMover(  FreeCADGui.activeDocument().activeView(), duplicateImportedPart( selection[0].Object ) )

    def GetResources(self):
        return {
            'MenuText': 'duplicate',
            'ToolTip': 'duplicate part (hold shift for multiple)'
            }

FreeCADGui.addCommand('assembly2_duplicatePart', DuplicatePartCommand())

#copy object


class EditPartCommand:
    def Activated(self):
        selection = [s for s in FreeCADGui.Selection.getSelection() if s.Document == FreeCAD.ActiveDocument ]
        obj = selection[0]
        docs = FreeCAD.listDocuments().values()
        docFilenames = [ d.FileName for d in docs ]
        if not obj.sourceFile in docFilenames :
            FreeCAD.open(obj.sourceFile)
            debugPrint(2, 'Openning %s' % str(obj.sourceFile))
        else:
            name = docs[docFilenames.index(obj.sourceFile)].Name
            debugPrint(2, 'Trying to set focus on %s, not working for some reason!' % str(obj.sourceFile))
            FreeCAD.setActiveDocument( name )
            FreeCAD.ActiveDocument=FreeCAD.getDocument( name )
            FreeCADGui.ActiveDocument=FreeCADGui.getDocument( name )
    def GetResources(self):
        return {
            'MenuText': 'edit',
            }
FreeCADGui.addCommand('assembly2_editImportedPart', EditPartCommand())

class ForkPartCommand:
    def Activated(self):
        selection = [s for s in FreeCADGui.Selection.getSelection() if s.Document == FreeCAD.ActiveDocument ]
        obj = selection[0]
        filename, filetype = QtGui.QFileDialog.getSaveFileName(
            QtGui.qApp.activeWindow(),
            "Specify the filename for the fork of '%s'" % obj.Label[:obj.Label.find('_import')],
            os.path.dirname(FreeCAD.ActiveDocument.FileName),
            "FreeCAD Document (*.fcstd)"
            )
        if filename == '':
            return
        if not os.path.exists(filename):
            debugPrint(2, 'copying %s -> %s' % (obj.sourceFile, filename))
            shutil.copyfile(obj.sourceFile, filename)
            obj.sourceFile = filename
            FreeCAD.open(obj.sourceFile)
        else:
            QtGui.QMessageBox.critical(  QtGui.qApp.activeWindow(), "Bad filename", "Specify a new filename!")

    def GetResources(self):
        return {
            'MenuText': 'fork',
            }
FreeCADGui.addCommand('assembly2_forkImportedPart', ForkPartCommand())


class DeletePartsConstraints:
    def Activated(self):
        selection = [s for s in FreeCADGui.Selection.getSelection() if s.Document == FreeCAD.ActiveDocument ]
        #if len(selection) == 1: not required as this check is done in initGui
        part = selection[0]
        deleteList = []
        for c in FreeCAD.ActiveDocument.Objects:
            if 'ConstraintInfo' in c.Content:
                if part.Name in [ c.Object1, c.Object2 ]:
                    deleteList.append(c)
        if len(deleteList) == 0:
            QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Info", 'No constraints refer to "%s"' % part.Name)
        else:
            flags = QtGui.QMessageBox.StandardButton.Yes | QtGui.QMessageBox.StandardButton.No
            msg = "Delete %s's constraint(s):\n  - %s?" % ( part.Name, '\n  - '.join( c.Name for c in deleteList))
            response = QtGui.QMessageBox.critical(QtGui.qApp.activeWindow(), "Delete constraints?", msg, flags )
            if response == QtGui.QMessageBox.Yes:
                for c in deleteList:
                    removeConstraint(c)
    def GetResources(self):
        return {
            'MenuText': 'delete constraints',
            }
FreeCADGui.addCommand('assembly2_deletePartsConstraints', DeletePartsConstraints())





from variableManager import ReversePlacementTransformWithBoundsNormalization

class _SelectionWrapper:
    'as to interface with assembly2lib classification functions'
    def __init__(self, obj, subElementName):
        self.Object = obj
        self.SubElementNames = [subElementName]


def classifySubElement( obj, subElementName ):
    selection = _SelectionWrapper( obj, subElementName )
    if planeSelected( selection ):
        return 'plane'
    elif cylindricalPlaneSelected( selection ):
        return 'cylindricalSurface'
    elif CircularEdgeSelected( selection ):
        return 'circularEdge'
    elif LinearEdgeSelected( selection ):
        return 'linearEdge'
    elif vertexSelected( selection ):
        return 'vertex' #all vertex belong to Vertex classification
    elif sphericalSurfaceSelected( selection ):
        return 'sphericalSurface'
    else:
        return 'other'

def classifySubElements( obj ):
    C = {
        'plane': [],
        'cylindricalSurface': [],
        'circularEdge':[],
        'linearEdge':[],
        'vertex':[],
        'sphericalSurface':[],
        'other':[]
        }
    prefixDict = {'Vertexes':'Vertex','Edges':'Edge','Faces':'Face'}
    for listName in ['Vertexes','Edges','Faces']:
        for j, subelement in enumerate( getattr( obj.Shape, listName) ):
            subElementName = '%s%i' % (prefixDict[listName], j+1 )
            catergory = classifySubElement( obj, subElementName )
            C[catergory].append(subElementName)
    return C

class SubElementDifference:
    def __init__(self, obj1, SE1, T1, obj2, SE2, T2):
        self.obj1 = obj1
        self.SE1 = SE1
        self.T1 = T1
        self.obj2 = obj2
        self.SE2 = SE2
        self.T2 = T2
        self.catergory = classifySubElement( obj1, SE1 )
        #assert self.catergory == classifySubElement( obj2, SE2 )
        self.error1 = 0 #not used for 'vertex','sphericalSurface','other'
        if self.catergory in ['cylindricalSurface','circularEdge','plane','linearEdge']:
            v1 = getSubElementAxis( obj1, SE1 )
            v2 = getSubElementAxis( obj2, SE2 )
            self.error1 = 1 - dot( T1.unRotate(v1), T2.unRotate(v2) )
        if self.catergory <> 'other':
            p1 = getSubElementPos( obj1, SE1 )
            p2 = getSubElementPos( obj2, SE2 )
            self.error2 = norm( T1(p1) - T2(p2) )
        else:
            self.error2 = 1 - (SE1 == SE2) #subelements have the same name
    def __lt__(self, b):
        if self.error1 <> b.error1:
            return self.error1 < b.error1
        else:
            return self.error2 < b.error2
    def __str__(self):
        return '<SubElementDifference:%s SE1:%s SE2:%s error1: %f error2: %f>' % ( self.catergory, self.SE1, self.SE2, self.error1, self.error2 )

def subElements_equal(obj1, SE1, T1, obj2, SE2, T2):
    try:
        if classifySubElement( obj1, SE1 ) == classifySubElement( obj2, SE2 ):
            diff = SubElementDifference(obj1, SE1, T1, obj2, SE2, T2)
            return diff.error1 == 0 and diff.error2 == 0
        else:
            return False
    except (IndexError, AttributeError), msg:
        return False


def importUpdateConstraintSubobjects( doc, oldObject, newObject ):
    '''
    TO DO (if time allows): add a task dialog (using FreeCADGui.Control.addDialog) as to allow the user to specify which scheme to use to update the constraint subelement names.
    '''
    #classify subelements
    if len([c for c in doc.Objects if  'ConstraintInfo' in c.Content and oldObject.Name in [c.Object1, c.Object2] ]) == 0:
        debugPrint(3,'Aborint Import Updating Constraint SubElements Names since no matching constraints')
        return
    debugPrint(2,'Import: Updating Constraint SubElements Names')
    newObjSubElements = classifySubElements( newObject )
    debugPrint(3,'newObjSubElements: %s' % newObjSubElements)
    # generating transforms
    T_old = ReversePlacementTransformWithBoundsNormalization( oldObject )
    T_new = ReversePlacementTransformWithBoundsNormalization( newObject )
    partName = oldObject.Name
    for c in doc.Objects:
        if 'ConstraintInfo' in c.Content:
            if partName == c.Object1:
                SubElement = "SubElement1"
            elif partName == c.Object2:
                SubElement = "SubElement2"
            else:
                SubElement = None
            if SubElement: #same as subElement <> None
                subElementName = getattr(c, SubElement)
                debugPrint(3,'  updating %s.%s' % (c.Name, SubElement))
                if not subElements_equal(  oldObject, subElementName, T_old, newObject, subElementName, T_new):
                    catergory = classifySubElement( oldObject, subElementName )
                    D = [ SubElementDifference( oldObject, subElementName, T_old, newObject, SE2, T_new)
                          for SE2 in newObjSubElements[catergory] ]
                    #for d in D:
                    #    debugPrint(2,'      %s' % d)
                    d_min = min(D)
                    debugPrint(3,'    closest match %s' % d_min)
                    newSE =  d_min.SE2
                    debugPrint(2,'  updating %s.%s   %s->%s' % (c.Name, SubElement, subElementName, newSE))
                    setattr(c, SubElement, newSE)
                    c.purgeTouched() #prevent constraint Proxy.execute being called when document recomputed.
                else:
                    debugPrint(3,'  leaving %s.%s as is, since subElement in old and new shape are equal' % (c.Name, SubElement))



if __name__ == '__main__':
    print('\nTesting importPart.py')
    def test_split_and_join( pathLib, path):
        print('Testing splitting and rejoining. lib %s' % (str(pathLib)))
        parts = path_split( pathLib, path )
        print('  parts %s' % parts )
        print('  rejoined   %s'  %  path_join(pathLib, parts ) )
        print('  original   %s'  %  path )

    test_split_and_join( ntpath, 'C:/Users/gyb/Desktop/Circular Saw Jig\Side support V1.00.FCStd')
    test_split_and_join( ntpath, 'C:/Users/gyb/Desktop/Circular Saw Jig/Side support V1.00.FCStd')
    test_split_and_join( posixpath, '/temp/hello1/foo.FCStd')

    def test_path_convert( path, pathLibFrom, pathLibTo):
        print('Testing path_convert_lib.')
        print('  original    %s'  %  path )
        converted = path_convert( path, pathLibFrom, pathLibTo)
        print('  converted   %s'  %  converted )
        print('  reversed    %s'  % path_convert( path, pathLibTo, pathLibFrom) )

    test_path_convert( r'C:\Users\gyb\Desktop\Circular Saw Jig\Side support V1.00.FCStd', ntpath, os.path )
