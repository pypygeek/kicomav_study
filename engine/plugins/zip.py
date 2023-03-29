#-*- coding: utf-8 -*-
import zipfile

class KavMain:
    def init(self, plugins_path):
        return 0
    
    def uninit(self):
        return 0
    
    def getinfo(self):
        info = dict()
        
        info['author'] = 'Kei Choi'
        info['version'] = '1.0'
        info['title'] = 'Zip Archive Engine'
        info['kmd_name'] = 'zip'
        
        return info
    
    def format(self, filehandle, filename):
        """파일 포맷을 분석한다.
        Args:
            args1: filehandle - 파일 핸들
            args2: filename - 파일 이름
        Returns:
            {파일 포맷 분석 정보}
            None
        """
        fileformat = {} # 포맷 정보를 담을 공간
        
        mm = filehandle
        if mm[0:4] == b'PK\x03\x04': # 헤더 체크
            fileformat['size'] = len(mm) # 포맷 주요 정보 저장
            
            ret = {'ff_zip': format}
            return ret
        
        return None
    
    def arclist(self, filename, fileformat):
        """압축 파일 내부의 파일 목록을 얻는다.
        Args:
            args1: filename - 파일 이름
            args2: fileformat - 파일 포맷 분석 정보
        Result:
            [[압축 엔진, 압축된 파일 이름]]
        """
        file_scan_list = [] # 검사 대상 정보를 모두 가짐
        
        # 미리 분석된 파일 포맷 중에 ZIP 포맷이 있는가?
        if 'ff_zip' in fileformat:
            zfile = zipfile.ZipFile(filename)
            for name in zfile.namelist():
                file_scan_list.append(['arc_zip', name])
            zfile.close()
        
        return file_scan_list
    
    def unarc(self, arc_engine_id, arc_name, fname_in_arc):
        """ZIP 파일 내부에 존재하는 파일 한 개씩 압축을 해제한다.
        Args:
            args1: arc_engine_id - 압축 엔진 ID
            args2: arc_name - 압축 파일
            args3: fname_in_arc - 압축 해제할 파일 이름
        Returns:
            압축 해제된 내용
            None
        """
        if arc_engine_id == 'arc_zip':
            zfile = zipfile.ZipFile(arc_name)
            data = zfile.read(fname_in_arc)
            zfile.close()
            
            return data
        
        return None