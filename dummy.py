"""플러그인 엔진 파일"""
#-*- coding: utf-8 -*-
import os

class KAVMain:
    def init(self, plugins_path):
        """플러그인 엔진을 초기화한다.
        Args: 
            arg1: plugins_path - 플러그인 엔진의 위치
        Returns:
            0 - 성공
            other - 실패
        """
        # 진단/치료하는 악성코드 이름
        self.virus_name = 'Dummy-Test-File (not a virus)'
        # 악성코드 패턴 등록
        self.dummy_pattern = 'Dummy Engin test file - KICOM Anti-Virus Project'
        
        return 0 # 플러그인 엔진 초기화 성공
    
    def uninit(self):
        """플러그인 엔진을 종료한다.
        Returns:
            0 - 성공
            other - 실패
        """
        del self.virus_name # 메모리 해제 (악성코드 이름 관련)
        del self.dummy_pattern # 메모리 해제 (악성코드 패턴)
        
        return 0
    
    def scan(self, filehandle, filename):
        """악성코드를 검사한다.
        Args:
            arg1: filehandle - 파일 핸들
            arg2: filename   - 파일 이름
        Returns: 
            악성코드 발견 여부, 악성코드 이름, 악성코드 ID 등등
        """
        try:
            # 파일을 열어 악성코드 패턴만큼 파일에서 읽는다.
            fp = open(filename, 'rb')
            buf = fp.read(len(self.dummy_pattern)) # 패턴의 크기
            fp.close()
            buf = str(buf, 'utf-8')
            
            # 악성코드 패턴을 비교한다.
            if buf == self.dummy_pattern:
                # 악성코드 패턴이 같다면 결과 값을 리턴한다.
                return True, self.virus_name, 0
            
        except IOError:
            pass
        
        # 악성코드를 발견하지 못했음으로 리턴한다.
        return False,"", -1
    
    def disinfect(self, filename, malware_id):
        """악성코드를 치료한다.
        Args
            arg1: filename   - 파일 이름
            arg2: malware_id - 치료할 악성코드 ID
            Returns: 
                True  - 치료 완료
                False - 치료 실패
        """
        try:
            # 악성코드 진단 결과에서 받은 ID 값이 0인가?
            if malware_id == 0:
                os.remove(filename) # 파일 삭제
                return True # 치료 완료 리턴
        except IOError:
            pass
        
        return False # 치료 실패 리턴
    
    def listvirus(self):
        """진단/치료 가능한 악성코드의 리스트를 알려준다.
        Returns: 
            악성코드 리스트
        """
        vlist = list()
        vlist.append(self.virus_name) # 진단/치료하는 악성코드 이름 등록
        
        return vlist
    
    def getinfo(self):
        """플러그인 엔진의 주요 정보를 알려준다. (제작자, 버전, Etc..)
        Returns:
            플러그인 엔진 정보
        """
        info = dict() # 사전형 변수 선언
        
        info['author'] = 'Kei Choi'
        info['version'] = 1.0
        info['title'] = 'Dummy Scan Engine' # 엔진 설명
        info['kmd_name'] = 'dummy' # 엔진 파일 이름
        
        return info