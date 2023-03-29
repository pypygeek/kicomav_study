#-*- coding: utf-8 -*-
import os
import io
import datetime
import types
import mmap
import glob
import tempfile

import k2kmdfile
import k2file
import k2const

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
        
        self.options = {} # 옵션
        self.set_options() # 기본 옵션을 설정한다.
        
        self.update_info = []  # 압축 파일 최종 치료를 위한 압축 리스트
        
        self.kavmain_inst = [] # 모든 플러그인의 KavMain 인스턴스

        self.result = {}
        self.identified_virus = set()

    def set_result(self):
        """백신 엔진의 악성코드 검사 결과를 초기화한다.
        """
        self.result['Folders'] = 0
        self.result['Files'] = 0
        self.result['Infected_files'] = 0
        self.result['Identified_viruses'] = 0
        self.result['IO_errors'] = 0

    def get_result(self):
        """ 백신 엔진의 악성코드 검사 결과를 얻는다.
        Returns:
            악성코드 검사 결과
        """
        # 지금까지 발견한 유니크한 악성코드의 수를 카운트한다.
        self.result['Identified_viruses'] = len(self.identified_virus)
        
        return self.result
 
    def set_options(self, options=None):
        """옵션을 설정한다.
        """
        if options:
            self.options['opt_list'] = options.opt_list
        else:
            self.options['opt_list'] = False
        
        return True
 
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
    
    def __scan_file(self, filename):
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
            self.result['IO_errors'] += 1 # 파일 I/O 오류 발생 수
        
        return False, "", -1, -1
    
    def scan(self, filename, *callback):
        """ 플러그인 엔진에게 악성코드 검사를 요청한다.
        Args:
            Args1: filename = 악성코드 검사 대상 파일 또는 폴더 이름
            Args2: callback - 검사 시 출력 화면 관련 콜백 함수
        Returns:
            0 - 성공
            1 - Ctrl+C를 이용해서 악성코드 검사 강제 종료
            -1 - 콜백 함수가 너무 많음
        Note:
            전체 폴더에 대해 악성코드를 검사한다.
        """

        scan_callback_fn = None # 악성코드 검사 콜백 함수
        disinfect_callback_fn = None # 악성코드 치료 콜백 함수
        update_callback_fn = None # 악성코드 압축 최종 치료 콜백 함수
        
        # 악성코드 검사 결과
        ret_value = {
            'filename': '', # 파일 이름
            'result': False, # 악성코드 발견 여부
            'virus_name': '', # 발견된 악성코드 이름
            'virus_id': -1, # 악성코드 ID
            'engine_id': -1 # 악성코드를 발견한 플러그인 엔진 ID
        }
        
        # 콜백 함수 저장
        try:
            scan_callback_fn = callback[0]
            disinfect_callback_fn = callback[1]
            update_callback_fn = callback[2]
        except IndexError:
            pass
    
        #  검사 대상 리스트에 파일을 등록
        file_info = k2file.FileStruct(filename)
        file_scan_list = [file_info]
        
        while len(file_scan_list):
            try:
                t_file_info = file_scan_list.pop(0) # 검사 대상 파일 하나를 가짐
                real_name = t_file_info.get_filename() # real_filename을 가져옴
                
                # 폴더면 내부 파일리스트만 검사 대상 리스트에 등록
                if os.path.isdir(real_name):
                # 폴더 등을 처리할 때를 위해 뒤에 붇는 os.sep는 우선 제거
                    if real_name[-1] == os.sep:
                        real_name = real_name[:-1]
                        
                # 콜백 호출 또는 검사 리턴값 생성
                ret_value['result'] = False # 폴더이므로 악성코드 없음
                ret_value['filename'] = real_name # 검사 파일 이름

                self.result['Folders'] += 1 # 폴더 개수 카운트
                
                if self.options['opt_list']: # 옵션 내용 중 모든 리스트 출력인가?
                    if isinstance(scan_callback_fn, types.FunctionType): # 콜백 함수가 존재하는가?
                        scan_callback_fn(ret_value) # 콜백 함수 호출
                
                    # 폴더 안의 파일들을 검사대상 리스트에 추가
                    flist = glob.glob(real_name + os.sep + '*')
                    tmp_flist = []
                    for rfname in flist:
                        tmp_info = k2file.FileStruct(rfname)
                        tmp_flist.append(tmp_info)
                        
                    file_scan_list = flist + file_scan_list
                elif os.path.isfile(real_name) or t_file_info.is_archive(): # 검사 대상이 파일인가? 압축 해제 대상인가?
                    self.result['Files'] += 1 # 파일 개수 카운트
                    
                    # 압축된 파일이면 해제한다.
                    ret = self.unarc(t_file_info)
                    if ret:
                        t_file_info = ret # 압축 결과물이 존재하면 파일 정보 교체
                    
                    # 포맷 분석
                    ff = self.format(t_file_info)
                    
                    # 3. 파일로 악성코드 검사
                    ret, vname, mid, eid = self.__scan_file(real_name)

                    # 악성코드 진단 개수 카운트
                    if ret:
                        self.result['Infected_files'] += 1
                        self.identified_virus.update([vname])

                    # self.result['Files'] += 1 # 파일 개수 카운트

                    # 콜백 호출 또는 검사 리턴값 생성
                    ret_value['result'] = ret # 악성코드 발견 여부
                    ret_value['engine_id'] = eid # 엔진 ID
                    ret_value['virus_name'] = vname # 악성코드 이름
                    ret_value['virus_id'] = mid # 악성코드 ID
                    ret_value['file_struct'] = t_file_info # 검사 파일 이름
                    
                    if ret_value['result']: # 악성코드 발견?
                        if isinstance(scan_callback_fn, types.FrameType):
                            action_type = scan_callback_fn(ret_value)
                            
                            if action_type == k2const.K2_ACTION_QUIT: # 종료?
                                return 0
                            
                            # scan 콜백 함수의 리턴값에 따라 악성코드를 치료한다.
                            self.__disinfect_process(ret_value, disinfect_callback_fn, action_type)
                    else:
                        if self.options['opt_list']: # 모든 리스트 출력?
                            if isinstance(scan_callback_fn, types.FunctionType):
                                scan_callback_fn(ret_value)
                                
                    # 압축 파일 최종 치료 처리
                    self.__update_process(t_file_info, update_callback_fn)
                    
                    # if self.options['opt_list']: # 모든 리스트 출력인가?
                    #     if isinstance(scan_callback_fn, types.FunctionType):
                    #         scan_callback_fn(ret_value)
                    #     else: # 아니라면 악성코드인 것만 출력
                    #         if ret_value['result']:
                    #             if isinstance(scan_callback_fn, types.FunctionType):
                    #                 scan_callback_fn(ret_value)
                    
                    # 이미 해당 파일이 악성코드라고 판명되었다면
                    # 그 파일을 압축 해제해서 내부를 볼 필요는 없다.
                    if not ret: # 따라서 악성코드가 아닌 경우만 검사
                        arc_file_list = self.arclist(t_file_info, ff)
                        if len(arc_file_list):
                            file_scan_list = arc_file_list + file_scan_list
            except KeyboardInterrupt:
                return 1 # 키보드 종료
            
        self.__update_process(None, update_callback_fn, True) # 최종 파일 정리
        return 0 # 정상적으로 검사 종료
        
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
    
    def get_version(self):
        """전체 플러그인 엔진의 최신 버전 정보를 전달한다.
        Returns:
            최신 버전 정보
        """
        return self.max_datetime
    
    def get_signum(self):
        """백신 엔진이 진단/치료 가능한 악성코드 수를 얻는다.
        Returns:
            진단/치료 가능한 악성코드 수
        """
        signum = 0 # 진단/치료 가능한 악성코드 수
        for inst in self.kavmain_inst:
            try:
                ret = inst.getinfo()
                # 플러그인 엔진 정보에 진단/치료 가능 악성코드 수 누적
                if 'sig_num' in ret:
                    signum += ret['sig_num']
            except AttributeError:
                continue
            
        return signum
    
    def unarc(self, file_struct):
        """플러그인 엔진에게 압축 해제를 요청한다.
        Args:
            args1: file_struct - 압축 해제 대상 파일 정보
        Returns:
            압축 해제된 파일 정보
            None
        """
        rname_struct = None
        
        try:
            if file_struct.is_archive(): # 압축인가?
                arc_engine_id = file_struct.get_archive_engine_name()
                arc_name = file_struct.get_archive_filename()
                name_in_arc = file_struct.get_filename_in_archive()
                
                # 압축 해제 엔진 모듈의 unarc 멤버 함수 호출
                for inst in self.kavmain_inst:
                    try:
                        unpack_data = inst.unarc(arc_engine_id, arc_name, name_in_arc)
                        
                        if unpack_data:
                            # 압축을 해제하여 임시 파일을 생성
                            rname = tempfile.mkstemp(prefix='ktmp')
                            fp = open(rname, 'wb')
                            
                            fp.write(unpack_data)
                            fp.close()
                            
                            rname_struct = file_struct
                            rname_struct.set_filename(rname)
                            break # 압축이 풀렸으면 종료
                    except AttributeError:
                        continue
                    
                return rname_struct
        except IOError:
            pass
    
        return None
    
    def arclist(self, file_struct, fileformat):
        """플러그인 엔진에게 압축 파일의 내부 리스트를 요청한다.
        Args:
            args1: file_struct - 압축 해제 대상 파일 정보
            args2: format - 미리 분석한 파일 포맷 분석 정보
        Returns:
            [압축 파일 내부 리스트]
            []
        """
        arc_list = [] # 압축 파일 리스트
        file_scan_list =[] # 검사 대상 정보를 모두 가짐(k2file.FileStruct)
        
        rname = file_struct.get_filename()
        deep_name = file_struct.get_additional_filename()
        mname = file_struct.get_master_filename()
        level = file_struct.get_level()
        
        # 압축 엔진 모듈의 arclist 멤버 함수 호출
        for inst in self.kavmain_inst:
            try:
                if self.options['opt_arc']: # 압축 검사 옵션이 있으면 모두 호출
                    arc_list = inst.arclist(rname, fileformat)
                    
                if len(arc_list): # 압축 리스트가 존재한다면 추가하고 종료
                    for alist in arc_list:
                        arc_id = alist[0] # 항상 압축 엔진 ID가 들어옴
                        name = alist[1] # 압축 파일의 내부 파일 이름
                        
                        if len(deep_name): # 압축 파일 내부 표시용
                            dname = '%s%s' % (deep_name)
                        else:
                            dname = '%s' % name
                            
                        fs = k2file.FileStruct()
                        # 기존 level보다 1증가 시켜 압축 깊이가 깊어짐을 표시
                        fs.set_archive(arc_id, rname, name, dname, mname, False, False, level+1)
                        file_scan_list.append(fs)
                        
                    self.result['Packed'] += 1
                    break
            except AttributeError:
                continue
            
        return file_scan_list
    
    def format(self, file_struct):
        """플러그인 엔진에게 파일 포맷 분석을 요청한다.
        Args:
            args1: file_struct - 압축 해제 대상 파일 정보
        Returns:
            {파일 포맷 분석 정보}
            {}
        """
        ret = {}
        filename = file_struct.get_filename()
        
        try:
            fp = open(filename, 'rb')
            mm = mmap.mmap(fp.fileno(), 0, access=mmap.ACCESS_READ)
            
            # 엔진 모듈 format 멤버 함수 호출
            for inst in self.kavmain_inst:
                try:
                    ff = inst.format(mm, filename)
                    if ff:
                        ret.update(ff)
                except AttributeError:
                    pass
                
            mm.close()
            fp.close()
            
        except IOError:
            pass
        
        return ret
    
    def __disinfect_process(self, ret_value, disinfect_callback_fn, action_type):
        """ 악성코드를 치료한다.
        Args:
            args1: ret_value - 악성코드 검사 겨로가
            args2: disinfect_callback_fn - disinfect 콜백 함수
            args3: action_type - 악성코드 치료 or 삭제 처리 여부
        Returns:
            True - 치료/삭제 성공
            False - 치료/삭제 실패
        """
        if action_type == k2const.K2_ACTION_IGNORE: # 치료에 대해 무시
            return
        
        t_file_info = ret_value['file_struct'] # 검사파일 정보
        mid = ret_value['virus_id'] # 악성코드 ID
        eid = ret_value['engine_id'] # 악성코드를 진단한 엔진 ID
        
        d_fname = t_file_info.get_filename() # 실제 파일 이름을 가져온다.
        d_ret = False
        
        if action_type == k2const.K2_ACTION_DISINFECT: # 치료 옵션이 설정되었나?
            d_ret = self.disinfect(d_fname, mid, eid)
            if d_ret:
                self.result['Disinfected_files'] += 1 # 치료 파일 수
            elif action_type == k2const.K2_ACTION_DELETE: # 삭제 옵션이 설정 되었나?
                try:
                    os.remove(d_fname)
                    d_ret = True
                    self.result['Deleted_files'] += 1 # 삭제 파일 수
                except IOError:
                    d_ret = False
                    
            t_file_info.set_modify(d_ret) # 치료(수정/삭제) 여부 표시
            
            if isinstance(disinfect_callback_fn, types.FunctionType):
                disinfect_callback_fn(ret_value, action_type)
                
    def __update_process(self, file_struct, update_callback_fn, immediately_flag=False):
        """update_info를 갱신한다.
        Args:
            args1: file_struct - 파일 정보 구조체
            args2: update_callback_fn - update 콜백 함수
            args3: immediately_flag - update_info 모든 정보 갱신 여부
        """
        # 압축 파일 정보의 재압축을 즉시하지 않고 내부 구성을 확인하여 처리한다. if immediately_flag is False: # ❶
        if immediately_flag is False:
            if len(self.update_info) == 0: # 아무런 파일이 없으면 추가
                self.update_info.append(file_struct)
            else:
                n_file_info = file_struct # 현재 작업 파일 정보
                p_file_info = self.update_info[-1] # 직전 파일 정보
            
                # 마스터 파일이 같은가?
                if p_file_info.get_master_filename() == n_file_info.get_master_filename():
                    if p_file_info.get_level() <= n_file_info.get_level():
                        # 마스터 파일이 같고 계속 압축 깊이가 깊어지면 계속 누적
                        self.update_info.append(n_file_info)
                    else:
                        # 마스터 파일이 같고 압축 깊이가 달라지면 내부 파일 업데이트 시점
                        ret_file_info = self.__update_arc_file_struct(p_file_info)
                        self.update_info.append(ret_file_info) # 결과 파일 추가
                        self.update_info.append(n_file_info) # 다음 파일 추가
        else:
            # 새로운 파일이 시작되므로 self.update_info 내부 모두 정리
            immediately_flag = True
        
        # 압축 파일 정보를 이용해 즉시 압축하여 최종 마스터 파일로 재조립한다
        if immediately_flag and len(self.update_info) > 1:
            ret_file_info = None
            
            while len(self.update_info):
                p_file_info = self.update_info[-1] # 직전 파일 정보
                ret_file_info = self.__update_arc_file_struct(p_file_info)
 
                if len(self.update_info): # 최상위 파일이 아니면 하위 결과 추가
                    self.update_info.append(ret_file_info)
     
            if isinstance(update_callback_fn, types.FunctionType) and ret_file_info:
                update_callback_fn(ret_file_info)

    def __update_arc_file_struct(self, p_file_info):
        """ update_info 내부의 압축을 처리한다.
        Args:
            args1: p_file_info - update_info의 마지막 파일 정보 구조체
        Returns:
            갱신된 파일 정보 구조체
        """               
        # 실제 압축 파일 이름이 같은 파일을 모두 추출한다.
        t = []
        arc_level = p_file_info.get_level()
        
        while len(self.update_info):
            if self.update_info[-1].get_level() == arc_level:
                t.append(self.update_info.pop()) # ❶
            else:
                break
        
        t.reverse() # 순위를 바꾼다.
 
        # 리턴값이 될 파일 정보 (압축 파일의 최상위 파일)
        ret_file_info = self.update_info.pop()
 
        # 업데이트 대상 파일들이 수정 여부를 체크한다
        b_update = False
 
        for finfo in t:
            if finfo.is_modify():
                b_update = True
                break
            
        if b_update: # 수정된 파일이 존재한다면 재압축 진행
            arc_name = t[0].get_archive_filename()
            arc_engine_id = t[0].get_archive_engine_name()
 
        for inst in self.kavmain_inst:
            try:
                ret = inst.mkarc(arc_engine_id, arc_name, t) # ❻
                if ret: # 최종 압축 성공
                    break
            except AttributeError:
                continue
            
            ret_file_info.set_modify(True) # 수정 여부 표시
            
        # 압축된 파일들 모두 삭제
        for tmp in t:
            t_fname = tmp.get_filename()
            # 플러그인 엔진에 의해 파일이 치료(삭제) 되었을 수 있음
            if os.path.exists(t_fname):
                os.remove(t_fname)
    
        return ret_file_info