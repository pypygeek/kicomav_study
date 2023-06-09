#-*- coding: utf-8 -*-

# 디버깅용 여부 설정하기
K2DEBUG = False

# 악성코드 치료를 지시하는 상수
# scan 콜백함수에서 리턴 값으로 사용
K2_ACTION_IGNORE = 0
K2_ACTION_DISINFECT = 1
K2_ACTION_DELETE = 2
K2_ACTION_QUIT = 3

# 악성코드 격리 상태 관련 상수
K2_QUARANTINE_MOVE = 0
K2_QUARANTINE_COPY = 1