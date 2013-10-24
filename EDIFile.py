import EDITSParser
import EDISegment

class EDIFile:

    BufferSize = 1000
    ElementDelimiter = '*'
    SegmentDelimiter = '~'
    FileBuffer = ''
    Validated = 0
    Valid = 0
    
    def __init__(self, filename):
        self.filename = filename
        self.TextEDIFile = open(self.filename, 'r', self.BufferSize)
        ISAString = self.TextEDIFile.read(106)
        self.ElementDelimiter = ISAString[3]
        self.SegmentDelimiter = ISAString[105]

        #Lots of work needed here. Ideally an EDIFile would peel off the ISA segment
        #then would iteratively process the (potentially many) GS Functional Groups.
        #Then, based on inspection of each Funtional Group, it would then be determined
        #how to initialize the EDITSParser for the Transaciton Set that group contains and
        #then parsing of that particular Transaction Set could be delegated to EDITSParser,
        #with a shared/global data file handle being passed to each differnet parser so that
        #all ISA, GS, GE, and IEA segments could be processed into the produced XML data file.

        #As it stands now, the EDIFile is assumed to have only one functional group and one
        #transaction set within that group and that one transaction set is a HIPAA 834 set.
        self.ISA = EDISegment.EDISegment(ISAString, self.ElementDelimiter)
        self.GS = self.__next__()
        self.Parser = EDITSParser.EDITSParser('EDITS834.xml')

    def __iter__(self):
        return self

    def __next__(self):
        keepreading = 1
        while keepreading:
            if self.FileBuffer.find(self.SegmentDelimiter) > 0:
                keepreading = 0
            else:
                newchunk = self.TextEDIFile.read(self.BufferSize)
                if newchunk == "":
                    keepreading = 0
                self.FileBuffer = self.FileBuffer + newchunk

        if self.FileBuffer == "":
            raise StopIteration
        
        if self.FileBuffer.find(self.SegmentDelimiter) > 0:
            NextSegment = self.FileBuffer[0:self.FileBuffer.find(self.SegmentDelimiter)]
            self.FileBuffer = self.FileBuffer[self.FileBuffer.find(self.SegmentDelimiter) + 1:len(self.FileBuffer)]
            return EDISegment.EDISegment(NextSegment,  self.ElementDelimiter)

    def validateTS(self):
        valid = 1
        for segment in self:
            match = self.Parser.matchSegment(segment)
            if match == 1 and len(self.Parser.segmentQueue) > 0:
                print(segment.toString())
            else:
                valid = 0
                break
        self.Validated = 1
        self.Valid = valid
        return valid

    def __del__(self):
        self.TextEDIFile.close()
        

if __name__ == "__main__":
    x = EDIFile('834.edi')
    print(x.ISA.toString())
    print(x.GS.toString())
    #print(x.ElementDelimiter)
    #print(x.SegmentDelimiter)
    x.validateTS()
    #    def __del__(self):
    xmlDataFile = open("TSData.xml", "w", encoding="utf-8")
    x.Parser.dataDocument.writexml(xmlDataFile, "\n", "\t")
    xmlDataFile.close()

