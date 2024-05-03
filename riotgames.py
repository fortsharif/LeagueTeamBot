import requests
from itertools import combinations
import os

# Add your Riot Games API key here
RIOT_API_KEY = os.getenv("RIOT_API_KEY")


def get_summoner_puuid(summoner_name, tag, region="euw1"):
    url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{summoner_name}/{tag}?api_key={RIOT_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        summoner_data = response.json()
        return summoner_data["puuid"]
    else:
        return None


def get_summoner_id(puuid, region="euw1"):
    url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={RIOT_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        summoner_data = response.json()
        return summoner_data["id"]
    else:
        return None


def get_summoner_rank(summoner_id, region="euw1"):
    url = f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={RIOT_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        ranks_data = response.json()
        rank = "Unranked"
        for entry in ranks_data:
            if entry["queueType"] == "RANKED_SOLO_5x5":
                rank = f"{entry['tier']} {entry['rank']}"
                break

        return rank
    else:
        return None


def get_rank_mmr(rank: str) -> int:
    tiers_mmr = {
        "UNRANKED": 1400,
        "IRON": 500,
        "BRONZE": 750,
        "SILVER": 1000,
        "GOLD": 1250,
        "PLATINUM": 1500,
        "DIAMOND": 2000,
        "MASTER": 2500,
        "GRANDMASTER": 3000,
        "CHALLENGER": 3500,
        "IV": 50,
        "III": 75,
        "II": 100,
        "I": 125,
    }

    if rank.upper() == "UNRANKED":
        return tiers_mmr[rank.upper()] + 250

    tier, division = rank.split()
    tier_mmr = tiers_mmr[tier.upper()]

    division_mmr = tiers_mmr[division.upper()]

    return tier_mmr + division_mmr


def create_fair_teams(player_ranks: dict):
    players = list(player_ranks.keys())
    player_combinations = combinations(players, len(players) // 2)

    team1 = {}
    team2 = {}

    best_diff = float("inf")  # Initialize to a very large value
    for combination in player_combinations:
        current_team1 = dict((player, player_ranks[player]) for player in combination)
        current_team2 = dict(
            (player, player_ranks[player])
            for player in players
            if player not in combination
        )

        avg_mmr_team1 = sum(
            get_rank_mmr(rank) for rank in current_team1.values()
        ) / len(current_team1)
        avg_mmr_team2 = sum(
            get_rank_mmr(rank) for rank in current_team2.values()
        ) / len(current_team2)

        diff = abs(avg_mmr_team1 - avg_mmr_team2)

        if diff < best_diff:
            team1 = current_team1
            team2 = current_team2
            best_diff = diff

    avg_mmr_team1 = sum(get_rank_mmr(rank) for rank in team1.values()) / len(team1)
    avg_mmr_team2 = sum(get_rank_mmr(rank) for rank in team2.values()) / len(team2)

    return team1, team2, int(avg_mmr_team1), int(avg_mmr_team2)
