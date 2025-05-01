import streamlit as st
import random
from dataclasses import dataclass
from typing import List
import pandas as pd

@dataclass
class Player:
    name: str
    gender: str  # 'M' 또는 'F'
    games_played: int = 0
    mixed_games_played: int = 0  # 혼성복식 게임 횟수 추가

class BadmintonCourt:
    def __init__(self):
        self.players = []
        self.game_type = None  # '남자복식', '여자복식', '혼성복식' 
        self.is_game_active = False
        self.is_confirmed = False  # 게임 확인 상태 추가

class BadmintonApp:
    def __init__(self):
        if 'players' not in st.session_state:
            st.session_state.players = []
        if 'courts' not in st.session_state:
            st.session_state.courts = []
            
    def run(self):
        st.title('플레이콕 경기 매칭 시스템')
        
        # 사이드바에 플레이어 추가 기능
        with st.sidebar:
            st.header('선수 관리')
            name = st.text_input('이름')
            gender = st.selectbox('성별', ['남자', '여자'])
            
            # 이름 중복 체크
            if name:
                if any(p.name == name for p in st.session_state.players):
                    st.error('이미 존재하는 이름입니다.')
                    name = None
            
            if st.button('선수 추가') and name:
                gender_code = 'M' if gender == '남자' else 'F'
                new_player = Player(name=name, gender=gender_code)
                st.session_state.players.append(new_player)
                st.success(f'{name} 선수가 추가되었습니다.')
                
            # 선수 목록 및 게임 횟수 표시
            st.subheader('선수 현황')
            player_data = {
                '이름': [p.name for p in st.session_state.players],
                '성별': [p.gender for p in st.session_state.players],
                '총 게임 횟수': [p.games_played for p in st.session_state.players],
                '혼성복식 횟수': [p.mixed_games_played for p in st.session_state.players]
            }
            df = pd.DataFrame(player_data)
            st.dataframe(df)
            
            # 선수 이름 수정 기능
            st.subheader('선수 이름 수정')
            if st.session_state.players:
                player_to_edit = st.selectbox(
                    '수정할 선수 선택',
                    [p.name for p in st.session_state.players],
                    key='edit_player'
                )
                new_name = st.text_input('새로운 이름', key='new_name')
                
                # 새 이름 중복 체크
                if new_name:
                    if any(p.name == new_name for p in st.session_state.players):
                        st.error('이미 존재하는 이름입니다.')
                        new_name = None
                
                if st.button('이름 수정') and new_name:
                    player = next(p for p in st.session_state.players if p.name == player_to_edit)
                    old_name = player.name
                    player.name = new_name
                    st.success(f'{old_name} 선수의 이름이 {new_name}으로 변경되었습니다.')
                    
                    # 게임 중인 선수의 이름도 함께 변경
                    for court in st.session_state.courts:
                        if court.is_game_active:
                            for p in court.players:
                                if p.name == old_name:
                                    p.name = new_name
            
        # 메인 화면에 코트 설정
        if not st.session_state.courts:
            court_count = st.number_input('코트 수', min_value=1, value=1)
            if st.button('코트 생성'):
                st.session_state.courts = [BadmintonCourt() for _ in range(court_count)]
                
        # 코트 표시
        for i, court in enumerate(st.session_state.courts):
            st.subheader(f'코트 {i+1}')
            col1, col2 = st.columns(2)
            
            if not court.is_game_active:
                game_type = st.selectbox(
                    '게임 유형',
                    ['남자복식', '여자복식', '혼성복식'],
                    key=f'game_type_{i}'
                )
                
                if st.button('매칭', key=f'match_{i}'):
                    court.game_type = game_type
                    court.players = self.match_players(game_type)
                    court.is_game_active = True
                    court.is_confirmed = False
                    
            else:
                # 게임 중인 경우 선수 표시
                for j, player in enumerate(court.players):
                    st.text(f'선수 {j+1}: {player.name}')
                    
                if not court.is_confirmed:
                    if st.button('확인', key=f'confirm_{i}'):
                        court.is_confirmed = True
                        # 게임 횟수 증가
                        for player in court.players:
                            player.games_played += 1
                            if court.game_type == '혼성복식':
                                player.mixed_games_played += 1
                else:
                    st.success('게임이 확인되었습니다.')
                    
                # 선수 교체 기능
                player_to_replace = st.selectbox(
                    '교체할 선수 선택',
                    [p.name for p in court.players],
                    key=f'replace_{i}'
                )
                # 현재 게임 중이 아닌 선수들만 선택 가능
                active_players = []
                for c in st.session_state.courts:
                    if c.is_game_active and c != court:
                        active_players.extend([p.name for p in c.players])
                
                new_player = st.selectbox(
                    '새로운 선수 선택',
                    [p.name for p in st.session_state.players 
                     if p.name not in active_players and p not in court.players],
                    key=f'new_player_{i}'
                )
                
                if st.button('선수 교체', key=f'replace_button_{i}'):
                    self.replace_player(court, player_to_replace, new_player)
                
                if st.button('게임 종료', key=f'end_{i}'):
                    self.end_game(court)
                    
    def match_players(self, game_type):
        # 현재 게임 중인 선수들 목록
        active_players = []
        for court in st.session_state.courts:
            if court.is_game_active:
                active_players.extend([p.name for p in court.players])

        if game_type == '남자복식':
            eligible_players = [p for p in st.session_state.players 
                              if p.gender == 'M' and p.name not in active_players]
            eligible_players.sort(key=lambda x: x.games_played)
            return eligible_players[:4]
        elif game_type == '여자복식':
            eligible_players = [p for p in st.session_state.players 
                              if p.gender == 'F' and p.name not in active_players]
            eligible_players.sort(key=lambda x: x.games_played)
            return eligible_players[:4]
        else:  # 혼성복식
            males = [p for p in st.session_state.players 
                    if p.gender == 'M' and p.name not in active_players]
            females = [p for p in st.session_state.players 
                      if p.gender == 'F' and p.name not in active_players]
            
            # 혼성복식 게임 횟수로 먼저 정렬, 같으면 총 게임 횟수로 정렬
            males.sort(key=lambda x: (x.mixed_games_played, x.games_played))
            females.sort(key=lambda x: (x.mixed_games_played, x.games_played))
            return males[:2] + females[:2]
        
    def replace_player(self, court, old_player_name, new_player_name):
        old_player = next(p for p in court.players if p.name == old_player_name)
        new_player = next(p for p in st.session_state.players if p.name == new_player_name)
        court.players[court.players.index(old_player)] = new_player
        
    def end_game(self, court):
        # 코트 초기화
        court.players = []
        court.game_type = None
        court.is_game_active = False
        court.is_confirmed = False

if __name__ == '__main__':
    app = BadmintonApp()
    app.run()
