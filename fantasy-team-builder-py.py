import csv
import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI()

# Path handling for serverless environment
base_path = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=base_path)

@dataclass
class Player:
    fullName: str
    Current_Team: str
    position: str
    Risk_Rating: str
    Consistency: float
    Upside_Potential: float
    season: str
    Total_FP: float

class TeamPreference(BaseModel):
    must_include_players: List[str]
    risk_rating: str = ''
    team_preference: str = ''

class FantasyTeamBuilder:
    def __init__(self):
        self.must_include_players = []
        self.fantasy_data = []
        self.schedule = []
        self._load_initial_data()

    def _load_initial_data(self):
        """Load initial data from files."""
        try:
            self.load_schedule(os.path.join(base_path, 'IPL_2025_Schedule.txt'))
            self.load_fantasy_data(os.path.join(base_path, 'IPL_FantasyData.csv'))
        except Exception as e:
            print(f'Error loading initial data: {e}')

    def load_schedule(self, filename: str) -> None:
        """Load the IPL schedule from a text file."""
        try:
            with open(filename, 'r') as f:
                self.schedule = [line.strip() for line in f.readlines()]
        except Exception as e:
            print(f'Error loading schedule: {e}')
            self.schedule = ['Error loading schedule']

    def parse_csv(self, filename: str) -> List[Dict]:
        """Parse CSV file and return list of dictionaries."""
        try:
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                return [row for row in reader]
        except Exception as e:
            print(f'Error parsing CSV: {e}')
            return []

    def load_fantasy_data(self, filename: str) -> None:
        """Load fantasy player data from CSV."""
        try:
            self.fantasy_data = self.parse_csv(filename)
        except Exception as e:
            print(f'Failed to load fantasy data: {e}')
            self.fantasy_data = []

    def get_teams_from_match(self, match: str) -> Optional[tuple]:
        """Extract teams from match string."""
        import re
        match_pattern = r'M\d+ - (.+) vs (.+)'
        teams = re.match(match_pattern, match)
        if teams and len(teams.groups()) == 2:
            return teams.group(1), teams.group(2)
        return None

    def get_players_for_teams(self, team1: str, team2: str) -> List[Dict]:
        """Get players from specified teams."""
        return [player for player in self.fantasy_data 
                if player['Current_Team'] in [team1, team2]]

    def select_best_xi(self, match_players: List[Dict], 
                      must_include_players: List[str],
                      risk_rating: str = '',
                      team_preference: str = '') -> List[Dict]:
        """Select best XI based on criteria."""
        risk_distribution = {
            'Low': 6,
            'Medium': 3,
            'High': 2
        }

        if risk_rating == 'Medium':
            risk_distribution = {'Low': 5, 'Medium': 4, 'High': 2}
        elif risk_rating == 'High':
            risk_distribution = {'Low': 4, 'Medium': 3, 'High': 4}

        current_season_players = [p for p in match_players if p['season'] == '2024']
        latest_players = current_season_players if current_season_players else match_players

        final_team = []
        remaining_spots = 11

        if must_include_players:
            selected_players = [p for p in latest_players 
                              if p['fullName'] in must_include_players]
            final_team.extend(selected_players)
            remaining_spots -= len(selected_players)

            for player in selected_players:
                risk = player['Risk_Rating']
                if risk_distribution[risk] > 0:
                    risk_distribution[risk] -= 1

            latest_players = [p for p in latest_players 
                            if p['fullName'] not in must_include_players]

        players_by_risk = {
            'Low': [p for p in latest_players if p['Risk_Rating'] == 'Low'],
            'Medium': [p for p in latest_players if p['Risk_Rating'] == 'Medium'],
            'High': [p for p in latest_players if p['Risk_Rating'] == 'High']
        }

        for risk_level, players in players_by_risk.items():
            if team_preference == 'consistency':
                players.sort(key=lambda x: float(x.get('Consistency', 0)), reverse=True)
            elif team_preference == 'upside':
                players.sort(key=lambda x: float(x.get('Upside_Potential', 0)), reverse=True)
            else:
                players.sort(key=lambda x: float(x.get('Total_FP', 0)), reverse=True)

        for risk_level, count in risk_distribution.items():
            available_players = players_by_risk[risk_level]
            selected = available_players[:count]
            final_team.extend(selected)

        return final_team[:11]

# Initialize the FantasyTeamBuilder
team_builder = FantasyTeamBuilder()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    with open(os.path.join(base_path, 'index.html'), 'r') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/api/matches")
def get_matches():
    return {"matches": team_builder.schedule}

@app.post("/api/best-xi/{match_index}")
def get_best_xi(match_index: int, preferences: TeamPreference):
    try:
        match = team_builder.schedule[match_index]
        teams = team_builder.get_teams_from_match(match)
        
        if not teams:
            raise HTTPException(status_code=400, detail="Invalid match format")
            
        team1, team2 = teams
        match_players = team_builder.get_players_for_teams(team1, team2)
        
        best_xi = team_builder.select_best_xi(
            match_players=match_players,
            must_include_players=preferences.must_include_players,
            risk_rating=preferences.risk_rating,
            team_preference=preferences.team_preference
        )
        
        return {"match": match, "best_xi": best_xi}
    except IndexError:
        raise HTTPException(status_code=404, detail="Match not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def handler(request, context):
    """
    Vercel serverless function handler
    """
    return app
