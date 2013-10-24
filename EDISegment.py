class EDISegment:

    elements = []
    delimiter = '*'
    
    def __init__(self,  segmentString,  delimiter):
        self.parseSegmentString(segmentString,  delimiter)
        
    def getElementByIndex(self, idx):
        try:
            return self.elements[idx]
        except:
            return ''
            
    def parseSegmentString(self, segmentString, delimiter):
        self.delimiter = delimiter
        self.elements = segmentString.split(delimiter)
        #print(self.elements)
        
    def toString(self):
        return self.delimiter.join(self.elements)
        
    def getSegmentID(self):
        return self.getElementByIndex(0)

if __name__ == "__main__":
    x = EDISegment('INS*1**3','*')
    print(x.getSegmentID())
    print(x.getElementByIndex(1))
    print(x.getElementByIndex(2))
    print(x.getElementByIndex(3))
    print(x.toString())
