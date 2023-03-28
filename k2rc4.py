#-*- coding: utf-8 -*-

from arc4 import ARC4

class RC4:
    """RC4 클래스
    rc4.set_key : 암호 문자열 정의
    rc4.crypt : 주어진 버퍼 암/복호화
    """
    # 멤버 변수를 초기화 한다.
    def __init__(self):
        self.arc4 = None
        
    def set_key(self, password):
        """암호를 설정한다.
        Argrs:
            args1: password - rc4의 암호문 
        """
        self.arc4 = ARC4(password)
        
    def crypt(self, data):
        """주어진 데이터를 암/복호화한다.
        Args:
            args1: data - 암/복호화할 데이터
        Returns:
            암/복호화 결과 데이터
        """
        cipher = self.arc4.encrypt(data)
        
        return cipher