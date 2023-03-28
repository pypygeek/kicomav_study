#-*- coding: utf-8 -*-
import os
import io
import datetime
import types
import mmap

import k2kmdfile

class Engine:
    def __init__(self, debug=False):
        """클래스를 초기화한다.
        Args:
            args1: debug - 디버그 여부
        """
        self.debug = debug # 디버깅 여부
        
        self.plugins_path = None # 플러그인 경로
        self.kmdfiles = [] # 우선순위가 기록된 kmd 리스트
        self.kmd_modules = [] # 메모리에 로딩된 모듈
        
        # 플러그 엔진의 가장 최신 시간 값을 가진다.
        # 초기값으로는 1980-01-01을 저장한다.
        self.max_datetime = datetime.datetime(1980, 1, 1, 0, 0, 0, 0)
        
    def set_plugins(self, plugins_path):
        """주어진 경로에서 플러그인 엔진을 로딩 준비한다.
        Args:
            args1: plugins_path - 플러그인 엔진 경로
        Returns:
            성공 여부
        """
        self.plugins_path = plugins_path
        
        # 플러그인 우선순위를 알아낸다.
        ret = self.__get_kmd_list(plugins_path + os.sep + 'kicom.kmd')
        if not ret: # 로딩할 KMD 파일이 없을경우
            return False
        
        if self.debug:
            print('[*] kicom.kmd :')
            print(' ', self.kmdfiles)
        
        # 우선순위대로 KMD 파일을 로딩한다.
        for kmd_name in self.kmdfiles:
            kmd_path = plugins_path + os.sep + kmd_name
            k = k2kmdfile.KMD(kmd_path) # 모든 KMD 파일을 복호화한다.
            module = k2kmdfile.load(kmd_name.split('.')[0], k.body)
            if module: # 메모리 로딩 성공
                self.kmd_modules.append(module)
                # 메모리 로딩 성공한 날짜 KMD에서 플러그 엔진의 시간 값 읽기
                # 최신 업데이트 날짜가 된다.
                self.__get_last_kmd_build_time(k)
            
        if self.debug:
            print('[*] kmd_modules : ')
            print(' ', self.kmd_modules)
            print('[*] Last updated %s UTC' % self.max_datetime.ctime())
        
        return True
    
    def __get_kmd_list(self, kicom_kmd_file):
        """플러그인 엔진의 로딩 우선순위를 알아낸다.
        Args:
            args1: kicom_kmd_file - kicom.kmd 파일의 전체 경로
        Returns:
            성공 여부
        """
        kmdfiles = [] # 우선순위 목록
         
        k = k2kmdfile.KMD(kicom_kmd_file) # kicom.kmd 파일을 복호화한다.
        k.body = str(k.body, 'utf-8')
        
        if k.body: # kicom.kmd 읽혔는가?
            msg = io.StringIO(k.body)
            
        while True:
            # 한 줄을 읽어 엔터키 제거
            line = msg.readline().strip()
            
            if not line: # 읽혀진 내용이 없으면 종료
                break
            elif line.find('.kmd') != -1: # KMD 확장자가 존재한다면
                kmdfiles.append(line) # KMD 우선순위 목록에 추가
            else: # 확장자가 KMD가 아니면 다음 파일로..
                continue
        
        if len(kmdfiles): # 우선순위 목록에 하나라도 있다면 성공
            self.kmdfiles = kmdfiles
            return True
        else: # 우선순위 목록에 아무것도 없으면 실패
            return False
        
    def __get_last_kmd_build_time(self, kmd_info):
        """복호화된 플러그인 엔진의 빌드 시간 값 중 최신 값을 보관한다.
        Args:
            args1: kmd_info - 복호화된 플러그인 엔진 정보
        """
        d_y, d_m, d_d= kmd_info.date
        t_h, t_m, t_s = kmd_info.time
        t_datetime = datetime.datetime(d_y, d_m, d_d, t_h, t_m, t_s)
        
        if self.max_datetime < t_datetime:
            self.max_datetime = t_datetime
            
    def create_instance(self):
        """백신 엔진의 인스턴스를 생성한다.
        """
        ei = EngineInstance(self.plugins_path, self.max_datetime, self.debug)
        if ei.create(self.kmd_modules): # 전체 플러그인 인스턴스 생성 시도
            return ei
        else:
            return None
        
class EngineInstance:
    def __init__(self, plugins_path, max_datetime, debug=False):
        """클래스를 초기화한다.
        Args:
            args1: plugins_path - 플러그인 엔진 경로
            args2: max_datetime - 플러그인 엔진의 최신 시간 값
            args3: debug - 디버그 여부
        """
        self.debug = debug # 디버깅 여부
        
        self.plugins_path = plugins_path # 플러그인 경로
        self.max_datetime = max_datetime # 플러그 엔진의 가장 최신 시간 값
        
        self.kavmain_inst = [] # 모든 플러그인의 KavMain 인스턴스
 
    def create(self, kmd_modules):
        """백신 엔진의 인스턴스를 생성한다.
        Args:
            args1: kmd_modules - 메모리에 로딩된 KMD 모듈 리스트
        """
        for mod in kmd_modules:
            try:
                t = mod.KavMain()
                self.kavmain_inst.append(t)
            except AttributeError: # KavMain 클래스 존재하지 않음
                continue
            
        if len(self.kavmain_inst): # KavMain 인스턴스가 하나라도 있으면 성공
            if self.debug:
                print('[*] Count of KavMain : %d' % (len(self.kavmain_inst))) # 최종적으로 몇 개의 플러그인 엔진 인스턴스가 생성되었는지 확인한다.
            return True
        else:
            return False
        
    def init(self):
        """플러그인 엔진 전체를 초기화한다.
        Returns:
            성공 여부
        Note:
            self.kavmain_inst는 최종 인스턴스가 아니다.
            init 초기화 명령어를 실행해서 정상인 플러그인만 최종 등록해야한다.
        """
        t_kavmain_inst = [] # 최종 인스턴스 리스트
        
        if self.debug:
            print('[*] KavMain.init() :')
        
        for inst in self.kavmain_inst:
            try:
                # 플러그인 엔진의 init 함수 호출
                ret = inst.init(self.plugins_path)
                if not ret: # 성공
                    t_kavmain_inst.append(inst) # 임시 최종 인스턴스로 등록
                    
                    if self.debug:
                        print('[-] %s.init(): %d' % (inst.__module__, ret))
            except AttributeError:
                continue
            
        self.kavmain_inst = t_kavmain_inst # 최종 KavMain 인스턴스 등록
        
        if len(self.kavmain_inst): # KavMain 인스턴스가 하나라도 있으면 성공
            if self.debug:
                print('[*] Count of KavMain.init() : %d' % (len(self.kavmain_inst)))
            return True
        else:
            return False
        
    def uninit(self):
        """플러그인 엔진 전체를 종료한다.
        """
        if self.debug:
            print('[*] KavMain.uninit():')
        
        for inst in self.kavmain_inst:
            try:
                ret = inst.uninit()
                if self.debug:
                    print('[-] %s.uninit(): %d' % (inst.__module__, ret))
            except AttributeError:
                continue
            
    def getinfo(self):
        """플러그인 엔진 정보를 얻는다.
        Returns:
            플러그인 엔진 정보 리스트
        """
        ginfo = [] # 플러그인 엔진 정보를 담는다.
        
        if self.debug:
            print('[*] KavMain.getinfo():')
            
        for inst in self.kavmain_inst:
            try:
                ret = inst.getinfo()
                ginfo.append(ret)
                
                if self.debug:
                    print('[-] %s.getinfo():' % inst.__module__)
                    for key in ret.keys():
                        print('- %-10s : %s' % (key, ret[key]))
            except AttributeError:
                continue
            
        return ginfo
    
    def listvirus(self, *callback):
        """플러그인 엔진이 진단/치료할 수 있는 악성코드 목록을 얻는다.
        Args:
            args1: *callback - 콜백 함수 (생략 가능)
        Returns:
            악성코드 목록 (콜백함수 사용 시 아무런 값도 없음)
        """
        vlist = [] # 진단/치료 가능한 악성코드 목록
        
        argc = len(callback) # 가변인자 확인
        
        if argc == 0: # 인자가 없으면
            cb_fn = None
        elif argc == 1: # callback 함수가 존재하는지 체크
            cb_fn = callback[0]
        else: # 인자가 너무 많으면 에러
            return []
        
        if self.debug:
            print('[*] KavMain.listvirus():')
            
        for inst in self.kavmain_inst:
            try:
                ret = inst.listvirus()
                
                # callback 함수가 있다면 callback 함수 호출
                if isinstance(cb_fn, types.FunctionType):
                    cb_fn(inst.__module__, ret)
                else: # callback 함수가 없으면 악성코드 목록을 누적하여 리턴
                    vlist += ret
                
                if self.debug:
                    print('[-] %s.listvirus():' % inst.__module__)
                for vname in ret:
                    print('- %s' % vname)
            except AttributeError:
                continue
            
        return vlist
    
    def scan(self, filename):
        """플러그인 엔진에게 악성코드 검사를 요청한다.
        Args:
            args1: filename - 악성코드 검사 대상 파일 이름
        Returns:
            악성코드 발견 유무, 악성코드 이름, 악성코드 ID, 플러그인 엔진 ID
        """
        if self.debug:
            print('[*] KavMain.scan() :')
            
        try:
            ret = False
            vname = ""
            mid = -1
            eid = -1
            
            fp = open(filename, 'rb')
            mm = mmap.mmap(fp.fileno(), 0, access=mmap.ACCESS_READ) # 파일 I/O의 속도를 높이기 위해 운영체제에서 지원하는 캐시 기능을 사용한다.
            
            for i, inst in enumerate(self.kavmain_inst):
                try:
                    ret, vname, mid = inst.scan(mm, filename) # 파일 핸들이 준비되면 각 플러그인 엔진의 scan 함수를 호출하여 악성코드 검사를 진행한다.
                    if ret: # 악성코드 발견하면 추가 악성코드 검사를 중단한다.
                        eid = i # 악성코들르 발견한 플러그 엔진 ID
                        
                        if self.debug:
                            print('[-]%s.scan(): %s' % (inst.__module__, vname))
                            
                        break
                except AttributeError:
                    continue
                
            if mm:
                mm.close()
                
            if fp:
                fp.close()
                
            return ret, vname, mid, eid
        except IOError:
            pass
        
        return False, "", -1, -1
    
    def disinfect(self, filename, malware_id, engine_id):
        """플러그인 엔진에게 악성코드 치료를 요청한다.
        Args:
            args1: filename - 악성코드 치료 대상 파일 이름
            args2: malware_id - 감염된 악성코드 ID
            args3: engine_id - 악성코드를 발견한 플러그인 엔진 ID
        Returns:
            악성코드 치료 성공 여부
        """
        ret = False
        
        if self.debug:
            print('[*] KavMain.disinfect():')
        
        try:
            # 악성코드를 진단한 플러그인 엔진에게만 치료를 요청한다.
            inst = self.kavmain_inst[engine_id]
            ret = inst.disinfect(filename, malware_id)
            
            if self.debug:
                print('[-] %s.disinfect(): %s' % (inst.__module__, ret))
        except AttributeError:
            pass
        
        return ret    