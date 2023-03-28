#-*- coding: utf-8 -*-
import hashlib

def md5(data):
    """주어진 데이터에 대해 MD5 해시를 구한다.
    Args:
        args1: data - 데이터
    Returns:
        MD5 해시 문자열
    """
    return hashlib.md5(data).hexdigest()

class KavMain:
    def init(self, plugins_path):
        return 0
    
    def uninit(self):
        return 0
    
    def getinfo(self):
        info = dict()
        
        info['author'] = 'KeiChoi'
        info['version'] = '1.0'
        info['title'] = 'Crypto Library'
        info['kmd_name'] = 'cryptolib'
        
        return info