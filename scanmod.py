"""악성코드 진단 함수를 별도의 파일로 추출"""
#-*- coding: utf-8 -*-
import os
import hashlib

# 악성코드를 검사한다.
def SearchVDB(vdb, fmd5):
    for t in vdb:
        if t[0] == str(fmd5, 'utf-8'): # MD5 해시가 같은지 비교
            return True, t[1] # 악성코드 이름을 함께 리턴
        
    return False # 악성코드가 발견되지 않음

# MD5를 이용해서 악성코드를 검사한다.
def ScanMD5(vdb, vsize, fname):
    ret = False # 악성코드 발견 유무
    vname = "" # 발견된 악성코드 명
    
    size = os.path.getsize(fname) # 검사 대상 파일 크기를 구한다.
    
    if vsize.coint(size):
        fp = open(fname, 'rb') # 바이너리 모드로 읽기
        buf = fp.read()
        fp.close()
        
        m = hashlib.md5()
        m.update(buf)
        fmd5 = m.hexdigest()
        
        ret, vname = SearchVDB(vdb, fmd5) # 악성코드를 검사한다.
    
    return ret, vname

# 특정 위치 검색범을 이용하여 악성코드를 검사한다.
def ScanStr(fp, offset, mal_str):
    size = len(mal_str) # 악성코드 진단 문자열의 길이
    mal_Str = bytes(mal_str, 'utf-8')
    # 특정 위치에서 악성코드 진단 문자열이 존재하는지 체크
    fp.seek(offset) # 악성코드 문자열이 있을 것으로 예상하는 위치로 이동
    buf = fp.read(size) # 악성코드 문자열의 길이만큼 읽기

    if buf == mal_str:
        return True # 악성코드 발견
    else:
        return False # 악성코드 미발견