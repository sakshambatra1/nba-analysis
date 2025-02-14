import streamlit as st
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
import pandas as pd
import time

# Configure page settings
st.set_page_config(
    page_title="NBA Career Clutch Comparison",
    page_icon="🏀",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stat-box {
        background-color: #1E1E1E;
        border-radius: 5px;
        padding: 20px;
        border: 1px solid #333;
    }
    .stat-value {
        font-size: 24px;
        font-weight: bold;
        color: #FF4B4B;
    }
    .stat-label {
        color: #888;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_player_id(player_name):
    """Get player ID from name"""
    player_dict = players.find_players_by_full_name(player_name)
    if not player_dict:
        return None
    return player_dict[0]['id']

@st.cache_data(ttl=3600)
def get_career_clutch_stats(player_id):
    """Get player's career clutch performance"""
    try:
        all_games = pd.DataFrame()
        
        # Get all NBA seasons from 1976-77 to present
        seasons = [f"{year}-{str(year+1)[-2:]}" for year in range(1976, 2024)]
        
        for season in seasons:
            try:
                # Get game log for each season
                gamelog = playergamelog.PlayerGameLog(
                    player_id=player_id,
                    season=season
                ).get_data_frames()[0]
                all_games = pd.concat([all_games, gamelog])
                time.sleep(0.6)  # Rate limiting
            except:
                continue
        
        if all_games.empty:
            return {"error": "No games found"}
            
        # Define clutch games (close games - margin ≤ 5 points)
        clutch_games = all_games[abs(all_games['PLUS_MINUS']) <= 5]
        
        # Calculate career clutch stats
        stats = {
            'games_played': len(clutch_games),
            'ppg': round(clutch_games['PTS'].mean(), 1) if not clutch_games.empty else 0,
            'fg_pct': round(clutch_games['FG_PCT'].mean() * 100, 1) if not clutch_games.empty else 0,
            'ft_pct': round(clutch_games['FT_PCT'].mean() * 100, 1) if not clutch_games.empty else 0,
            'plus_minus': round(clutch_games['PLUS_MINUS'].mean(), 1) if not clutch_games.empty else 0,
            'win_pct': round((clutch_games['PLUS_MINUS'] > 0).mean() * 100, 1) if not clutch_games.empty else 0,
            'total_clutch_points': int(clutch_games['PTS'].sum()) if not clutch_games.empty else 0,
            'total_games': len(all_games),
            'clutch_game_pct': round(len(clutch_games) / len(all_games) * 100, 1) if not all_games.empty else 0
        }
        
        return stats
    except Exception as e:
        return {"error": str(e)}

# App header
st.title("🏀 NBA Career Clutch Performance Analyzer")
st.markdown("Compare players' entire career performance in close games (margin ≤ 5 points)")

# Player selection
col1, col2 = st.columns(2)
with col1:
    player1 = st.text_input("Player 1:", "LeBron James")
with col2:
    player2 = st.text_input("Player 2:", "Kevin Durant")

if st.button("Compare Players", type="primary"):
    with st.spinner("Analyzing career clutch performance..."):
        # Get player IDs
        p1_id = get_player_id(player1)
        p2_id = get_player_id(player2)
        
        if not p1_id or not p2_id:
            st.error(f"Player not found: {player1 if not p1_id else player2}")
            st.stop()
        
        # Get clutch stats
        p1_stats = get_career_clutch_stats(p1_id)
        p2_stats = get_career_clutch_stats(p2_id)
        
        # Error handling
        if "error" in p1_stats or "error" in p2_stats:
            st.error("Error fetching stats: " + str(p1_stats.get("error", p2_stats.get("error"))))
            st.stop()
        
        # Display comparison
        st.markdown("### Career Clutch Performance")
        
        col1, col2 = st.columns(2)
        
        def display_clutch_stats(stats, name, col):
            with col:
                st.markdown(f"<div class='stat-box'>", unsafe_allow_html=True)
                st.markdown(f"### {name}")
                
                metrics = [
                    ("Total Games Played", "total_games", ""),
                    ("Clutch Games Played", "games_played", ""),
                    ("% Games That Were Clutch", "clutch_game_pct", "%"),
                    ("Points in Clutch Games", "ppg", "PPG"),
                    ("FG% in Clutch", "fg_pct", "%"),
                    ("FT% in Clutch", "ft_pct", "%"),
                    ("Avg Plus/Minus", "plus_minus", ""),
                    ("Win % in Clutch", "win_pct", "%"),
                    ("Total Clutch Points", "total_clutch_points", "")
                ]
                
                for label, key, suffix in metrics:
                    st.metric(
                        label,
                        f"{stats[key]}{suffix}",
                        delta=None
                    )
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Display both players' stats
        display_clutch_stats(p1_stats, player1, col1)
        display_clutch_stats(p2_stats, player2, col2)
        
        # Add career insights
        st.markdown("### Career Insights")
        
        win_diff = abs(p1_stats['win_pct'] - p2_stats['win_pct'])
        better_clutch = player1 if p1_stats['win_pct'] > p2_stats['win_pct'] else player2
        
        points_diff = abs(p1_stats['ppg'] - p2_stats['ppg'])
        better_scorer = player1 if p1_stats['ppg'] > p2_stats['ppg'] else player2
        
        st.markdown(f"""
        - {better_clutch} has a higher career win percentage in clutch games by {win_diff:.1f}%
        - {better_scorer} averages {points_diff:.1f} more points in close games
        - {player1} has played {p1_stats['games_played']} close games ({p1_stats['clutch_game_pct']}% of games) vs {player2}'s {p2_stats['games_played']} games ({p2_stats['clutch_game_pct']}% of games)
        - {player1}'s total clutch points: {p1_stats['total_clutch_points']} | {player2}'s total clutch points: {p2_stats['total_clutch_points']}
        """)

# Footer
st.markdown("---")
st.caption("Data from NBA.com | Close games defined as final margin ≤ 5 points | Stats for entire career")