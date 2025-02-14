import streamlit as st
from nba_api.stats.endpoints import clutchplayerstats
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
    """Get player's career clutch performance in last 5 minutes of close games"""
    try:
        # Get current season for the range
        current_season = "2023-24"
        
        # Try last 3 seasons first for newer players
        clutch_stats = clutchplayerstats.ClutchPlayerStats(
            player_id=player_id,
            per_mode_simple='Totals',
            season_type_all_star='Regular Season',
            clutch_time=5,
            point_diff=5,
            season=current_season
        ).get_data_frames()[0]
        
        if clutch_stats.empty:
            # If no stats found in recent seasons, try historical data
            clutch_stats = clutchplayerstats.ClutchPlayerStats(
                player_id=player_id,
                per_mode_simple='Totals',
                season_type_all_star='Regular Season',
                clutch_time=5,
                point_diff=5,
                season='1976-77'  # Historical data
            ).get_data_frames()[0]

        if clutch_stats.empty:
            return {"error": "No clutch stats found"}

        # Extract the stats
        stats = {
            'games_played': int(clutch_stats['GP'].iloc[0]),
            'minutes': round(float(clutch_stats['MIN'].iloc[0]), 1),
            'ppg': round(float(clutch_stats['PTS'].iloc[0]) / float(clutch_stats['GP'].iloc[0]), 1),
            'fg_pct': round(float(clutch_stats['FG_PCT'].iloc[0]) * 100, 1),
            'fg3_pct': round(float(clutch_stats['FG3_PCT'].iloc[0]) * 100, 1),
            'ft_pct': round(float(clutch_stats['FT_PCT'].iloc[0]) * 100, 1),
            'plus_minus': round(float(clutch_stats['PLUS_MINUS'].iloc[0]), 1),
            'total_points': int(clutch_stats['PTS'].iloc[0]),
            'assists': round(float(clutch_stats['AST'].iloc[0]) / float(clutch_stats['GP'].iloc[0]), 1),
            'rebounds': round(float(clutch_stats['REB'].iloc[0]) / float(clutch_stats['GP'].iloc[0]), 1),
            'steals': round(float(clutch_stats['STL'].iloc[0]) / float(clutch_stats['GP'].iloc[0]), 1),
            'blocks': round(float(clutch_stats['BLK'].iloc[0]) / float(clutch_stats['GP'].iloc[0]), 1),
            'turnovers': round(float(clutch_stats['TOV'].iloc[0]) / float(clutch_stats['GP'].iloc[0]), 1)
        }
        
        return stats
    except Exception as e:
        return {"error": str(e)}

# App header
st.title("🏀 NBA Career Clutch Performance Analyzer")
st.markdown("Compare players' career performance in clutch situations (last 5 minutes, margin ≤ 5 points)")

# Player selection
col1, col2 = st.columns(2)
with col1:
    player1 = st.text_input("Player 1:", "LeBron James")
with col2:
    player2 = st.text_input("Player 2:", "Kobe Bryant")

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
        time.sleep(1)  # Rate limiting
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
                    ("Clutch Games Played", "games_played", ""),
                    ("Avg. Clutch Minutes", "minutes", ""),
                    ("Points per Game", "ppg", ""),
                    ("FG%", "fg_pct", "%"),
                    ("3P%", "fg3_pct", "%"),
                    ("FT%", "ft_pct", "%"),
                    ("Plus/Minus", "plus_minus", ""),
                    ("Total Clutch Points", "total_points", ""),
                    ("Assists per Game", "assists", ""),
                    ("Rebounds per Game", "rebounds", ""),
                    ("Steals per Game", "steals", ""),
                    ("Blocks per Game", "blocks", ""),
                    ("Turnovers per Game", "turnovers", "")
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
        
        ppg_diff = abs(p1_stats['ppg'] - p2_stats['ppg'])
        better_scorer = player1 if p1_stats['ppg'] > p2_stats['ppg'] else player2
        
        plus_minus_diff = abs(p1_stats['plus_minus'] - p2_stats['plus_minus'])
        better_impact = player1 if p1_stats['plus_minus'] > p2_stats['plus_minus'] else player2
        
        st.markdown(f"""
        - {better_scorer} averages {ppg_diff:.1f} more points in clutch situations
        - {better_impact} has a better plus/minus in clutch by {plus_minus_diff:.1f} points
        - {player1} has played {p1_stats['games_played']} clutch games, averaging {p1_stats['minutes']} minutes
        - {player2} has played {p2_stats['games_played']} clutch games, averaging {p2_stats['minutes']} minutes
        - Career clutch scoring: {player1}: {p1_stats['total_points']} points | {player2}: {p2_stats['total_points']} points
        """)

# Footer
st.markdown("---")
st.caption("Data from NBA.com | Clutch defined as last 5 minutes with margin ≤ 5 points")