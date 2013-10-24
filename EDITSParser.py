import xml.dom.minidom
import EDISegment
from xml.dom.minidom import getDOMImplementation

class EDITSParser:

    def __init__(self, filename):
        self.filename = filename
        self.spec = xml.dom.minidom.parse(filename)
        self.remove_whitespace_nodes(self.spec, True)
        self.nextNode = self.spec.documentElement.firstChild
        self.buildSegmentQueue()
        self.lastMatchLineage = []
        self.lastMatchDataLineage = []
        
        #Set up XML document to write the parsed data to.
        impl = getDOMImplementation()
        self.dataDocument = impl.createDocument(None, "edidatafile", None)
        self.dataDocumentElement = self.dataDocument.documentElement
        self.dataDocumentElement.setAttribute('id', self.spec.documentElement.getAttribute('id'))
        self.dataDocumentElement.setAttribute('name', self.spec.documentElement.getAttribute('name'))

    def remove_whitespace_nodes(self,  node, unlink=False):
        remove_list = []
        for child in node.childNodes:
            if child.nodeType == node.TEXT_NODE and \
               not child.data.strip():
                remove_list.append(child)
            elif child.hasChildNodes():
                self.remove_whitespace_nodes(child, unlink)
        for node in remove_list:
            node.parentNode.removeChild(node)
            if unlink:
                node.unlink()


    def resetHasOccurredCounts(self,  node):
        nodelist = node.getElementsByTagName('*')
        for element in nodelist:
            element.setAttribute('has_occurred',0)

    def printNode(self,  node):
        print("Node information:")
        print ("   current node id: " + node.getAttribute('id'))
        print ("   can repeat: " + node.getAttribute('repeat'))
        print ("   has occurred: " + node.getAttribute('has_occurred'))
        print ("   parent id: " + node.parentNode.getAttribute('id'))
        print ("   parent repeat: " + node.parentNode.getAttribute('repeat'))
        print ("   parent has occurred: " + node.parentNode.getAttribute('has_occurred'))

    def buildSegmentQueue(self):
        #returns a list of xml.dom.Elements that represents rules and information of EDI segments that can come next when parsing an edi file.
        self.segmentQueue = list()
        travelDirection = "down"
        while 1:
            if self.nextNode.nodeType == self.nextNode.TEXT_NODE:
                print(self.nextNode)
                if self.nextNode.nextSibling != None:
                    self.nextNode = self.nextNode.nextSibling
                else:
                    #!!!
                    break
            elif self.nextNode.nodeName == "edifilespec":
                #print self.nextNode
                break

            elif self.nextNode.nodeName == "table":
                if travelDirection == "down":
                    self.nextNode = self.nextNode.firstChild
                else:
                    if self.nextNode.nextSibling != None:
                        travelDirection = "down"
                        self.nextNode = self.nextNode.nextSibling
                    else:
                        travelDirection = "up"
                        self.nextNode = self.nextNode.parentNode

            elif self.nextNode.nodeName == "loop":
                if travelDirection == "down":
                    if not self.nextNode.hasAttribute("has_occurred") or int(self.nextNode.getAttribute("has_occurred")) < int(self.nextNode.getAttribute("repeat")):
                        self.segmentQueue.append(self.nextNode.firstChild)
                        if self.nextNode.firstChild.getAttribute("usage") == "R" \
                        and (not self.nextNode.firstChild.hasAttribute("has_occurred") \
                        or self.nextNode.firstChild.getAttribute("has_occurred") == 0):
                            break
                    if self.nextNode.nextSibling != None:
                        travelDirection = "down"
                        self.nextNode = self.nextNode.nextSibling
                    else:
                        travelDirection = "up"
                        self.nextNode = self.nextNode.parentNode
                else: #travelDirection is "up"
                    if (self.nextNode.childNodes.length > 1 \
                        and (self.nextNode.getAttribute("repeat") == ">1"\
                        or int(self.nextNode.getAttribute("has_occurred")) < int(self.nextNode.getAttribute("repeat")))):
                        self.segmentQueue.append(self.nextNode.firstChild)
                        #max(self.segmentQueue).setAttribute("usage","S")
                        self.segmentQueue[len(self.segmentQueue) - 1].setAttribute("ussage",  "S")
                    travelDirection = "down"
                    if self.nextNode.nextSibling != None:
                        self.nextNode = self.nextNode.nextSibling
                    else:
                        travelDirection = "up"
                        self.nextNode = self.nextNode.parentNode

            elif self.nextNode.nodeName == "segment":
                #self.printNode(self.nextNode)
                if (self.nextNode.getAttribute("repeat") == ">1" \
                    or (self.nextNode.hasAttribute("has_occurred") and int(self.nextNode.getAttribute("has_occurred")) < int(self.nextNode.getAttribute("repeat"))) \
                    or(not self.nextNode.hasAttribute("has_occurred"))\
                    ):
                    self.segmentQueue.append(self.nextNode)

                if (self.nextNode.getAttribute("usage") == "R" \
                    and (not self.nextNode.hasAttribute("has_occurred") or self.nextNode.getAttribute("has_occurred") == 0)):
                    break

                if self.nextNode.nextSibling != None:
                    self.nextNode = self.nextNode.nextSibling
                else :
                    self.nextNode = self.nextNode.parentNode
                    travelDirection = "up"
 
    def printSegmentQueue(self):
        for el in self.segmentQueue:
            print(el.tagName + " " + el.getAttribute("id") + " " + el.getAttribute("name") + " " + str(el.getAttribute("has_occurred")))

    def matchSegment(self, EDISegment):
        #if len(EDISegment) == 0:
        #    return 0
        for specElement in self.segmentQueue:
            #specElement is a xml.dom.Element that represents rules and information of an EDI segment.

            #!!!matchEDIElements and validateEDIElements here.
            if self.matchEDIElements(EDISegment,  specElement):
                match = 1
            else:
                match = 0

            if match:
                #print(EDISegment.getSegmentID() + " matches")

                self.nextNode = specElement
                self.writeDataSegment(specElement, EDISegment)
                self.lastMatch = specElement
                
                if specElement.hasAttribute("has_occurred"):
                    specElement.setAttribute("has_occurred",  int(specElement.getAttribute("has_occurred")) + 1)
                else:
                    specElement.setAttribute("has_occurred",  "1")
                
                if (specElement.parentNode.nodeName == "loop" \
                    and specElement.parentNode.firstChild.isSameNode(specElement)):
                    #If so, we need to create/increment the loop occurrence count.

                    if specElement.parentNode.hasAttribute("has_occurred"):
                        hasOccurred = specElement.parentNode.getAttribute("has_occurred")
                        hasOccurred = int(hasOccurred) + 1
                    else:
                        hasOccurred = 1
                    
                    self.resetHasOccurredCounts(specElement.parentNode)

                    specElement.parentNode.setAttribute("has_occurred", str(hasOccurred))
                    specElement.setAttribute("has_occurred", 1)
                
                self.buildSegmentQueue()
                return 1
        return 0
    
    def matchEDIElements(self, EDISegment,  specElement):
        #Make sure the EDISegment matches the rules laid out in the specElement.
        if EDISegment.getSegmentID() == specElement.getAttribute("id"):
            match = 1
        else:
            match = 0
        return match
    
    def validateEDIElement(self, EDISegment,  specElement):
        #Make sure the EDISegment elements are valid against the rules laid out in the specElement.
        return 0

    def writeDataSegment(self, specElement, EDISegment):
        #Before writing the EDISegment, we need to compare this segments lineage to the previous segment so that we
        #know whether we need to extend the current XML data branch, or go back and create a new one somewhere.
        
        #Let's get the lineage of this EDISegment.
        thisMatchLineage = self.getSpecLineage(specElement)
        
        #Determine if there is a straight up lineage match, i.e. this EDI segment and the last EDI segment are "leafs on the same branch."
        if thisMatchLineage == self.lastMatchLineage:
            #print('Lineages match!')
            lineageMismatch = 'false'
        else:
            #print('Lineages do not match!')
            lineageMismatch = 'true'

        #Determine where the lineage of this EDISegment and the last EDISegment diverge.
        stopindex = min(len(thisMatchLineage), len(self.lastMatchLineage)) - 1
        i = 0
        while (i <= stopindex):
            if (not thisMatchLineage[i].isSameNode(self.lastMatchLineage[i])):
                lineageMismatch = 'true'
                break
            i = i + 1

        if (len(thisMatchLineage) < len(self.lastMatchLineage) and EDISegment.getSegmentID() != 'SE'):
            i = i - 1

        #For lineages that don't match, we need to do some work to the XML data file's current branch.
        if lineageMismatch =='true':
            thisMatchDataLineage = []
            #Build the new data lineage first using elements that match between this EDISegment lineage and the last.
            j = 0
            while (j < i) :
                thisMatchDataLineage.append(self.lastMatchDataLineage[j])
                j = j + 1

            k = j
            while (k < len(thisMatchLineage)):
                newElementID = thisMatchLineage[k].nodeName
                newNode = self.dataDocument.createElement(newElementID)
                newNode.setAttribute('id', thisMatchLineage[k].getAttribute('id'))
                newNode.setAttribute('name', thisMatchLineage[k].getAttribute('name'))
                
                #if (thisMatchDataLineage[k - 1]):
                if (k - 1 > 0 and thisMatchDataLineage[k - 1]):
                    thisMatchDataLineage[k - 1].appendChild(newNode)
                else:
                    if (newNode.tagName != 'edifilespec'):
                        self.dataDocumentElement.appendChild(newNode);

                thisMatchDataLineage.append(newNode)
                k = k + 1

        #Set the class variables for the next go round.
        self.lastMatchLineage = thisMatchLineage
        if (lineageMismatch == 'true'):
            self.lastMatchDataLineage = thisMatchDataLineage
        
        #Build and the current EDISegment as a <segment> node in the XML data file.
        newEDISegmentNode = self.dataDocument.createElement('segment')
        newEDISegmentNode.setAttribute('id', specElement.getAttribute('id'))
        newEDISegmentNode.setAttribute('name', specElement.getAttribute('name'))

        #Add the EDISegment elements as <element> nodes hanging off the <segment> node in the XML data file.
        m = 1
        while (m < len(EDISegment.elements)):
            newEDIElementNode = self.dataDocument.createElement('element')
            newEDIElementNode.setAttribute('id', specElement.getAttribute('id') + format(m, '#02'))
            newEDIElementNode.value = EDISegment.getElementByIndex(m)
            newEDIElementNode.setAttribute('value', EDISegment.getElementByIndex(m))
            newEDISegmentNode.appendChild(newEDIElementNode)
            m = m + 1
        
        #Set the class variables that point to XML data file locations for the next go round.
        try:
            self.lastMatchDataLineage[len(self.lastMatchDataLineage) - 1].appendChild(newEDISegmentNode)
        except:
            print('Error appending child to EDITSParser.lastMatchDataLineage')
            self.dataDocumentElement.appendChild(newEDISegmentNode)

        return 0

    def getSpecLineage(self, specElement):
        lineage = []
        while specElement.parentNode.nodeType != xml.dom.minidom.Node.DOCUMENT_NODE:
            lineage.append(specElement.parentNode)
            specElement = specElement.parentNode
        lineage.reverse()
        return lineage
    
    def printSpecLineage(self,  lineage):
        for specElement in lineage:
            print(specElement.getAttribute("id"))

if __name__ == "__main__":
#    x = EDITSParser("EDITS834.xml")
#    loop = 1
#    x.printSegmentQueue()
#    while loop:
#        segment = EDISegment.EDISegment(input("Enter next input segment: "), ' ')
#        match = x.matchSegment(segment)
#        if match == 1 and len(x.segmentQueue) > 0:
#            x.printSegmentQueue()
#        else:
#            loop = 0

    #Create the following to avoid warnings.
    bogusSegment = EDISegment.EDISegment('INS', ' ')

    impl = getDOMImplementation()

    xmldoc = impl.createDocument(None, "edifile", None)
    doc = xmldoc.documentElement
    table = xmldoc.createElement('table')
    segment = xmldoc.createElement('segment')
    element = xmldoc.createElement('element')
    element.setAttribute('id',  'INS')
    
    doc.appendChild(table)
    table.appendChild(segment)
    segment.appendChild(element)

    TSData = open("TSData.xml", "w", encoding="utf-8")
    xmldoc.writexml(TSData, "\n", "\t")
    TSData.close()
