#-*- coding: utf-8 -*-
import time

def convert_date(t):
    """주어진 정수에서 날짜를 얻는다.
    Args:
        args1: 년, 월, 일이 포함된 2Byte 정수
    Returns:
        년, 월, 일
    """
    y = ((t & 0xFE00) >> 9) + 1980
    m = (t & 0x01E0) >> 5
    d = (t & 0x001F)
    
    return y, m, d

def covert_time(t):
    """주어진 정수에서 시간을 얻는다.
    Args:
        args1: 시, 분, 초가 포함된 2Byte 정수
    Returns:
        시, 분, 초
    """
    h = (t & 0xF800) >> 11
    m = (t & 0x07E0) >> 5
    s = (t & 0x001F) * 2
    
    return h, m, s

def get_now_date(now=None):
    """현재 날짜를 2byte 날짜 값으로 변환한다.
    Args:
        args1: 현재 날짜/시간 값 (생략 가능)
    Returns:
        2byte 날짜 값
    """
    if not now:
        now = time.gmtime()
    
    t_y = now.tm_year - 1980
    t_y = (t_y << 9) & 0xFE00
    t_m = (now.tm_mon << 5) & 0x01E0
    t_d = now.tm_mday & 0x001F
    
    return (t_y | t_m | t_d) & 0xFFFF

def get_now_time(now=None):
    """현재 시간을 2byte 시간 값으로 변환한다.
    Args:
        args1: 현재 날짜/시간 값 (생략 가능)
    Returns:
        2byte 시간 값
    """
    if not now:
        now = time.gmtime()
        
    t_h = (now.tm_hour << 11) & 0xF800
    t_m = (now.tm_min << 5) & 0x07E0
    t_s = (now.tm_sec // 2) & 0x001F
    
    return (t_h | t_m | t_s) & 0xFFFF