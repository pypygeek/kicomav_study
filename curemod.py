"""악성코드 치료 모듈"""
#-*- coding: utf-8 -*-
import os

# 주어진 파일을 삭제한다.
def CureDelete(fname):
    return os.remove(fname)