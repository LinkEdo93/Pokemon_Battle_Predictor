# -*- coding: utf-8 -*-
"""
Created on Wed May 28 12:10:48 2025

@author: Edo
"""

from flask import Flask, request, render_template
import pandas as pd
import pickle
import os

print("Running from:", os.getcwd())

# Load the model
with open('pokemon_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Load the data
pokemon_df = pd.read_csv('pokemon_data.csv')
pokemon_df['Name'] = pokemon_df['Name'].str.lower()
stat_cols = ['HP', 'Attack', 'Defense', 'Sp. Atk', 'Sp. Def', 'Speed']

# Names for the autocomplete feature
pokemon_names = sorted(pokemon_df['Name'].str.capitalize().tolist())

# Dictionary of type effectiveness
type_effectiveness = {
    'Normal': {'Rock': 0.5, 'Ghost': 0, 'Steel': 0.5}, 'Fire': {'Fire': 0.5, 'Water': 0.5, 'Grass': 2, 'Ice': 2, 'Bug': 2, 'Rock': 0.5, 'Dragon': 0.5, 'Steel': 2},
    'Water': {'Fire': 2, 'Water': 0.5, 'Grass': 0.5, 'Ground': 2, 'Rock': 2, 'Dragon': 0.5},
    'Electric': {'Water': 2, 'Electric': 0.5, 'Grass': 0.5, 'Ground': 0, 'Flying': 2, 'Dragon': 0.5},
    'Grass': {'Fire': 0.5, 'Water': 2, 'Grass': 0.5, 'Ground': 2, 'Flying': 0.5, 'Bug': 0.5, 'Rock': 2, 'Dragon': 0.5, 'Steel': 0.5},
    'Ice': {'Fire': 0.5, 'Water': 0.5, 'Grass': 2, 'Ground': 2, 'Flying': 2, 'Dragon': 2, 'Steel': 0.5},
    'Fighting': {'Normal': 2, 'Ice': 2, 'Rock': 2, 'Dark': 2, 'Steel': 2, 'Poison': 0.5, 'Flying': 0.5, 'Psychic': 0.5, 'Bug': 0.5, 'Ghost': 0, 'Fairy': 0.5},
    'Poison': {'Grass': 2, 'Fairy': 2, 'Poison': 0.5, 'Ground': 0.5, 'Rock': 0.5, 'Ghost': 0.5, 'Steel': 0},
    'Ground': {'Fire': 2, 'Electric': 2, 'Poison': 2, 'Rock': 2, 'Steel': 2, 'Grass': 0.5, 'Bug': 0.5, 'Flying': 0},
    'Flying': {'Grass': 2, 'Fighting': 2, 'Bug': 2, 'Electric': 0.5, 'Rock': 0.5, 'Steel': 0.5},
    'Psychic': {'Fighting': 2, 'Poison': 2, 'Psychic': 0.5, 'Steel': 0.5, 'Dark': 0},
    'Bug': {'Grass': 2, 'Psychic': 2, 'Dark': 2, 'Fire': 0.5, 'Fighting': 0.5, 'Poison': 0.5, 'Flying': 0.5, 'Ghost': 0.5, 'Steel': 0.5, 'Fairy': 0.5},
    'Rock': {'Fire': 2, 'Ice': 2, 'Flying': 2, 'Bug': 2, 'Fighting': 0.5, 'Ground': 0.5, 'Steel': 0.5},
    'Ghost': {'Psychic': 2, 'Ghost': 2, 'Normal': 0, 'Dark': 0.5},
    'Dragon': {'Dragon': 2, 'Steel': 0.5, 'Fairy': 0},
    'Dark': {'Psychic': 2, 'Ghost': 2, 'Fighting': 0.5, 'Dark': 0.5, 'Fairy': 0.5},
    'Steel': {'Ice': 2, 'Rock': 2, 'Fairy': 2, 'Fire': 0.5, 'Water': 0.5, 'Electric': 0.5, 'Steel': 0.5},
    'Fairy': {'Fighting': 2, 'Dragon': 2, 'Dark': 2, 'Fire': 0.5, 'Poison': 0.5, 'Steel': 0.5}
}

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html', pokemon_names=pokemon_names)

@app.route('/predict', methods=['POST'])
def predict():
    poke1 = request.form['pokemon1'].strip().lower()
    poke2 = request.form['pokemon2'].strip().lower()

    try:
        p1 = pokemon_df[pokemon_df['Name'] == poke1].iloc[0]
        p2 = pokemon_df[pokemon_df['Name'] == poke2].iloc[0]
    except IndexError:
        return render_template(
            'index.html',
            prediction_text="❌ Invalid Pokémon name entered.",
            pokemon_names=pokemon_names
        )

    # Calculate features of the model
    stat_sum_1 = p1[stat_cols].sum()
    stat_sum_2 = p2[stat_cols].sum()

    type_eff_1_to_2 = (
        type_effectiveness.get(p1['Type 1'], {}).get(p2['Type 1'], 1) *
        type_effectiveness.get(p1['Type 1'], {}).get(p2['Type 2'], 1) *
        type_effectiveness.get(p1['Type 2'], {}).get(p2['Type 1'], 1) *
        type_effectiveness.get(p1['Type 2'], {}).get(p2['Type 2'], 1)
    )

    type_eff_2_to_1 = (
        type_effectiveness.get(p2['Type 1'], {}).get(p1['Type 1'], 1) *
        type_effectiveness.get(p2['Type 1'], {}).get(p1['Type 2'], 1) *
        type_effectiveness.get(p2['Type 2'], {}).get(p1['Type 1'], 1) *
        type_effectiveness.get(p2['Type 2'], {}).get(p1['Type 2'], 1)
    )

    features = {
        'stat_sum_1': stat_sum_1,
        'stat_sum_2': stat_sum_2,
        'type_eff_1_to_2': type_eff_1_to_2,
        'type_eff_2_to_1': type_eff_2_to_1
    }

    input_df = pd.DataFrame([features])
    prediction = model.predict(input_df)[0]

    winner = poke1.capitalize() if prediction == 1 else poke2.capitalize()


    poke1_image_url = f"https://img.pokemondb.net/artwork/large/{poke1.replace(' ', '-')}.jpg"
    poke2_image_url = f"https://img.pokemondb.net/artwork/large/{poke2.replace(' ', '-')}.jpg"

    return render_template(
        'index.html',
        prediction_text=f"🏆 Predicted winner: {winner}",
        poke1_name=poke1.capitalize(),
        poke2_name=poke2.capitalize(),
        poke1_stats=p1[stat_cols].to_dict(),
        poke2_stats=p2[stat_cols].to_dict(),
        p1_type1=p1['Type 1'],
        p1_type2=p1['Type 2'],
        p2_type1=p2['Type 1'],
        p2_type2=p2['Type 2'],
        poke1_image_url=poke1_image_url,
        poke2_image_url=poke2_image_url,
        pokemon_names=pokemon_names
    )

if __name__ == '__main__':
    app.run(debug=True, port=5001)
