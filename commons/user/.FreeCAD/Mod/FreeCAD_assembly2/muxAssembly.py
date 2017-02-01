from assembly2lib import *
import Part
import os, numpy

class Proxy_muxAssemblyObj:
    def execute(self, shape):
        pass

def muxObjects(doc, mode=0):
    'combines all the imported shape object in doc into one shape'
    faces = []

    if mode == 1:
        objects = doc.getSelection()
    else:
        objects = doc.Objects

    for obj in objects:
        if 'importPart' in obj.Content:
            debugPrint(3, '  - parsing "%s"' % (obj.Name))
            faces = faces + obj.Shape.Faces
    return Part.makeShell(faces)

def muxMapColors(doc, muxedObj, mode=0):
    'call after muxedObj.Shape =  muxObjects(doc)'
    diffuseColors = []
    faceMap = {}

    if mode == 1:
        objects = doc.getSelection()
    else:
        objects = doc.Objects

    for obj in objects:
        if 'importPart' in obj.Content:
            for i, face in enumerate(obj.Shape.Faces):
                if i < len(obj.ViewObject.DiffuseColor):
                    clr = obj.ViewObject.DiffuseColor[i]
                else:
                    clr = obj.ViewObject.DiffuseColor[0]
                faceMap[faceMapKey(face)] = clr
    for f in muxedObj.Shape.Faces:
        try:
            key = faceMapKey(f)
            clr = faceMap[key]
            del faceMap[key]
        except KeyError:
            debugPrint(3, 'muxMapColors: waring no faceMap entry for %s - key %s' % (f,faceMapKey(f)))
            clr = muxedObj.ViewObject.ShapeColor
        diffuseColors.append( clr )
    muxedObj.ViewObject.DiffuseColor = diffuseColors

def faceMapKey(face):
    c = sum([ [ v.Point.x, v.Point.y, v.Point.z] for v in face.Vertexes ], [])
    return tuple(c)
   
class MuxAssemblyCommand:
    def Activated(self):
        #first check if assembly mux part already existings
        '''checkResult = [ obj  for obj in FreeCAD.ActiveDocument.Objects
                        if hasattr(obj, 'type') and obj.type == 'muxedAssembly' ]
        if len(checkResult) == 0:'''
        #deleted to force a creation of a new one any time
        partName = 'muxedAssembly'
        debugPrint(2, 'creating assembly mux "%s"' % (partName))
        muxedObj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",partName)
        muxedObj.Proxy = Proxy_muxAssemblyObj()
        muxedObj.ViewObject.Proxy = 0
        muxedObj.addProperty("App::PropertyString","type")
        muxedObj.type = 'muxedAssembly'
        FreeCADGui.ActiveDocument.getObject(muxedObj.Name).Visibility = False
        '''else:
            muxedObj = checkResult[0]
            debugPrint(2, 'updating assembly mux "%s"' % (muxedObj.Name))'''
            #deleted to force a creation of a new one any time
        'muxedObj.Shape = muxObjects( FreeCAD.ActiveDocument )'
        muxedObj.Shape = muxObjects(FreeCADGui.Selection, 1)
        muxMapColors(FreeCADGui.Selection, muxedObj, 1)
        'muxMapColors(FreeCAD.ActiveDocument, muxedObj)'
        FreeCAD.ActiveDocument.recompute()

       
    def GetResources(self):
        msg = 'Combine selected parts into a single object (for example to create a drawing of the assembly)'
        return {
            'Pixmap' : ':/assembly2/icons/muxAssembly.svg',
            'MenuText': msg,
            'ToolTip': msg
            }

FreeCADGui.addCommand('muxAssembly', MuxAssemblyCommand())
