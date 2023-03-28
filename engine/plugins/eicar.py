"""eicar 플러그인 엔진"""
#-*- coding: utf-8 -*-
import os
import cryptolib

class KavMain:
    def init(self, plugins_path):
        return 0
    
    def uninit(self):
        return 0
    
    def scan(self, filehandle, filename):
        try:
            mm = filehandle
            
            size = os.path.getsize(filename)
            if size == 68: # EICAR Test 악성코드의 크기와 일치하는가?
               # 크기가 일치한다면 MD5 해시 계산
               fmd5 = cryptolib.md5(mm[:66])
               
               # 파일에서 얻은 해시값과 EICAR Test 악성코드이 해시값이 일치하는가?
               if fmd5 == b'44d88612fea8a8f36de82e1278abb02f':
                   return True, 'EICAR-Test-File (not a virus)', 0
        except IOError:
            pass
        
        return False, "", -1
    
    def disinfect(self, filename, malware_id):
        try:
            # 악성코드 진단 결과에서 받은 ID 값이 0인가?
            if malware_id == 0:
                os.remove(filename)
                return True
        except IOError:
            pass
        
        return False
    
    def listvirus(self):
        vlist = list()
        vlist.append('EICAR-Test-File (not a virus)') # 진단/치료하는 악성코드 이름 등록
        
        return vlist
    
    def getinfo(self):
        info = dict()
        
        info['author'] = 'Kei Choi'
        info['version'] = '1.1'
        info['title'] = 'EICAR Scan Engine'
        info['kmd_nmae'] = 'eicar'
        info['sig_num'] = 1 # 진단/치료 가능한 악성코드 수
        
        return info