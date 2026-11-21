from hashlib import sha256
from pathlib import Path
import struct


class PeImage:
    def __init__(self,path):
        self.path=Path(path);self.data=self.path.read_bytes();self.sha256=sha256(self.data).hexdigest();self.pe=self.u32(0x3c);self.optional=self.pe+24
        if self.data[self.pe:self.pe+4]!=b'PE\0\0' or self.u16(self.optional)!=0x20b:raise ValueError('expected original PE32+ image')
        self.base=self.u64(self.optional+24);self.sections=[]
        for index in range(self.u16(self.pe+6)):
            offset=self.optional+self.u16(self.pe+20)+index*40;size,rva,rawsize,raw=struct.unpack_from('<IIII',self.data,offset+8);self.sections.append((rva,max(size,rawsize),raw,rawsize))

    def u16(self,offset):return struct.unpack_from('<H',self.data,offset)[0]
    def u32(self,offset):return struct.unpack_from('<I',self.data,offset)[0]
    def u64(self,offset):return struct.unpack_from('<Q',self.data,offset)[0]
    def offset(self,address):
        rva=address-self.base
        for start,length,raw,rawsize in self.sections:
            if start<=rva<start+length and rva-start<rawsize:return raw+rva-start
        raise ValueError('address is not original initialized bytes '+hex(address))
    def string(self,address):
        offset=self.offset(address);end=self.data.index(0,offset);return self.data[offset:end].decode('ascii')
    def exports(self):
        rva,size=struct.unpack_from('<II',self.data,self.optional+112)
        if not rva:return []
        offset=self.offset(self.base+rva);count=self.u32(offset+24);functions=self.offset(self.base+self.u32(offset+28));names=self.offset(self.base+self.u32(offset+32));ordinals=self.offset(self.base+self.u32(offset+36));values=[]
        for index in range(count):
            name=self.string(self.base+self.u32(names+4*index));ordinal=self.u16(ordinals+2*index);target=self.u32(functions+4*ordinal)
            values.append({'name':name,'address':hex(self.base+target),'forwarder':self.string(self.base+target) if rva<=target<rva+size else None})
        return values
    def range(self,address):
        rva,size=struct.unpack_from('<II',self.data,self.optional+112+3*8);offset=self.offset(self.base+rva)
        for position in range(offset,offset+size,12):
            start,end,_=struct.unpack_from('<III',self.data,position)
            if start<=address-self.base<end:return self.base+start,self.base+end
        return None
    def pin(self,name,start,end):
        offset=self.offset(start);self.offset(end-1);data=self.data[offset:offset+end-start]
        return {'name':name,'start':hex(start),'end_exclusive':hex(end),'file_offset':offset,'bytes':len(data),'sha256':sha256(data).hexdigest()}
    def imports(self):
        rva,_=struct.unpack_from('<II',self.data,self.optional+112+8)
        if not rva:return {}
        result={};position=self.offset(self.base+rva)
        while any(self.data[position:position+20]):
            original,_,_,name,first=struct.unpack_from('<IIIII',self.data,position);module=self.string(self.base+name);thunks=self.offset(self.base+(original or first));index=0
            while (value:=self.u64(thunks+8*index)):
                label='#'+str(value&0xFFFF) if value>>63 else self.string(self.base+value+2)
                result[self.base+first+8*index]={'module':module,'name':label};index+=1
            position+=20
        return result
