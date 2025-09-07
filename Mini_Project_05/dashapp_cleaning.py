import os
import sys
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import plotly.subplots as sp
import plotly.colors as pc
import sqlalchemy as sa
from sqlalchemy import create_engine

movie_df = pd.read_csv("enriched_new_movies.csv")

movie_df['themes'] = movie_df['themes'].apply(eval)
movie_df['tone'] = movie_df['tone'].apply(eval)

rating_counts = movie_df['age_rating'].value_counts().reset_index()
rating_counts.columns = ['age_rating', 'count']

def extract_themes():
    theme_counts = {}
    for themes_list in movie_df['themes']:
        for theme in themes_list:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
    return pd.DataFrame({'theme': list(theme_counts.keys()), 
                         'count': list(theme_counts.values())}).sort_values('count', ascending=False)

themes_df = extract_themes()

# Create a function to extract all unique tones and their frequencies
def extract_tones():
    tone_counts = {}
    for tones_list in movie_df['tone']:
        for tone in tones_list:
            tone_counts[tone] = tone_counts.get(tone, 0) + 1
    return pd.DataFrame({'tone': list(tone_counts.keys()), 
                         'count': list(tone_counts.values())}).sort_values('count', ascending=False)

tones_df = extract_tones()

# Create some basic visualizations
fig1 = px.bar(rating_counts, x='age_rating', y='count', 
              title='Distribution of Movies by Age Rating',
              labels={'count': 'Number of Movies', 'age_rating': 'Age Rating'})

fig2 = px.bar(themes_df.head(10), x='theme', y='count', 
              title='Top 10 Movie Themes',
              labels={'count': 'Frequency', 'theme': 'Theme'})

fig3 = px.bar(tones_df.head(10), x='tone', y='count', 
              title='Top 10 Movie Tones',
              labels={'count': 'Frequency', 'tone': 'Tone'})

# Display the figures
fig1.show()
fig2.show()
fig3.show()

movie_df['theme_count'] = movie_df['themes'].apply(len)
movie_avg_themes = movie_df['theme_count'].mean()

# Get average number of tones per movie
movie_df['tone_count'] = movie_df['tone'].apply(len)
movie_avg_tones = movie_df['tone_count'].mean()

# Create a simple theme-to-tone mapping to explore relationships
theme_tone_mapping = {}
for _, movie in movie_df.iterrows():
    for theme in movie['themes']:
        if theme not in theme_tone_mapping:
            theme_tone_mapping[theme] = {}
        for tone in movie['tone']:
            theme_tone_mapping[theme][tone] = theme_tone_mapping[theme].get(tone, 0) + 1

# Convert theme-tone mapping to DataFrame for easier use
theme_tone_pairs = []
for theme, tones in theme_tone_mapping.items():
    for tone, count in tones.items():
        theme_tone_pairs.append({'theme': theme, 'tone': tone, 'count': count})
theme_tone_df = pd.DataFrame(theme_tone_pairs)

# Save processed data to CSVs for use in the dashboard
rating_counts.to_csv('rating_counts.csv', index=False)
themes_df.to_csv('themes_data.csv', index=False)
tones_df.to_csv('tones_data.csv', index=False)
theme_tone_df.to_csv('theme_tone_data.csv', index=False)

# Save a processed version of the movie data
processed_movie_df = movie_df.copy()
processed_movie_df['tone_str'] = processed_movie_df['tone'].apply(lambda x: ', '.join(x))
processed_movie_df['themes_str'] = processed_movie_df['themes'].apply(lambda x: ', '.join(x))
processed_movie_df.to_csv('processed_movies.csv', index=False)

print("Data processing complete. Files saved for dashboard use.")

# processed_movie_df.drop(columns=['themes', 'tone'], inplace=True)
# processed_movie_df.to_csv('processed_movies.csv', index=False)

# processed_movie_df = pd.read_csv('processed_movies.csv')